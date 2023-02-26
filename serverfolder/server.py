import socket
import os
from _thread import *
import threading
import json

file_keys = {}
blacklist = ["Tomas"]

def init():
    if not os.path.exists("filekeys.json"):
        with open('filekeys.json','w') as outfile:
            json.dump(file_keys, outfile)
    
def main():
    init()
    with open('filekeys.json') as infile:
            file_keys = json.load(infile)
    
    ######################
    print(file_keys)

    print("Starting server...")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((socket.gethostname(), 1235))
    s.listen(5)

    for i in range(4): #wait for one client to connect
        clientsocket, address = s.accept()
        if(clientsocket.recv(1024).decode('utf-8') in blacklist):
            clientsocket.sendall(bytes("<DENIED>",'utf-8'))
            clientsocket.close()
            continue
        else:
            clientsocket.sendall(bytes("<ALLOWED>",'utf-8'))
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
            print("awaiting message")
            header = sock.recv(1024).decode("utf-8")
            command,filename,filesize, filestate,password = header.split("#")
            if(command == '<READ>'):
                uploadMode(sock,filename,filesize,filestate,password,file_keys)
                continue
            elif(command == '<WRITE>'):
                downloadMode(sock,filename,password)
                continue
            elif(command == '<LIST>'):
                listMode(sock)
                continue
            elif (command == '<DELETE>'):
                checkForPassword(sock, filename,password,file_keys)
                print(file_keys)
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
        sock.close()

def buildHeader(command, filename='', filesize='', filestate='', password=''):
    return f"{command}#{filename}#{filesize}#{filestate}#{password}"

def decodeHeader(header):
    return header.split("#")

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
    ###########
    print(file_keys)
    return
    

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

# Function to delete
def deleteMode(sock, filename,file_keys):
    try:
        os.remove(f"./Files/{filename}")
        print(file_keys)
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