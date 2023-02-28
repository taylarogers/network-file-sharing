import socket
import os

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((socket.gethostname(), 1232))

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
            message = input("What would you like to do? Choose one of the options: \n -Upload\n -MultiUpload\n -Download \n -List \n -Quit \n")
            if (message == 'Upload'):
                uploadMode(sock)
                continue
            elif (message == 'MultiUpload'):
                multiUploadMode(sock)
                continue
            elif (message == 'Download'):
                downloadMode(sock)
                continue
            elif (message == 'List'):
                listMode(sock)
                continue
            elif (message == 'Quit'):
                print("Closing server link...")
                sock.send(bytes(buildHeader("<QUIT>"),"utf-8"))
                break
            else:
                print("Please enter a valid message.")
                continue
    finally:
        sock.close()

#building the header that needs to be sent to the server
def buildHeader(command, filename='', filesize='', filestate='', password=''):
    return f'{command}#{filename}#{filesize}#{filestate}#{password}'


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
            uploadMode()
    else:
        print("This is not a valid number")

    
#function to send a file to the server
def uploadMode(sock):
    filename = input("Please enter the name of the file: ")
    password = input("Please enter the password (leave blank if no password): ")
    password = password if password != "" else None
    filesize = os.path.getsize(filename)
    filestate = "protected" if password == None else "open"
    #send the header
    sock.send(bytes(buildHeader("<READ>", filename, filesize, filestate=filestate,password=password),"utf-8"))
    #open the file to send
    file = open(filename, "rb")
    
    #read packets to send over
    while True:
        packet = file.read(1024)
        if not packet:
            break
        sock.send(packet)
    file.close()

#function to receive a file from the server
def downloadMode(sock):
    filename, password = input("Please enter the filename of the file you wish to send followed by the file password: \n").split(" ")
    sock.send(bytes(buildHeader("<WRITE>",filename, password=password),"utf-8"))
    header = sock.recv(1024).decode("utf-8")
    command,filename_h, filesize_h= decodeHeader(header,0), decodeHeader(header,1),decodeHeader(header,2)
    if command == "<FAILED>":
        print("Request failed.")
        return
    #data to write to file
    file_bytes = b""
    #recieve the file in packets
    while True:
        packet = sock.recv(1024)
        if not packet:
            break;
        file_bytes += packet
    #open the file to write to and write to the file
    if(len(file_bytes) == filesize_h):
        file = open(filename_h, "wb")
        file.write(file_bytes)
        file.close()
        return
    else:
        print("Transfer failed")
        return

#function to request a list of files currently on the server

def listMode(sock):
    sock.send(bytes(buildHeader("<LIST>"),"utf-8"))
    header = sock.recv(1024).decode("utf-8")
    filelist = sock.recv(1024).decode("utf-8")
    print(filelist)

if __name__ == "__main__":
    main()