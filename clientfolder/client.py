import socket
import os
import hashlib
import sys

def main():

    n = len(sys.argv)
    if n < 3:
        IP_ADDR = '127.0.0.1'
        PORT_NO = 1230
    else:
        IP_ADDR = sys.argv[1]
        PORT_NO = int(sys.argv[2])

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((IP_ADDR, PORT_NO))

    try:
        username = input("Please enter your username: ")
        password = input("Please enter your password: ")

        sock.send(bytes(f"{username}<SPLIT>{password}",'utf-8'))
        status,message = sock.recv(1024).decode('utf-8').split("#")
        if status == "<BANNED>":
            print(message)
            sock.close()
            return
        elif status == "<OK>":
            print(message)
        elif status == "<INVALID>":
            print(message)
            sock.close()
            return

        # accept console input for instructions
        while (True):
            # type the message to be sent
            message = input("What would you like to do? Choose one of the options: \n -Upload\n -MultiUpload\n -Download \n -List \n -Delete \n -Quit \n")
            if (message == 'Upload'):
                uploadMode(sock,username)
                continue
            elif (message == 'MultiUpload'):
                multiUploadMode(sock)
                continue
            elif (message == 'Download'):
                downloadMode(sock,username)
                continue
            elif (message == 'List'):
                listMode(sock,username)
                continue
            elif (message == 'Delete'):
                deleteMode(sock)
                continue
            elif (message == 'Quit'):
                print("Closing server link...")
                try:
                    sock.send(bytes(buildHeader("<QUIT>"),"utf-8"))
                except:
                    print("Connection Interrupted.")
                break
            else:
                print("Please enter a valid message.")
                continue
    finally:
        sock.close()

#building the header that needs to be sent to the server
def buildHeader(command, filename=' ', filesize=' ', filestate=' ', password=' ',checksum = ' ', username = ' '):
    return f'{command}#{filename}#{filesize}#{filestate}#{password}#{checksum}#{username}'


#decoding headers that come from the server
def decodeHeader(header,pos):
    return header.split("#")[pos]


#function to send multiple files at once
def multiUploadMode(sock):
    #enter the amount of files to send:
    numFiles=input("Please enter the number of files you wish to upload (1-100):\n")

    #check if a number is valid
    if numFiles.isdigit() and int(numFiles)>0:
        numFiles=int(numFiles)
        #for loop to go through all files
        for x in range(numFiles):
            uploadMode(sock, True)
            returnedMessage = sock.recv(1024).decode("utf-8")
            print(returnedMessage)
    else:
        print("This is not a valid number")

    
#function to send a file to the server
def uploadMode(sock, username, multi=False):
    try:
        filename = input("Please enter the name of the file: ")
        password = input("Please enter the password (leave blank if no password): ")
        filesize = os.path.getsize(filename)
        filestate = "open" if password == "" else "protected"
        #send the header
        sock.send(bytes(buildHeader("<READ>", filename, filesize,username=username,filestate=filestate,password=password, checksum=generateChecksum(filename)),"utf-8"))
        #open the file to send
        file = open(filename, "rb")
    
        #read packets to send over
        while True:
            packet = file.read(1024)
            if not packet:
                break
            sock.sendall(packet)
        file.close()

        if multi==False:
            returnedMessage = sock.recv(1024).decode("utf-8")
            print(returnedMessage)
    except:
        print("Action Failed. Connection interrupted")

#function to receive a file from the server
def downloadMode(sock,user):
    try:
        filename = input("Please enter the name of the file: ")
        password = input("Please enter the password (leave blank if no password): ")
        sock.send(bytes(buildHeader("<WRITE>",filename, password=password,username=user),"utf-8"))
        command,filename,filesize,filestate,password,checksum = sock.recv(1024).decode("utf-8").split("#")
        if command == "<FAILED>":
            print("Request failed.")
            return
        elif command == "<OK>":
            hash_no = hashlib.md5()
            #recieve the file in packets
            with open(filename,'wb') as f:
                byte_total = 0
                filesize = int(filesize)
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
            #open the file to write to and write to the file
            if(byte_total == filesize and hash_no.hexdigest() == checksum):
                f.close()
                return
            else:
                print("Transfer failed")
                return
    except:
        print("Action Failed. Connection interrupted")
    
# Delete function
def deleteMode(sock):
    filename = input('Please input the file name that you would like to delete:\n')
    password = input('Please input the password for the file (if none leave blank):\n')
    sock.send(bytes(buildHeader("<DELETE>", filename, "", "", password), "utf-8"))
    returnedMessage = sock.recv(1024).decode("utf-8")
    print(returnedMessage)

#function to request a list of files currently on the server

def listMode(sock,username):
    sock.send(bytes(buildHeader("<LIST>",username=username),"utf-8"))
    header = sock.recv(1024).decode("utf-8")
    filelist = sock.recv(1024).decode("utf-8")
    print(filelist)

def generateChecksum(file):
    checksum = hashlib.md5()
    with open(file, 'rb') as f:
        while True:
            data = f.read(1024*64)
            if not data:
                break
            checksum.update(data)
    return checksum.hexdigest()
            

if __name__ == "__main__":
    main()