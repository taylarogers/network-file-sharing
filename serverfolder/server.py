import socket
import os
from _thread import *
import threading
import json

file_keys = {}
blacklist = ['123.45.67']
no_clients = 0

def init():
    if not os.path.exists("filekeys.json"):
        with open('filekeys.json','w') as outfile:
            json.dump(file_keys, outfile)
    with open('filekeys.json') as infile:
            file_keys = json.load(infile)
    
def main():
    init()
    print("Starting server...")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((socket.gethostname(), 1237))
    s.listen(5)
    no_clients = 0

    while True:
        print(no_clients)
        clientsocket, address = s.accept()
        print(f"connection from {address} has been established!")
        if clientsocket.recv(1024).decode('utf-8') in blacklist:
            print("Connection refused.")
            clientsocket.send(bytes("<FAILED>",'utf-8'))
            clientsocket.close()
        else:
            clientsocket.send(bytes("<SUCCEEDED>",'utf-8'))
            start_new_thread(doThings,(clientsocket,address, no_clients))
            no_clients += 1

def doThings(sock,addr,no_clients):
    try:
        counter = 0
        while True:
            header = sock.recv(1024).decode("utf-8")
            command,filename,filesize, filestate,password = header.split("#")
            if(command == '<READ>'):
                uploadMode(sock,filename,filesize,filestate,password)
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
        print("Dumping JSON")
        sock.close()
        no_clients -= 1
        return

def buildHeader(command, filename='', filesize='', filestate='', password='', usrtype = 'default'):
    return f"{command}#{filename}#{filesize}#{filestate}#{password}{usrtype}"

def decodeHeader(header):
    return header.split("#")

def uploadMode(sock,filename,filesize, filestate,password):

    file_keys[filename] = (filestate,password)
    
    with open(filename,"wb") as f: 
        while True:
            # read 1024 bytes from the socket (receive)
            bytes_read = sock.recv(4096)
            if not bytes_read:    
                # if nothing is coming through then we are done
                break
            # write to the file the bytes we just received
            f.write(bytes_read)
    
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

def listMode(sock):
    #send the header
    sock.send(bytes(buildHeader(command="<LIST>"),"utf-8"))
    filelist = os.listdir(os.curdir)
    sock.send(bytes(" >" + "\n >".join(filelist) ,"utf-8"))

if __name__ == "__main__":
    main()