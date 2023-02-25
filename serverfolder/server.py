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
    print(file_keys)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((socket.gethostname(), 1239))
    s.listen(5)

    while True:
        clientsocket, address = s.accept()
        print(f"connection from {address} has been established!")
        start_new_thread(doThings,(clientsocket,address))
    

def doThings(sock,addr):
    try:
        counter = 0
        while True:
            header = sock.recv(1024).decode("utf-8")
            command,filename,filesize, filestate,password = header.split("#")
            if(command == '<READ>'):
                receiveMode(sock,filename,filesize,filestate,password)
                break
            elif(command == '<WRITE>'):
                sendMode(sock,filename,password)
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
def receiveMode(sock,filename,filesize, filestate,password):
    file_keys[filename] = (filestate,password)
    
    #data to write to file
    file_bytes = b""

    #recieve the file in packets
    while True:
        packet = sock.recv(1024)
        if not packet:
            break
        file_bytes += packet
    
    #open the file to write to and write to the file
    if(len(file_bytes) == filesize):
        file = open(filename, "wb")
        file.write(file_bytes)
        file.close()
        return
    else:
        print("Transfer failed")
        return
    
#function to send a file from the server to a client
def sendMode(sock,filename,password):
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