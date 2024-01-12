import os
import multiprocessing
import pickle
import datetime
from socket import *

peer_list = multiprocessing.Manager().list()
RFC_list = multiprocessing.Manager().list()

serverPort = 7734
serverSocket = socket(AF_INET,SOCK_STREAM)
serverSocket.bind(("localhost",serverPort))
serverSocket.listen(1)
print("server running")
while 1:
    connectionSocket, addr = serverSocket.accept()
    if os.fork() == 0:
        print("subprocess open")
        serverSocket.close()

        peer_RFCs_and_uploadPort = connectionSocket.recv(1024)
        hostname = gethostname()
        for p in peer_list:
            if p[0] == gethostname():
                hostname = gethostname() + "-" + str(len(peer_list))
        peer_list.insert(0, [hostname, pickle.loads(peer_RFCs_and_uploadPort)[0]])
        for f in pickle.loads(peer_RFCs_and_uploadPort)[1]:
            RFC_number = int("".join(x for x in f if x.isdigit()))
            title = f
            RFC_list.insert(0, [RFC_number, title, hostname])
        close = False
        while close == False:
            option = connectionSocket.recv(1024)
            if option.decode("utf-8") == "1":
                response_message = "P2P-CI/1.0 200 OK"
                for rfc in RFC_list:
                    response_message += "\n" + str(rfc[0]) + " " + rfc[1] + " " + rfc[2]
                    for peer in peer_list:
                        if peer[0] == rfc[2]:
                            response_message += " " + str(peer[1])
                connectionSocket.send(response_message.encode("utf-8"))
            elif option.decode("utf-8") == "2":
                request_message = connectionSocket.recv(1024).decode("utf-8")
                substrings = request_message.split()
                rfcNum = substrings[2]
                host = substrings[5]
                exists = False
                for item in RFC_list:
                    if item[0] == int(rfcNum) and item[2] == host:
                        exists = True
                response_message = ""
                uploadPort = 0
                if exists:

                    for item in peer_list:
                        if item[0] == host:
                            uploadPort = item[1]
                    uploadName = "localhost"
                    clientSocket = socket(AF_INET, SOCK_STREAM)
                    clientSocket.connect((uploadName,uploadPort))
                    clientSocket.send(pickle.dumps(["file info", rfcNum]))
                    values = pickle.loads(clientSocket.recv(1024))
                    clientSocket.close()

                    response_message += "P2P-CI/1.0 200 OK"
                    response_message += "\nDate: " + str(datetime.datetime.now())
                    response_message += "\nOS: " + values[3]
                    response_message += "\nLast Modified: " + str(values[0]) + " seconds"
                    response_message += "\nContent-Length: " + str(values[1])
                    response_message += "\nContent-Type: " + str(values[2])

                    RFC_list.insert(0, [rfcNum, "rfc" + str(rfcNum) + ".txt", hostname])
                else:
                    response_message += "P2P-CI/1.0 404 Not Found"
                connectionSocket.send(pickle.dumps([response_message, uploadPort]))
            elif option.decode("utf-8") == "3":
                connectionSocket.send("connection closed".encode("utf-8"))
                close = True

        toRemove = []
        for item in RFC_list:
            if item[2] == hostname:
                toRemove.append(item)
        for item in toRemove:
            RFC_list.remove(item)

        uploadPort = 0
        for item in peer_list:
            if item[0] == hostname:
                uploadPort = item[1]
        uploadName = "localhost"
        clientSocket = socket(AF_INET, SOCK_STREAM)
        clientSocket.connect((uploadName,uploadPort))
        clientSocket.send(pickle.dumps(["close"]))
        clientSocket.close()

        toRemove = []
        for item in peer_list:
            if item[0] == hostname:
                toRemove.append(item)
                uploadPort = item[1]
        for item in toRemove:
            peer_list.remove(item)

        connectionSocket.close()
        print("subprocess closed")
        os._exit(0)
    connectionSocket.close()