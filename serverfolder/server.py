import socket
import os
from _thread import *
import threading
import json

file_keys = {}

def init():
    if not os.path.exists("filekeys.json"):
        with open('filekeys.json','w') as outfile:
            json.dump(file_keys, outfile)
    
def main():
    init()
    with open('filekeys.json') as infile:
            file_keys = json.load(infile)
    print("Starting server...")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((socket.gethostname(), 1239))
    s.listen(5)

    for i in range(2): #wait for one client to connect
        clientsocket, address = s.accept()
        print(f"connection from {address} has been established!")
        start_new_thread(doThings,(clientsocket,address,file_keys))

    print(file_keys)
    with open('filekeys.json','w') as outfile:
            json.dump(file_keys, outfile)
    s.close()
    return

def doThings(sock,addr,file_keys):
    try:
        counter = 0
        while True:
            header = sock.recv(1024).decode("utf-8")
            command,filename,filesize, filestate,password = header.split("#")
            if(command == '<READ>'):
                uploadMode(sock,filename,filesize,filestate,password,file_keys)
                break
            elif(command == '<WRITE>'):
                downloadMode(sock,filename,password)
                break
            elif(command == '<LIST>'):
                listMode(sock)
                break
            elif(command == '<QUIT>'):
                print("Closing server link...")
                break;
            else:
                print("Invalid Message")
                counter+=1
                if(counter > 3): break
                continue
    finally:
        with open('filekeys.json','w') as outfile:
            json.dump(file_keys, outfile)
        sock.close()

def buildHeader(command, filename='', filesize='', filestate='', password=''):
    return f"{command}#{filename}#{filesize}#{filestate}#{password}"

def decodeHeader(header):
    return header.split("#")

#function for receiving a file to be stored

def uploadMode(sock,filename,filesize, filestate,password,file_keys):

    file_keys[filename] = (filestate,password)
    
    with open(filename,"wb") as f: 
        while True:
            # read 1024 bytes from the socket (receive)
            bytes_read = sock.recv(1024)
            if not bytes_read:    
                # if nothing is coming through then we are done
                break
            # write to the file the bytes we just received
            f.write(bytes_read)
        f.close()
    

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