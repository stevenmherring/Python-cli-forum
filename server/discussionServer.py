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
COLOR_OUTGOING = "magenta"

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
SUB_ID = "id"
SUB_R = "r"
SUB_P = "p"

"""
Socket Information
"""
PACKET_LENGTH = 4096
PORT_NUMBER = 9390

"""
Default Server Values
"""
CLIENT_DATA_FILE = "/clients/ids.json"
GROUPS_PATH = "/groups"
GROUPS_DATA_FILE = GROUPS_PATH + "/groups.json"
DEFAULT_N = 3
DELAY_PRINT = 0.03

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
        #mark dirty on data change, !dirty on data retrieval
        dirty = False
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
                        enterSG(clientSocket, userID, n)
                    elif msgType == REQUEST_RG:
                        #read mode
                        enterRG(clientSocket, userID, n)
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

def responseBuilder(threadID, mtype, body):
    """
    Build and returns a json style response as basic protocol. Message Type and its body
    """
    response = {
        "type": mtype,
        "body": body
    }
    sys.stdout.write(colored(json.dumps(response), COLOR_OUTGOING))
    sys.stdout.write(colored(("Thread: " + threadID + json.dumps(response)), COLOR_OUTGOING))
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
    """
    Loads the groups on startup
    """
    global groups
    global lock
    #load groups
    with lock:
        with open(GROUPS_DATA_FILE, "r") as f:
            groupsData = json.loads(f.read())
            groups = groupsData["groups"]

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
    Available Group Mode, Allows user to use special commands s, u, n, q
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

def enterSG(clientSocket, userID, msgCount):
    """
    Subscribed Group Mode, Allows user to use special commands u, n, q
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
        if msgType != REQUEST_SG:
            res = responseBuilder("Error", "Wrong mode type, in SG requesting " + msgType)
            clientSocket.send(json.dumps(res))
            return False
        subcommand = message["subcommand"].lower()
        if subcommand == SUB_U:
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
            res = responseBuilder("Success", "Exit SG Mode successfully.")
            clientSocket.send(json.dumps(res))
            return True
        else:
            #bad command
            res = responseBuilder("Error", "Bad command. Please refer to help")
            clientSocket.send(json.dumps(res))

def enterRG(clientSocket, userID, msgCount, groupName):
    """
    Read Group Mode, Allows user to use special commands [id], r, n, p, q
    """
    global groups
    messageCount = 0
    res = {}
    #build initial posting response ie. posts 1-msgCount
    while True:
        res = {}
        req = clientSocket.recv(PACKET_LENGTH)
        message = json.loads(req)
        msgType = message["type"].lower()
        if msgType != REQUEST_RG:
            res = responseBuilder("Error", "Wrong mode type, in RG requesting " + msgType)
            clientSocket.send(json.dumps(res))
            return False
        subcommand = message["subcommand"].lower()
        if subcommand == SUB_ID:
            #enter read post mode
            postName = message["postName"]
            enterDisplayPost(clientSocket, userID, postName)
        elif subcommand == SUB_R:
            #mark post read
            postSubject = message["postSubject"]
            postNum = message["postNumber"]
            markPost(userID, groupName, postSubject, postNum, "r")
        elif subcommand == SUB_N:
            #lists next N posts in groupName
            #TODO
        elif subcommand == SUB_P:
            #makes a new post in groupName
            postData = {} = message["body"]
            createPost(userID, postData)
        elif subcommand == SUB_Q:
            #exits AG mode
            res = responseBuilder("Success", "Exit RG Mode successfully.")
            clientSocket.send(json.dumps(res))
            return True
        else:
            #bad command
            res = responseBuilder("Error", "Bad command. Please refer to help")
            clientSocket.send(json.dumps(res))


def enterDisplayPost(clientSocket, userID, postName):
    """
    Mode to display a post more detailed, and interactive
    """
    #TODO

def markPost(userID, groupName, postSubject, postNumber, mark):
    """
    Marks a post as Read, Unread etc...based on 'r', 'u'
    Holy shit, super neg on the O(n) but that's okay, n*k very small.
    """
    global lock
    with lock:
        for d in groups:
            if d["name"] == groupName:
                with open(d["path"], "rw") as f:
                    subjects = json.loads(f.read())
                    for s in subjects:
                        if s["name"] == postSubject:
                            p = s["thread"][postNumber]
                            if p["postNumber"] == postNumber:
                                p["usersViewed"].append(userID)
                            else:
                                #error, postNumbers not aligned
                                res = responseBuilder("Error", "Post Numbers Not Aligned")
                                clientSocket.send(json.dumps(res))

def createPost(userID, postData):
    """
    Creates a post from user
    """
    #TODO

def delay(t):
    """
    Sleep for time t.
    """
    sleep(t)

def beginListening(serverSocket):
    """
    Listens for clients, spawns and sends client to new thread.
    """
    alert = "Server started listening on port " + PORT_NUMBER
    for c in alert:
        sys.stdout.write(colored(c, COLOR_IMPORTANT))
        delay(DELAY_PRINT)
    threadCount = 0
    while True:
        sys.stdout.write(colored("Waiting for clients...", COLOR_IMPORTANT))
        #accept client
        clientSocket, clientAddr = serverSocket.accept()
        newThread = clientHandler(str(threadCount), clientSocket, clientAddr)
        threadCount = threadCount + 1
        newThread.start()

def main():
    """
    Def Main
    """
    #preload group and client information
    loadGroups()
    loadClients()
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
