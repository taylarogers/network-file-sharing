import socket
import os
from _thread import *
import threading
import json

file_keys = {}
blacklist = ["Tomas"]
user_credentials = {}

def init():
    if not os.path.exists("filekeys.json"):
        with open('filekeys.json','w') as outfile:
            json.dump(file_keys, outfile)
    if not os.path.exists("user_credentials.json"):
        with open('user_credentials.json','w') as outfile:
            json.dump(user_credentials, outfile)
    
def main():
    init()
    with open('filekeys.json') as infile:
            file_keys = json.load(infile)
    with open('user_credentials.json') as infile:
            user_credentials = json.load(infile)
    print("Starting server...")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((socket.gethostname(), 1231))
    s.bind((socket.gethostname(), 1232))
    s.listen(5)

    for i in range(4): #wait for one client to connect
        clientsocket, address = s.accept()
        print(f"connection from {address} has been established!")
        
        #get login details
        getlogin(clientsocket,user_credentials)
                
        start_new_thread(doThings,(clientsocket,address,file_keys,user_credentials))

    print(file_keys)
    with open('filekeys.json','w') as outfile:
            json.dump(file_keys, outfile)
    with open('user_credentials.json','w') as outfile:
            json.dump(user_credentials, outfile)
    s.close()
    return

def doThings(sock,addr,file_keys,user_credentials):
    print("Thread started")
    try:
        while True:
            print("awaiting message")
            header = sock.recv(1024).decode("utf-8")
            command,filename,filesize,filestate,password = header.split("#")
            if(command == '<READ>'):
                uploadMode(sock,filename,filesize,filestate,password,file_keys)
                continue
            elif(command == '<WRITE>'):
                downloadMode(sock,filename,password)
                continue
            elif(command == '<LIST>'):
                listMode(sock, file_keys)
                continue
            elif (command == '<DELETE>'):
                checkForPassword(sock, filename,password,file_keys)
                listMode(sock)
                continue
            elif(command == '<REG>'):
                addUser(sock,user_credentials)
                continue
            elif(command == '<QUIT>'):
                print("Closing server link...")
                break
            else:
                print("Invalid Message")
                counter+=1
                if(counter > 3): break
                continue
    finally:
        with open('filekeys.json','w') as outfile:
            json.dump(file_keys, outfile)
        with open('user_credentials.json','w') as outfile:
            json.dump(user_credentials, outfile)
        sock.close()

def buildHeader(command, filename='', filesize='', filestate='', password=''):
    return f"{command}#{filename}#{filesize}#{filestate}#{password}"

def decodeHeader(header):
    return header.split("#")

def getlogin(sock,user_credentials):
    username,password = sock.recv(1024).decode('utf-8').split("<SPLIT>")
    print("Creds recv", username,password)
    if username in user_credentials:
        print("They're in")
        if user_credentials[username][1] == "banned":
            sock.send(bytes("<BANNED>#Error. User is banned. Please contact a systems administrator",'utf-8'))
            sock.close()
        elif user_credentials[username][1] == "ok" and user_credentials[username][0] == password:
            sock.send(bytes("<OK>#Password accepted. User login successful!",'utf-8'))
        elif user_credentials[username][1] == "ok" and user_credentials[username][0] != password:
            sock.send(bytes("<INVALID>#Password denied. Please enter a valid password.",'utf-8'))
    else:
        print("They're not in")
        user_credentials[username] = (password,"ok")
        sock.send(bytes("<OK>",'utf-8'))
    return

#function for receiving a file to be stored

def uploadMode(sock,filename,filesize, filestate,password,file_keys):
    
    file_keys[filename] = (filestate,password)
    print("opening file")
    with open(f"./Files/{filename}","wb") as f: 
        print("opened file")
        byte_total = 0
        filesize = int(filesize)
        counter = 0
        while True:
            # read 1024 bytes from the socket (receive)
            bytes_read = sock.recv(1024)
            byte_total += len(bytes_read)
            if byte_total >= filesize:
                f.write(bytes_read)
                break
            elif not bytes_read:    
                # if nothing is coming through then we are done
                break
            # write to the file the bytes we just received
            print(f"writing_bytes {counter}")
            f.write(bytes_read)
            counter += 1
    print("bytes written")
    f.close()
    return
    
def addUser(sock,user_credentials):
    username,password,permissions = sock.recv(1024).decode('utf-8').split("#")
    #if the user does not have credentials with the server then add them
    if username not in user_credentials:
        user_credentials[username] = password

#function to send a file from the server to a client
def downloadMode(sock,filename,password):
    file = open(filename, "rb")
    filesize = os.path.getsize(filename)
    filestate,pwd = file_keys[filename]
    if filestate == 'protected' and password == pwd:
        sock.send(bytes(buildHeader("<WRITE>",filename,filesize,password),"utf-8"))
        while True:
            packet = file.read(1024)
            if not packet:
                break
            sock.send(packet)
        file.close()
    else:
        sock.send(bytes(buildHeader("<FAILED>",filename,filesize,password),"utf-8"))

#function to return a list of files available on the server   
def listMode(sock, file_keys):
    #send the header
    sock.send(bytes(buildHeader(command="<LIST>"),"utf-8"))
    filelist = " > \n"

    for filename in file_keys.keys():
        values = file_keys[filename]
        status = values[0]
        filelist = filelist + f" > {filename} ({status}) \n"

    filelist = filelist + " >"

    sock.send(bytes(filelist,"utf-8"))

# Function to delete
def deleteMode(sock, filename,file_keys):
    try:
        os.remove(f"./Files/{filename}")
        del file_keys[filename]
        sock.send(bytes(f"[*] Successfully deleted {filename}", "utf-8"))
    except:
        print("[X] File not found")
        sock.send(bytes(f"[X] Could not find {filename} - please choose a file that already exists", "utf-8"))

def checkForPassword(sock, filename, password, file_keys):
    if file_keys.get(filename) == None:
        sock.send(bytes(f"[X] {filename} does not exist and cannot be deleted"))
    else:
        values = file_keys.get(filename)

        if values[0] == "open":
            deleteMode(sock, filename, file_keys)
        elif values[1] == password:
            deleteMode(sock, filename, file_keys)
        else:
            sock.send(bytes(f"[X] Incorrect password for {filename} - cannot delete file"))

if __name__ == "__main__":
    main()