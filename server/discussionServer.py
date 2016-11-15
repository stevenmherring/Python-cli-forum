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
SUB_S = "s"
SUB_U = "u"
SUB_N = "n"
SUB_Q = "q"

"""
Socket Information
"""
PACKET_LENGTH = 4096
PORT_NUMBER = 9390

"""
Default Server Values
"""
CLIENT_DATA_FILE = "/clients/ids.json"
GROUPS_PATH = "/groups/"
DEFAULT_N = 3

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
            try:
                req = clientSocket.recv(PACKET_LENGTH)
                message = json.loads(req)
                msgType = message["type"].lower()
                if !loggedIn and msgType == REQUEST_LOGIN:
                    userID = message["arg1"]
                    loginClient(clientSocket, userID, offline_clients, online_clients, loggedIn)
                elif msgType == REQUEST_HELP:
                    res = helpMenu()
                    clientSocket.send(json.dumps(res))
                elif msgType == REQUEST_LOGOUT:
                    logoutClient(clientSocket, userID, offline_clients, online_clients, loggedIn)
                elif loggedIn:
                    if message["N"] == None:
                        n = DEFAULT_N
                    else:
                        n = int(message["N"])
                    if msgType == REQUEST_AG:
                        #available mode
                        enterAG(clientSocket, userID, n)
                    elif msgType == REQUEST_SG:
                        #subscribe mode
                        enterSG()
                    elif msgType == REQUEST_RG:
                        #read mode
                        enterRG()
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
    """
    Loads the clients on startup from client file
    """
    global offline_clients
    global lock
    #load clients
    with lock:
        with open(CLIENT_DATA_FILE, "r") as f:
            clientData = json.loads(f.read())
            offline_clients = clientData["clients"]

def loginClient(clientSocket, userID, offline_clients, online_clients, loggedIn):
    """
    Checks if the user is logged off & exits then logs them in
    """
    global lock
    clientData = {}
    with lock:
        clientData = next((client for client in offline_clients if client["id"] == userID), None)
        if clientData != None:
            online_clients.append(clientData)
            offline_clients[:] = [client for client in offline_clients if client.get("id") != userID]
            loggedIn = True
            res = responseBuilder("Success", ("User ID: " + userID + " logged in successfully."))
            clientSocket.send(json.dumps(res))
            return True
        else:
            #user doesn't exists
            res = responseBuilder("Error", ("User ID: " + userID + " does not exist."))
            clientSocket.send(json.dumps(res))
            return False

def logoutClient(clientSocket, userID, offline_clients, online_clients, loggedIn):
    """
    Checks if the user is logged in and logs them out
    """
    global lock
    clientData = {}
    with lock:
        clientData = next((client for client in online_clients if client["id"] == userID), None)
        if clientData != None:
            offline_clients.append(clientData)
            online_clients[:] = [client for client in online_clients if client.get("id") != userID]
            loggedIn = False
            res = responseBuilder("Success", ("User ID: " + userID + " logged out successfully."))
            clientSocket.send(json.dumps(res))
            return True
        else:
            #user doesn't exists
            res = responseBuilder("Error", ("User ID: " + userID + " does not exist."))
            clientSocket.send(json.dumps(res))
            return False

def enterAG(clientSocket, userID, msgCount):
    """
    Available Group Mode, Allows user to use special commands
    s – subscribe to groups. It takes one or more numbers between 1 and N as arguments. E.g., given the output above, the user may enter “s 1 3” to subscribe to two more groups: comp.programming and comp.lang.c
    u – unsubscribe. It has the same syntax as the s command, except that it is used to unsubscribe from one or more groups. E.g., the user can unsubscribe from group comp.lang.javascript by entering the command “u 5”
    n – lists the next N discussion groups. If all groups are displayed, the program exits from the ag command mode
    q – exits from the ag command, before finishing displaying all groups
    """
    global groups
    messageCount = 0
    res = {
        "type": "Success"
        "groupList": []
    }
    if (messageCount + msgCount) > len(groups):
        maxRange = len(groups)
    else:
        maxRange = messageCount + msgCount
    for i in range(messageCount, maxRange):
        with lock:
            res[groupList].add(groups[i])
    clientSocket.send(json.dumps(res))
    while True:
        res = {}
        req = clientSocket.recv(PACKET_LENGTH)
        message = json.loads(req)
        msgType = message["type"].lower()
        if msgType != REQUEST_AG:
            res = responseBuilder("Error", "Wrong mode type, in AG requesting " + msgType)
            clientSocket.send(json.dumps(res))
            return False
        subcommand = message["subcommand"].lower()
        if subcommand == SUB_S:
            #subscribe groups
            selections = message["selections"]
            for s in selections:
                if s not in clients[userID][subscriptions]:
                    clients[userID][subscriptions].append(s)
        elif subcommand == SUB_U:
            #unsubscribed
            selections = message["selections"]
            for s in selections:
                if s in clients[userID][subscriptions]:
                    clients[userID][subscriptions].remove(s)
        elif subcommand == SUB_N:
            #lists next N groups
            msgCount = int(message["N"])
            res = {
                "type": "Success"
                "groupList": []
            }
            if (messageCount + msgCount) > len(groups):
                maxRange = len(groups)
            else:
                maxRange = messageCount + msgCount
            for i in range(messageCount, maxRange):
                with lock:
                    res[groupList].add(groups[i])
            clientSocket.send(json.dumps(res))
        elif subcommand == SUB_Q:
            #exits AG moder
            res = responseBuilder("Success", "Exit AG Mode successfully.")
            clientSocket.send(json.dumps(res))
            return True
        else:
            #bad command
            res = responseBuilder("Error", "Bad command. Please refer to help")
            clientSocket.send(json.dumps(res))

def enterSG(clientSocket, userID):

def enterRG(clientSocket, userID):


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
