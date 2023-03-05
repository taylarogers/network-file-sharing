import socket
import os
import hashlib
import sys

def main():
    # Collect any command line arguments if there are, specifying the IP address and port number of the server
    numCommands = len(sys.argv)

    if numCommands < 3:
        IP_ADDR = '127.0.0.1'
        PORT_NO = 1230
    else:
        IP_ADDR = sys.argv[1]
        PORT_NO = int(sys.argv[2])

    # Create socket 
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((IP_ADDR, PORT_NO))

    try:
        # Welcoming message
        print('     (¯`·.¸¸.·´¯`·.¸¸.·´¯)')
        print('     ( \                 / )')
        print('    ( \ )    Welcome    ( / )')
        print('   ( ) (       to        ) ( )')
        print('    ( / )  the server!  ( \ )')
        print('     ( /                 \ )')
        print('      (_.·´¯`·.¸¸.·´¯`·.¸_)')
        print('[*] Please login to access features.')

        # Get the user to login with their details
        username = input("[-] Username: ")
        password = input("[-] Password: ")

        # Send login details to server and received a message back depicting if successful
        sock.send(bytes(f"{username}<SPLIT>{password}",'utf-8'))
        status, message = sock.recv(1024).decode('utf-8').split("#")

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

        # Prompt user to interact with the server with specified actions
        while (True):
            # Receive the user action
            action = input("[*] Enter the action you would like to perform: \n -> Upload \n -> Download \n -> List \n -> Delete \n -> Quit \n[-] ")

            if (action == 'Upload'):
                # Check if it is a multiple or single upload
                uploadOption = input('[*] How many files would you like to upload? \n -> One \n -> Many \n[-] ')

                if (uploadOption == 'One'):
                    uploadMode(sock, username)
                elif (uploadOption == 'Many'):
                    multiUploadMode(sock, username)
                else:
                    print('[X] Incorrect command entered. Please try again.')

                continue
            elif (action == 'Download'):
                downloadMode(sock)
                continue
            elif (action == 'List'):
                listMode(sock,username)
                continue
            elif (action == 'Delete'):
                deleteMode(sock)
                continue
            elif (action == 'Quit'):
                print("[*] Closing server link...")
                try:
                    sock.send(bytes(buildHeader("<QUIT>"),"utf-8"))
                except BrokenPipeError:
                    print("[X] Connection Interrupted.")
                break
            else:
                print('[X] Incorrect command entered. Please try again.')
                continue
    finally:
        sock.close()

# Build header in protocol standard
def buildHeader(command, filename=' ', filesize=' ', filestate=' ', password=' ',checksum = ' ', username = ' '):
    return f'{command}#{filename}#{filesize}#{filestate}#{password}#{checksum}#{username}'


# Decode header in protocl standard
def decodeHeader(header,pos):
    return header.split("#")[pos]

# Uploading multiple files at once
def multiUploadMode(sock, username):
    # Determine how many files to send
    num = input("[*] How many files would you like to upload? (1-100): \n[-] ")

    # Determine if valid number
    if num.isdigit() and int(num) > 0:
        num=int(num)

        # Retrieve all the files
        for fileNum in range(num):
            uploadMode(sock, username, True)
            returnedMessage = sock.recv(1024).decode("utf-8")
            print(returnedMessage)
    else:
        print("[X] This is not a valid number. Please try again.")
    
# Upload a file to the server
def uploadMode(sock, username, multi=False):
    try:
        filename = input("[*] Filename: \n[-] ")

        enteringPassword = input('[*] Would you like to password protect this file? \n -> Yes \n -> No \n[-] ')
        password = ""

        if (enteringPassword == 'Yes'):
            password = input("[*] Password: \n[-] ")
            uploadFile(sock, filename, username, password)

            if multi==False:
                returnedMessage = sock.recv(1024).decode("utf-8")
                print(returnedMessage)
        elif (enteringPassword == 'No'):
            uploadFile(sock, filename, username, password)

            if multi==False:
                returnedMessage = sock.recv(1024).decode("utf-8")
                print(returnedMessage)
        else:
            print(print('[X] Incorrect command entered. Please try again.'))

    except BrokenPipeError:
        print("[X] Connection interrupted. Please try again.")

# Sending file
def uploadFile(sock, filename, username, password):
    try:
        # Determine file info
        filesize = os.path.getsize(f"./Files/{filename}")
        print(filesize)
        filestate = "open" if password == "" else "protected"

        # Send header
        sock.send(bytes(buildHeader("<READ>", filename, filesize,username=username,filestate=filestate,password=password, checksum=generateChecksum(f"./Files/{filename}")),"utf-8"))
        
        print("yebo")
        # Read packets from file to send to server
        file = open(f"./Files/{filename}", "rb")
        print("yes")

        while True:
            packet = file.read(1024)
            if not packet:
                break
            sock.sendall(packet)
        
        # Close the file
        file.close()
    except:
        print("[X] There was an error while uploading the file.")

# Retrieve file from server
def downloadMode(sock):
    try:
        # Accept file information from user
        filename = input("[*] Filename: \n[-] ")

        enteringPassword = input('[*] Is this file password protected? \n -> Yes \n -> No \n[-] ')
        password = ""

        if (enteringPassword == 'Yes'):
            password = input("[*] Password: \n[-] ")
            downloadFile(sock, filename, password)
        elif (enteringPassword == 'No'):
            downloadFile(sock, filename, password)
        else:
            print(print('[X] Incorrect command entered. Please try again.'))

    except BrokenPipeError:
        print("[X] Action Failed. Connection interrupted")

# Receieve file
def downloadFile(sock, filename, password):
    try:
        # Send request to server
        sock.send(bytes(buildHeader("<WRITE>",filename, password=password),"utf-8"))
        command,filename,filesize,filestate,password,checksum = sock.recv(1024).decode("utf-8").split('#')

        # Receive message from server
        if "<FAILED>" in command:
            print(command[8:])
        elif command == "<OK>":
            hash_no = hashlib.md5()

            # Recieve the file in packets and determine if it was altered in any way
            with open(filename,'wb') as f:
                byte_total = 0
                filesize = int(filesize)

                # Receives file bytes
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

            # Determines if the transfer was successful between server and client
            if(byte_total == filesize and hash_no.hexdigest() == checksum):
                f.close()
                print("[*] File downloaded successfully.")
            else:
                print("[X] The file was corrupted during the transfer. Please try again.")
    except: 
        print('[X] There was an error receiving this file. Please try again.')

# Deleting files from the server
def deleteMode(sock):
    try:
        # Get file information
        filename = input('[*] Filename:\n[-] ')

        enteringPassword = input('[*] Is this file password protected? \n -> Yes \n -> No \n[-] ')
        password = ""

        if (enteringPassword == 'Yes'):
            password = input("[*] Password: \n[-] ")
            deleteFile(sock, filename, password)
        elif (enteringPassword == 'No'):
            deleteFile(sock, filename, password)
        else:
            print(print('[X] Incorrect command entered. Please try again.'))
        
    except BrokenPipeError:
        print("[X] Action Failed. Connection interrupted")

# Deleting file
def deleteFile(sock, filename, password):
    # Send details to server
    sock.send(bytes(buildHeader("<DELETE>", filename, "", "", password), "utf-8"))

    # Display confirmation message
    returnedMessage = sock.recv(1024).decode("utf-8")
    print(returnedMessage)

# Listing all files that are currently hosted on the server
def listMode(sock, username):
    # Send instruction to server
    sock.send(bytes(buildHeader("<LIST>",username=username),"utf-8"))

    # Receive the information from the server
    header = sock.recv(1024).decode("utf-8")
    filelist = sock.recv(1024).decode("utf-8")

    # Display to user
    print(filelist)

# Checking if file has been corrupted during transmission by checking the values of the bits using hashing
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