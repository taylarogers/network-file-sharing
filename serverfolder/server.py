import socket
import os
from _thread import *
import threading
import json
import hashlib

PORT_NO = 1230

file_keys = {}
blacklist = ["Tayla"]
user_credentials = {}

# If the storage files do not exist then create them and store the data currently stored in the dictionaries in them
def data_init():
    if not os.path.exists("filekeys.json"):
        with open('filekeys.json','w') as outfile:
            json.dump(file_keys, outfile)
    if not os.path.exists("user_credentials.json"):
        with open('user_credentials.json','w') as outfile:
            json.dump(user_credentials, outfile)

# Main method that is run every time the server is started 
def main():
    data_init()

    # Load data from files into dictionaries
    with open('filekeys.json') as infile:
            file_keys = json.load(infile)
    with open('user_credentials.json') as infile:
            user_credentials = json.load(infile)

    # Start the server
    print("[*] Starting server...")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((socket.gethostname(), PORT_NO))
    s.listen(5)

    # Wait for a client to connect to the server
    for i in range(4):
        clientsocket, address = s.accept()
        print(f"[*] Connection established: {address}.")
        
        # Get login details to verify ability to use server
        # Code 1 means that the login was unsuccessful
        if getlogin(clientsocket,user_credentials) == 1:
            continue
                
        start_new_thread(commands,(clientsocket,address,file_keys,user_credentials))

    # Load everything that is in dictionaries back into the files for storage
    with open('filekeys.json','w') as outfile:
            json.dump(file_keys, outfile)
    with open('user_credentials.json','w') as outfile:
            json.dump(user_credentials, outfile)

    # Close server
    s.close()
    return

# Function that decides what is done in the server based off of user input
def commands(sock,addr,file_keys,user_credentials):
    print("[*] Thread started.")

    # Decide what actions to take
    try:
        while True:
            print("[*] Awaiting message...")

            # Receive input from client
            header = sock.recv(1024).decode("utf-8")
            command,filename,filesize,filestate,password,checksum = header.split("#")

            if(command == '<READ>'):
                uploadMode(sock,filename,filesize,filestate,password,checksum,file_keys)
                continue
            elif(command == '<WRITE>'):
                downloadMode(sock,filename,password,file_keys)
                continue
            elif(command == '<LIST>'):
                listMode(sock, file_keys)
                continue
            elif (command == '<DELETE>'):
                checkForPassword(sock, filename,password,file_keys)
                continue
            elif(command == '<REG>'):
                addUser(sock,user_credentials)
                continue
            elif(command == '<QUIT>'):
                print(f"[*] Closing client link: {addr}...")
                break
            else:
                print("[X] Invalid message.")
                counter+=1
                if(counter > 3): break
                continue
    finally:
        # Write dictionary data to files
        with open('filekeys.json','w') as outfile:
            json.dump(file_keys, outfile)
        with open('user_credentials.json','w') as outfile:
            json.dump(user_credentials, outfile)
        sock.close()

# Compile a header in format of created protocol
def buildHeader(command, filename='', filesize='', filestate='', password='',checksum=''):
    return f"{command}#{filename}#{filesize}#{filestate}#{password}#{checksum}"

# Break down received header
def decodeHeader(header):
    return header.split("#")

# Check user login details against records
def getlogin(sock,user_credentials):
    # Receive details from client
    username,password = sock.recv(1024).decode('utf-8').split("<SPLIT>")
    print(f"[*] Login: details received for {username}")

    if username in user_credentials:
        # If the user is registered
        if user_credentials[username][1] == "banned":
            print(f"[X] Login: {username} is banned from the system.")
            sock.send(bytes("<BANNED>#[X] User is banned - please contact a systems administrator.",'utf-8'))
            sock.close()
            return 1
        elif user_credentials[username][1] == "ok" and user_credentials[username][0] == password:
            print(f"[*] Login: {username} is logged in.")
            sock.send(bytes("<OK>#[*] Password accepted - user login successful.",'utf-8'))
            return 0
        elif user_credentials[username][1] == "ok" and user_credentials[username][0] != password:
            print(f"[X] Login: {username} has entered an incorrect password.")
            sock.send(bytes("<INVALID>#[X] Password denied - please enter a valid password for this account.",'utf-8'))
            return 1
    else:
        # If the user is not registered
        print(f"[*] Login: {username} has created an account.")
        user_credentials[username] = (password,"ok")
        sock.send(bytes("<OK>#[*] Account created - user login successful.",'utf-8'))
        return 0

# Storing a file on the server
def uploadMode(sock,filename,filesize, filestate,password,checksum,file_keys):
    print(f"[*] Upload: storing {filename}")
    
    file_keys[filename] = (filestate,password)

    # Write bytes to a new file
    with open(f"./Files/{filename}","wb") as f: 
        byte_total = 0
        filesize = int(filesize)

        while True:
            # Read 1024 bytes from the socket (receive)
            bytes_read = sock.recv(1024)
            byte_total += len(bytes_read)

            if byte_total >= filesize:
                f.write(bytes_read)
                break
            elif not bytes_read:    
                # if nothing is coming through then we are done
                break

            # Write to the file the bytes we just received
            f.write(bytes_read)

        print(f"[*] Upload: {filename} stored.")

        # Close file
        f.close()

    if filesize == os.path.getsize(f"./Files/{filename}") and checksum == generateChecksum(f"./Files/{filename}"):
        # Send message back to client for feedback
        sock.send(bytes(f"[*] Upload: {filename} uploaded successfully.", "utf-8"))
    else:
        # Send message back to client for feedback
        sock.send(bytes(f"[X] Upload: there was an issue transmitting {filename}.", "utf-8"))    
    return

####### DELETE????? ADMIN ROLE NECESSARY   
# Add user credentials to stored values
def addUser(sock,user_credentials):
    # Receive user information
    username,password,permissions = sock.recv(1024).decode('utf-8').split("#")

    # If credentials not stored on server then add them
    if username not in user_credentials:
        user_credentials[username] = password

# Sending a file on the server to the client
def downloadMode(sock,filename,password,file_keys):
    file = open(f"./Files/{filename}", "rb")
    filesize = os.path.getsize(f"./Files/{filename}")
    filestate,pwd = file_keys[filename]

    # Check for ability to be able to download file
    if (filestate == 'protected' and password == pwd) or (filestate == 'open'):
        sock.send(bytes(buildHeader("<OK>",filename,filesize,password,checksum=generateChecksum(f"./Files/{filename}")),"utf-8"))
        # Send file bytes back to client
        while True:
            packet = file.read(1024)
            if not packet:
                break
            sock.sendall(packet)

        # Close the file
        file.close()

        print(f"[*] Download: {filename} sent.")
    else:
        # Send error message back to client
        sock.send(bytes(buildHeader("<FAILED>",filename,filesize,password),"utf-8"))
        print(f"[*] Download: {filename} failed to send.")

# Listing the available files on the server
def listMode(sock, file_keys):
    # Send the header
    sock.send(bytes(buildHeader(command="<LIST>"),"utf-8"))
    filelist = " > \n"

    # Create list of filenames and their protection status
    for filename in file_keys.keys():
        values = file_keys[filename]
        status = values[0]
        filelist = filelist + f" > {filename} ({status}) \n"

    filelist = filelist + " >"

    # Send list
    sock.send(bytes(filelist,"utf-8"))

    print(f"[*] List: files listed on server sent.")

# Deleting a file on the server
def deleteMode(sock, filename,file_keys):
    try:
        # Remove from physical folder and from dictionary
        os.remove(f"./Files/{filename}")
        del file_keys[filename]
        sock.send(bytes(f"[*] Delete: {filename} successfully deleted.", "utf-8"))
        print(f"[*] Delete: {filename} deleted.")
    except:
        # Send error message
        print(f"[X] Delete: {filename} not found.")
        sock.send(bytes(f"[X] Delete: {filename} not found - please choose a file that already exists.", "utf-8"))

# Check if a password is valid for access to certain files
def checkForPassword(sock, filename, password, file_keys):
    # Check if file exists in the dictionary
    if file_keys.get(filename) == None:
        print(f"[X] Delete: invalid access to {filename} which does not exist.")
        sock.send(bytes(f"[X] Delete: {filename} not found - cannot be deleted.", "utf-8"))
    else:
        values = file_keys.get(filename)

        # Check if the file is password protected or not
        if values[0] == "open":
            deleteMode(sock, filename, file_keys)
        elif values[1] == password:
            deleteMode(sock, filename, file_keys)
        else:
            print(f"[X] Delete: incorrect password entered for {filename}.")
            sock.send(bytes(f"[X] Delete: incorrect password for {filename} - cannot delete file", "utf-8"))

def generateChecksum(filename):
    checksum = hashlib.md5()
    with open(filename, 'rb') as file:
        while True:
            data = file.read(1024*64)
            if not data:
                break
            checksum.update(data)
    return checksum.hexdigest()

if __name__ == "__main__":
    main()