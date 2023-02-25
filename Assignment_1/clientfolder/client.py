import socket
import os

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((socket.gethostname(), 1239))

    try:
        # accept console input for instructions
        while (True):
            # type the message to be sent
            message = input("What would you like to do? \n (s)end file, (r)etrieve file, (l)ist files, (q)uit \n")
            
            if (message == 's'):
                sendmode(sock)
                break
            elif (message == 'r'):
                recvmode(sock)
                break
            elif (message == 'l'):
                listmode(sock)
                break
            elif (message == 'q'):
                print("Closing server link...")
                sock.send(bytes(buildheader("<QUIT>"),"utf-8"))
                break
            else:
                print("Please enter a valid message.")
                continue
    finally:
        sock.close()

def buildheader(command, filename='', filesize='', filestate='', password=''):
    return f"{command}#{filename}#{filesize}#{filestate}#{password}"

def decodeheader(header,pos):
    return header.split("#")[pos]

def sendmode(sock):
    #enter the name of the file you wish to send
    filename, password = input("Please enter the filename of the file you wish to send and the associated password: \n").split(" ")
    filesize = os.path.getsize(filename)
    #send the header
    sock.send(bytes(buildheader("<READ>", filename, filesize, "protected", password=password),"utf-8"))
    #open the file to send
    file = open(filename, "rb")
    
    #read packets to send over
    while True:
        packet = file.read(1024)
        if not packet:
            break
        sock.send(packet)
    file.close()

def recvmode(sock):
    filename, password = input("Please enter the filename of the file you wish to send followed by the file password: \n").split(" ")
    sock.send(bytes(buildheader("<WRITE>",filename, password=password),"utf-8"))
    header = sock.recv(1024).decode("utf-8")
    command,filename_h, filesize_h= decodeheader(header,0), decodeheader(header,1),decodeheader(header,2)
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

def listmode(sock):
    sock.send(bytes(buildheader("<LIST>"),"utf-8"))
    header = sock.recv(1024).decode("utf-8")
    filelist = sock.recv(1024).decode("utf-8")
    print(filelist)

if __name__ == "__main__":
    main()