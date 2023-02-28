import socket
import os
from _thread import *
import threading
import json

file_keys = {}
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
        counter = 0
        while True:
            header = sock.recv(1024).decode("utf-8")
            command,filename,filesize,filestate,password = header.split("#")
            if(command == '<READ>'):
                uploadMode(sock,filename,filesize,filestate,password,file_keys)
                continue
            elif(command == '<WRITE>'):
                downloadMode(sock,filename,password)
                continue
            elif(command == '<LIST>'):
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
            sock.send(bytes("<BANNED>",'utf-8'))
            sock.send(bytes("Login failed. User is banned.",'utf-8'))
            sock.close()
        elif user_credentials[username][1] == "ok" and user_credentials[username][0] == password:
            sock.send(bytes("<OK>",'utf-8'))
            sock.send(bytes("Login successful!",'utf-8'))
    else:
        print("They're not in")
        user_credentials[username] = (password,"ok")
        sock.send(bytes("<OK>",'utf-8'))
        sock.send(bytes("New login detected, user registered on server.", 'utf-8'))
    return

#function for receiving a file to be stored

def uploadMode(sock,filename,filesize, filestate,password,file_keys):

    file_keys[filename] = (filestate,password)
    
    with open(filename,"wb") as f:
        total_bytes = b"" 
        while True:
            # read 1024 bytes from the socket (receive)
            bytes_read = sock.recv(1024)
            if len(total_bytes) == filesize:
                break
            if not bytes_read:    
                # if nothing is coming through then we are done
                break
            # write to the file the bytes we just received
        f.write(total_bytes)
        f.close()
    
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
def listMode(sock):
    #send the header
    sock.send(bytes(buildHeader(command="<LIST>"),"utf-8"))
    filelist = os.listdir(os.curdir)
    sock.send(bytes(" >" + "\n >".join(filelist),"utf-8"))

if __name__ == "__main__":
    main()