import os
import collections
import pickle
import platform
from socket import *

uploadSocket = socket(AF_INET,SOCK_STREAM)
uploadSocket.bind(("localhost",0))
uploadPort = uploadSocket.getsockname()[1]

if os.fork() == 0:
    #print("upload server running")
    uploadSocket.listen(1)
    close = False
    while close == False:
        connectionSocket, addr = uploadSocket.accept()
        optionInfo = pickle.loads(connectionSocket.recv(1024))
        if optionInfo[0] == "close":
            close = True
        elif optionInfo[0] == "file info":
            fileNum = optionInfo[1]
            name = "rfc" + fileNum + ".txt"
            values = [os.path.getmtime(name), os.path.getsize(name), "text", platform.system()]
            connectionSocket.send(pickle.dumps(values))
        elif optionInfo[0] == "download":
            fileNum = optionInfo[1]
            name = "rfc" + fileNum + ".txt"
            fp = open(name, "r")
            data = fp.read()
            connectionSocket.send(str(data).encode("utf-8"))
            fp.close()
        connectionSocket.close()
    #print("upload server closed")
    os._exit(0)
else:
    serverName = "localhost"
    serverPort = 7734
    clientSocket = socket(AF_INET, SOCK_STREAM)
    clientSocket.connect((serverName,serverPort))

    RFC_list = collections.deque()
    files = os.listdir('.')
    for f in files:
        if "rfc" in f:
            RFC_list.append(f)
    clientSocket.send(pickle.dumps([uploadPort, RFC_list]))
    while 1:
        option = input("Options\n 1 - list RFCs\n 2 - download RFC\n 3 - exit\n input: ")
        clientSocket.send(option.encode("utf-8"))
        if option == "1":
            server_RFCs = clientSocket.recv(1024).decode("utf-8")
            print(server_RFCs)
        if option == "2":
            rfcNum = input('RFC number: ')
            host = input('host: ')
            osVal = input("os: ")
            request_message = "GET RFC " + rfcNum + " P2P-CI/1.0"
            request_message += "\nHost: " + host
            request_message += "\nOS: " + osVal
            clientSocket.send(request_message.encode("utf-8"))
            response_message = pickle.loads(clientSocket.recv(1024))
            print(response_message[0])
            substrings = response_message[0].split()
            if substrings[1] == "200":
                downloadPort = response_message[1]
                uploadName = "localhost"
                downloadSocket = socket(AF_INET, SOCK_STREAM)
                downloadSocket.connect((uploadName,downloadPort))
                downloadSocket.send(pickle.dumps(["download", rfcNum]))
                name = "rfc" + rfcNum + ".txt"
                fp = open(name, "w")
                data = downloadSocket.recv(1024).decode("utf-8")
                while data:
                    fp.write(data)
                    data = downloadSocket.recv(1024).decode("utf-8")
                fp.close()
                downloadSocket.close()
        elif option == "3":
            break
    clientSocket.close()