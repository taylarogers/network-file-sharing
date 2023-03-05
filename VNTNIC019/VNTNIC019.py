import socket,hashlib,sys,os

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
        #Before a user is able to interact with the server they need to log in/register
        username = input("[-]Enter username: ")
        password = input("[-]Enter password: ")

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

        #Once logged in a user can choose an action
        while (True):
            #Choose action
            message = input("What would you like to do? Choose one of the options: \n [-] Upload\n [-] MultiUpload\n [-] Download \n [-] List \n [-] Delete \n [-] Quit \n")
            if (message == 'Upload'):
                uploadMode(sock,username)
                continue
            elif (message == 'MultiUpload'):
                multiUploadMode(sock,username)
                continue
            elif (message == 'Download'):
                downloadMode(sock)
                continue
            elif (message == 'List'):
                listMode(sock,username)
                continue
            elif (message == 'Delete'):
                deleteMode(sock)
                continue
            elif (message == 'Quit'):
                print("Closing the link to the server")
                try:
                    sock.send(("<QUIT># # # # # #".encode('utf-8')))
                except BrokenPipeError:
                    print("Connection Interrupted")
                break
            else:
                print("Please choose from one of the listed options.")
                continue
    finally:
        sock.close()

#Function for turning client commands into the correct protocol format
def buildHeader(command, filename=' ', filesize=' ', filestate=' ', password=' ',checksum = ' ', username = ' '):
    return f'{command}#{filename}#{filesize}#{filestate}#{password}#{checksum}#{username}'


#Function for a client to decode a header from the server
def decodeHeader(header,pos):
    return header.split("#")[pos]

#Function for a client to retrieve a file from the server
def downloadMode(sock):
    try:
        filename = input("Enter the name of the file: ")
        password = input("Enter the password (leave blank for no password): ")
        sock.send(bytes(buildHeader("<WRITE>",filename, password=password),"utf-8"))
        command,filename,filesize,filestate,password,checksum = sock.recv(1024).decode("utf-8").split('#')
        if "<FAILED>" in command:
            print(command[8:])
        elif command == "<OK>":
            hash_no = hashlib.md5()
            #receive the file in packets
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
            #Open te file to write the bytes
            if(byte_total == filesize and hash_no.hexdigest() == checksum):
                f.close()
            else:
                print("Download Failed")
    except BrokenPipeError:
        print("Action Failed. Connection interrupted")

  
#Function to send a file to the server
def uploadMode(sock, username, multi=False):
    try:
        filename = input("Enter the name of the file: ")
        password = input("Enter the password (leave blank for no password): ")
        filesize = os.path.getsize(filename)
        filestate = "open" if password == "" else "protected"
        #send the header
        sock.send(bytes(buildHeader("<READ>", filename, filesize,username=username,filestate=filestate,password=password, checksum=generateChecksum(filename)),"utf-8"))
        #open the file to send
        file = open(filename, "rb")
    
        #Breakdown packets 
        while True:
            packet = file.read(1024)
            if not packet:
                break
            sock.sendall(packet)
        file.close()

        if multi==False:
            returnedMessage = sock.recv(1024).decode("utf-8")
            print(returnedMessage)
    except BrokenPipeError:
        print("Failed. Connection was interrupted")

#Function to list all files on the server
def listMode(sock,username):
    sock.send(bytes(buildHeader("<LIST>",username=username),"utf-8"))
    header = sock.recv(1024).decode("utf-8")
    filelist = sock.recv(1024).decode("utf-8")
    print(filelist)
    
#Function to delete a file on the server
def deleteMode(sock):
    filename = input('Please input the file name that you would like to delete:\n')
    password = input('Please input the password for the file (if none leave blank):\n')
    sock.send(bytes(buildHeader("<DELETE>", filename, "", "", password), "utf-8"))
    returnedMessage = sock.recv(1024).decode("utf-8")
    print(returnedMessage)


#Function to allow for multiple files to be uploaded 
def multiUploadMode(sock,username):
    #Number of files to send
    nFiles=input("How many filed do you wish to upload?(1-100):\n")

    #Check if number is valid
    if nFiles.isdigit() and int(nFiles)>0:
        nFiles=int(nFiles)
        #For loop to go through all files
        for x in range(nFiles):
            uploadMode(sock,username, True)
            returnedMessage = sock.recv(1024).decode("utf-8")
            print(returnedMessage)
    else:
        print("This is not a valid number")
  

#Function for hashing the file contents before sending or after receiving a file 
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