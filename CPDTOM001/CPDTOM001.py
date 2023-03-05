# CPDTOM001 Client
# Author: Tomas Cupido
# Version: 05/03/2023
# Std. Num.: CPDTOM001

import socket
import os
import hashlib
import sys
from time import sleep

def main():

    # Accepts optional command line arguments for connecting the client, leave blank for defaults
    n = len(sys.argv)
    # Default command line arguments
    if n < 3:
        IP_ADDR = '127.0.0.1'
        PORT_NO = 1230
    # User specified IP and Port
    else:
        IP_ADDR = sys.argv[1]
        PORT_NO = int(sys.argv[2])

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((IP_ADDR, PORT_NO))

    clear()

    try:
        #try login to the server
        logincode,username = login(sock)
        #if the login is invalid or fails
        if logincode == 1:
            return
        
        clear(1)

        print("------------\nWelcome to the program!\n------------")

        # accept console input for instructions
        while (True):
            print("------------\nMain Menu\n------------")
            # type the message to be sent
            message = input("Please select one of the following options: \n ⮞ (U)pload\n ⮞ (M)ultiUpload\n ⮞ (D)ownload \n ⮞ (L)ist \n ⮞ D(e)lete \n ⮞ (Q)uit \n")
            if (message.lower() == 'upload' or message[0].lower() == 'u'):
                clear()
                print("----------\nUpload\n----------")
                uploadMode(sock,username)
                input("Please press <RETURN> to continue.")
                clear()
                continue
            elif (message.lower() == 'multiupload' or message[0].lower() == 'm'):
                clear()
                multiUploadMode(sock,username)
                input("Please press <RETURN> to continue.")
                clear()
                continue
            elif (message.lower() == 'download' or message[0].lower() == 'd'):
                clear()
                print("----------\nDownload\n----------")
                downloadMode(sock,username)
                input("Please press <RETURN> to continue.")
                clear()
                continue
            elif (message.lower() == 'list' or message[0].lower() == 'l'):
                clear()
                print("----------\nList\n----------")
                listMode(sock,username)
                input("Please press <RETURN> to continue.")
                clear()
                continue
            elif (message.lower() == 'delete' or message[0].lower() == 'e'):
                clear()
                print("----------\nDelete\n----------")
                deleteMode(sock,username)
                input("Please press <RETURN> to continue.")
                clear()
                continue
            elif (message.lower() == 'quit' or message[0].lower() == 'q'):
                clear()
                print("Closing server link...")
                try:
                    sock.send(bytes(buildHeader("<QUIT>"),"utf-8"))
                except:
                    print("[X] Error: Connection Interrupted. Closing client...")
                break
            else:
                print("Request invalid. Please enter a valid message.")
                clear(1)
                continue
    finally:
        sock.close()
        clear(2)

# Function to send login details to the server
def login(sock):
    print("----------\nLogin\n----------")

    # User login
    username = input("Please enter your username: \n")
    password = input("Please enter your password: \n")

    # Send user details for authentication
    sock.send(bytes(f"{username}<SPLIT>{password}",'utf-8'))

    # Recieve confirmation or denial from server
    status,message = sock.recv(1024).decode('utf-8').split("#")

    # Clear the screen
    clear()

    # If the user is banned from the server 
    if status == "<BANNED>":
        print(message)
        sock.close()
        return 1,username
    # If the user manages to log into the server
    elif status == "<OK>":
        print(message)
        return 0,username
    # If the user's submitted data is invalid
    elif status == "<INVALID>":
        print(message)
        sock.close()
        return 1,username

#building the header that needs to be sent to the server
def buildHeader(command, filename=' ', filesize=' ', filestate=' ', password=' ',checksum = ' ', username = ' '):
    return f'{command}#{filename}#{filesize}#{filestate}#{password}#{checksum}#{username}'

# Function to send multiple files at once
def multiUploadMode(sock,username):
    print("----------\nMultiUpload\n----------")
    # Enter the number of files to send:
    while True:
        uploadMode(sock,username)
        msg = input("Please press any key then <RETURN> to continue uploading, or enter 'Q' to quit.\n")
        clear()
        if msg.lower() == 'q':
            break

    
# Function to send a file to the server
def uploadMode(sock, username):
    localList() # prints the list of files locally available to the client
    try:
        # get the filename 
        filename = input("Please enter the name of the file or 'Q' to quit: \n")
        if filename.lower() == 'q':
            return
        # get the password
        password = input("Please enter the password (leave blank if no password): \n")
        # get the filesize
        filesize = os.path.getsize('./Files/' + filename)
        # send the filestate, if there's a password the file is considered protected and only visible to the user who sent it
        filestate = "open" if password == "" else "protected"
        # open the file to send
        file = open('./Files/' + filename, "rb")
        # send the header
        sock.send(bytes(buildHeader("<READ>", filename, filesize,username=username,filestate=filestate,password=password, checksum=generateChecksum('Files/'+filename)),"utf-8"))
    
        # read packets to send over
        while True:
            packet = file.read(1024)
            if not packet:
                break
            sock.sendall(packet)
        file.close()

        # print the message received from the server
        returnedMessage = sock.recv(1024).decode("utf-8")
        print(returnedMessage)
        
    except FileNotFoundError:
        print("Error. File not found. Please input a valid file")
        clear(1)
        uploadMode(sock, username)

# Function to receive a file from the server
def downloadMode(sock,user):
    # list the available files
    listMode(sock,user)
    try:
        # get the name of the file
        filename = input("Please enter the name of the file or 'Q' to quit: \n")
        if filename.lower() == 'q':
            return
        # enter the password of the associated file
        password = input("Please enter the password (leave blank if no password): \n")
        # send the header data
        sock.send(bytes(buildHeader("<WRITE>",filename, password=password,username=user),"utf-8"))
        # receive the response from the server
        header = sock.recv(1024).decode("utf-8").split("#")
        if len(header) == 2:
            command,message = header
        else:
            command,filename,filesize,filestate,password,checksum = header
        # if the request failed 
        if command == "<FAILED>":
            print(message)
            return
        # if the request succeeded
        elif command == "<OK>":
            # use the md5 hashing to generate a checksum on the received file
            hash_no = hashlib.md5()
            #recieve the file in packets
            with open(f"./Files/{filename}",'wb') as f:
                byte_total = 0
                filesize = int(filesize)
                # receive and write the data to the file
                while True:
                    bytes_read = sock.recv(1024)
                    byte_total += len(bytes_read)
                    if byte_total >= filesize:
                        f.write(bytes_read)
                        hash_no.update(bytes_read)
                        break
                    elif not bytes_read:
                        break
                    f.write(bytes_read)
                    hash_no.update(bytes_read)
            # if the number of bytes received is the same and the file hash is the same
            if(byte_total == filesize and hash_no.hexdigest() == checksum):
                f.close()
                print(f"{filename} was successfully downloaded!")
                return
            else:
                print("Transfer failed. Please try again.")
                os.remove(f"./Files/{filename}")
                return
    except BrokenPipeError:
        print("Action Failed. Connection interrupted")
    
# Delete function to delete a file located on the server
def deleteMode(sock,user):
    # list the available files on the server
    listMode(sock,user)
    # input the filename of the file that is to be deleted
    filename = input("Please input the file name that you would like to delete or 'Q' to quit:\n")
    if filename.lower() == 'q':
            return
    # input the password of the file that is to be deleted
    password = input('Please input the password for the file (if none leave blank):\n')
    # send the header
    sock.send(bytes(buildHeader("<DELETE>", filename, "", "", password), "utf-8"))
    # get the response from the server
    returnedMessage = sock.recv(1024).decode("utf-8")
    print(returnedMessage)

# Function to request a list of files currently on the server
def listMode(sock,username):
    sock.send(bytes(buildHeader("<LIST>",username=username),"utf-8"))
    header = sock.recv(1024).decode("utf-8")
    filelist = sock.recv(1024).decode("utf-8")
    print(filelist)

# Lists the files locally available to the client
def localList():
    files = os.listdir('./Files')
    for file in files:
        print('•' + file)

# Function which uses md5 hashing to generate a checksum for a file being sent or received
def generateChecksum(file):
    checksum = hashlib.md5()
    with open(file, 'rb') as f:
        while True:
            # data read buffer for large files
            data = f.read(1024*64)
            if not data:
                break
            checksum.update(data)
    return checksum.hexdigest()

# Function to clear the terminal after a set time for cleaner UI         
def clear(time = 0):
    sleep(time)
    if os.name == 'posix':
        os.system('clear')
    else:        
        os.system('cls')

if __name__ == "__main__":
    main()