#!/usr/bin/env python
# discussionServer.py
"""
Python Discussion Application: Server
"""

from socket import *
from termcolor import colored #for setting output color source: https://pypi.python.org/pypi/termcolor
import threading, sys, os, time, StringIO, json

"""
String Messages
"""
IO_ERROR = "IO Error, terminating connection.\n"

"""
Color definitions
"""
COLOR_ERROR = "red"
COLOR_IMPORTANT = "cyan"

"""
Client commands
"""
REQUEST_LOGIN = "login"
REQUEST_LOGOUT = "logout"
REQUEST_HELP = "help"
REQUEST_AG = "ag"
REQUEST_SG = "sg"
REQUEST_RG = "rg"

"""
Socket Information
"""
PACKET_LENGTH = 4096
PORT_NUMBER = 9390

"""
Server data
"""
lock = threading.lock()
offline_clients = []
online_clients = []
groups = {} #pull from groups directory, each subdir is a group with *.txt files for each thread

class clientHandler(threading.Thread):
    """
    Handles new Client connections
    """
    def __init__(self, threadID, clientSocket, clientAddr):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.clientSocket = clientSocket
        self.clientAddr = clientAddr

    def run(self):
        global offline_clients
        global online_clients
        global groups

        loggedIn = False
        userID = ""
        while True:
            res = {}
            try:
                req = clientSocket.recv(PACKET_LENGTH)
                message = json.loads(req)
                msgType = message["type"].lower()
                if !loggedIn and msgType == REQUEST_LOGIN:
                    userID = message["arg1"]
                    if userID in offline_clients:
                        #login
                        with lock:
                            online_clients.append(userID)
                            offline_clients.remove(userID)
                        loggedIn = True
                        res = responseBuilder("Success", ("User ID: " + userID + " logged in successfully."))
                        clientSocket.send(json.dumps(res))
                    elif userID in online_clients:
                        #already logged in
                        res = responseBuilder("Error", ("User ID: " + userID + " is already logged in."))
                        clientSocket.send(json.dumps(res))
                    else:
                        #user doesn't exists
                        res = responseBuilder("Error", ("User ID: " + userID + " does not exist."))
                        clientSocket.send(json.dumps(res))
                elif msgType == REQUEST_HELP:
                    res = helpMenu()
                    clientSocket.send(json.dumps(res))
                elif msgType == REQUEST_LOGOUT:
                    if loggedIn:
                        with lock:
                            offline_clients.append(userID)
                            online_clients.remove(userID)
                        loggedIn = False
                        res = responseBuilder("Success", ("User ID: " + userID + " has been logged out."))
                        clientSocket.send(json.dumps(res))
                    else:
                        res = responseBuilder("Error", "Not logged in")
                        clientSocket.send(json.dumps(res))
                elif loggedIn:
                    if msgType == REQUEST_AG:
                        #available mode
                    elif msgType == REQUEST_SG:
                        #subscribe mode
                    elif msgType == REQUEST_RG:
                        #read mode
                    else:
                        sys.stdout.write(colored(("Unsupported command: " + msgType + " by client " + userID), COLOR_ERROR))
                        res = responseBuilder("Error", ("Unsupported command: " + msgType + " by client " + userID))
                        clientSocket.send(json.dumps(res))
                else:
                    sys.stdout.write(colored(("Unsupported command: " + msgType + " by client " + userID), COLOR_ERROR))
                    res = responseBuilder("Error", ("Unsupported command: " + msgType + " by client " + userID))
                    clientSocket.send(json.dumps(res))

            except IOError as err:
                sys.stdout.write(colored(err, COLOR_ERROR))
                res = {
                    "type": "Error",
                    "body": IO_ERROR
                }
                clientSocket.send(json.dumps(res))
        clientSocket.close()
        threadName.exit()

def responseBuilder(mtype, body):
    """
    Build and returns a json style response as basic protocol. Message Type and its body
    """
    response = {
        "type": mtype,
        "body": body
    }
    return response

def helpMenu():
    """
    Returns json style help menu
    """
    usage = """Server supported commands
    login clientID  - Attempts to login with clientID
    logout          - Logs out of current clientID
    help            - Display usage guide
    ag N            - Display available groups, N at a time default is 5
                    - ag mode, (S)ubscribe, (U)nsubscribe, (N)ext, (Q)uit
    sg N            - Display subscribed groups, N at a time default is 5
                    - sg mode, (U)nsubscribe, (N)ext, (Q)uit
    rg gname N      - Enters rg mode in group gname, displays N messages at a time default is 5
                    - rg mode
        [id]        - Reads message of number [id]. While in a message, 'q' to quit or 'n #' to read next # lines
        r [id]      - Marks [id] read
        n N         - Displays next N messages
        p           - Post a message
        q           - Exits rg mode
    """
    response = {
        "type": "Success",
        "body": usage
    }
    return response

def loadGroups():
    global groups
    #load groups

def loadClients():
    global offline_clients
    #load clients

def beginListening(serverSocket):
    """
    Listens for clients, spawns and sends client to new thread.
    """
    threadCount = 0
    while True:
        sys.stdout.write(colored("Waiting for clients...", COLOR_IMPORTANT))
        #accept client
        clientSocket, addr = serverSocket.accept()
        newThread = clientHandler(str(threadCount), clientSocket, clientAddr)
        threadCount = threadCount + 1
        newThread.start()

def main():
    """
    Def Main
    """
    sys.stdout.write(colored(("Server started on port " + PORT_NUMBER), COLOR_IMPORTANT))
    serverSocket = socket(AF_INET, SOCK_STREAM)
    serverSocket.bind("", PORT_NUMBER)
    serverSocket.listen(MAX_CLIENTS)
    beginListening(serverSocket)
    #cleanup
    serverSocket.close()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        raise SystemExit
