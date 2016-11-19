#!/usr/bin/env python
# discussionServer.py
"""
Python Discussion Application: Server
"""

from socket import *
from termcolor import colored #for setting output color source: https://pypi.python.org/pypi/termcolor
import threading, sys, os, time, json

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
        clientSocket = self.clientSocket
        clientAddr = self.clientAddr
        updatePrint((".....New Client Connected: " + str(clientAddr) + "\n"), COLOR_OUTGOING)
        #mark dirty on data change, !dirty on data retrieval
        dirty = False
        loggedIn = False
        userID = ""
        while True:
            try:
                req = bytes.decode((clientSocket.recv(PACKET_LENGTH)))
                message = json.loads(req)
                msgType = message["type"].lower()
                if not loggedIn and msgType == REQUEST_LOGIN:
                    userID = message["arg1"]
                    loginClient(clientSocket, userID, offline_clients, online_clients, loggedIn)
                elif msgType == REQUEST_HELP:
                    res = helpMenu()
                    clientSocket.send(str.encode(json.dumps(res)))
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
                        sys.stdout.flush()
                        res = responseBuilder("Error", ("Unsupported command: " + msgType + " by client " + userID))
                        clientSocket.send(str.encode(json.dumps(res)))
                else:
                    sys.stdout.write(colored(("Unsupported command: " + msgType + " by client " + userID), COLOR_ERROR))
                    sys.stdout.flush()
                    res = responseBuilder("Error", ("Unsupported command: " + msgType + " by client " + userID))
                    clientSocket.send(str.encode(json.dumps(res)))

            except IOError as err:
                sys.stdout.write(colored(err, COLOR_ERROR))
                sys.stdout.flush()
                res = {
                    "type": "Error",
                    "body": IO_ERROR
                }
                clientSocket.send(str.encode(json.dumps(res)))
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
    sys.stdout.flush()
    sys.stdout.write(colored(("Thread: " + threadID + json.dumps(response)), COLOR_OUTGOING))
    sys.stdout.flush()
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

def typePrint(message, color):
    """
    Typed out 'loading' style print w/ color
    """
    for c in message:
        delay(DELAY_PRINT)
        sys.stdout.write(colored(c, color))
        sys.stdout.flush()

def updatePrint(message, color):
    """
    Quick print w/ color
    """
    sys.stdout.write(colored(message, color))
    sys.stdout.flush()

def trimBytesToString(bytes):
    """
    Takes a bytes object, returns a string version without the b' ' prologue/epilogue
    """
    return str(bytes)[2:-1]


def loadGroups():
    """
    Loads the groups on startup
    """
    global groups
    global lock
    #load groups
    typePrint("Populating discussion groups....\n", COLOR_TASK_START)
    with lock:
        with open(GROUPS_DATA_FILE, "r") as f:
            groupsData = json.loads(f.read())
            groups = groupsData["groups"]
    typePrint(".......Discussion groups populated!!!\n", COLOR_TASK_FINISH)

def loadClients():
    """
    Loads the clients on startup from client file
    """
    global offline_clients
    global lock
    #load clients
    typePrint("Populating client data....\n", COLOR_TASK_START)
    with lock:
        with open(CLIENT_DATA_FILE, "r") as f:
            clientData = json.loads(f.read())
            offline_clients = clientData["clients"]
    typePrint(".......Client data populated!!!\n", COLOR_TASK_FINISH)

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
            clientSocket.send(str.encode(json.dumps(res)))
            return True
        else:
            #user doesn't exists
            res = responseBuilder("Error", ("User ID: " + userID + " does not exist."))
            clientSocket.send(str.encode(json.dumps(res)))
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
            clientSocket.send(str.encode(json.dumps(res)))
            return True
        else:
            #user doesn't exists
            res = responseBuilder("Error", ("User ID: " + userID + " does not exist."))
            clientSocket.send(str.encode(json.dumps(res)))
            return False

def enterAG(clientSocket, userID, msgCount):
    """
    Available Group Mode, Allows user to use special commands s, u, n, q
    """
    global groups
    messageCount = 0
    res = {
        "type": "Success",
        "groupList": []
    }
    if (messageCount + msgCount) > len(groups):
        maxRange = len(groups)
    else:
        maxRange = messageCount + msgCount
    for i in range(messageCount, maxRange):
        with lock:
            res[groupList].add(groups[i])
    clientSocket.send(str.encode(json.dumps(res)))
    while True:
        res = {}
        req = bytes.decode(clientSocket.recv(PACKET_LENGTH))
        message = json.loads(req)
        msgType = message["type"].lower()
        if msgType != REQUEST_AG:
            res = responseBuilder("Error", "Wrong mode type, in AG requesting " + msgType)
            clientSocket.send(str.encode(json.dumps(res)))
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
                "type": "Success",
                "groupList": []
            }
            if (messageCount + msgCount) > len(groups):
                maxRange = len(groups)
            else:
                maxRange = messageCount + msgCount
            for i in range(messageCount, maxRange):
                with lock:
                    res[groupList].add(groups[i])
            clientSocket.send(str.encode(json.dumps(res)))
        elif subcommand == SUB_Q:
            #exits AG moder
            res = responseBuilder("Success", "Exit AG Mode successfully.")
            clientSocket.send(str.encode(json.dumps(res)))
            return True
        else:
            #bad command
            res = responseBuilder("Error", "Bad command. Please refer to help")
            clientSocket.send(str.encode(json.dumps(res)))

def enterSG(clientSocket, userID, msgCount):
    """
    Subscribed Group Mode, Allows user to use special commands u, n, q
    """
    global groups
    messageCount = 0
    res = {
        "type": "Success",
        "groupList": []
    }
    if (messageCount + msgCount) > len(groups):
        maxRange = len(groups)
    else:
        maxRange = messageCount + msgCount
    for i in range(messageCount, maxRange):
        with lock:
            res[groupList].add(groups[i])
    clientSocket.send(str.encode(json.dumps(res)))
    while True:
        res = {}
        req = bytes.decode(clientSocket.recv(PACKET_LENGTH))
        message = json.loads(req)
        msgType = message["type"].lower()
        if msgType != REQUEST_SG:
            res = responseBuilder("Error", "Wrong mode type, in SG requesting " + msgType)
            clientSocket.send(str.encode(json.dumps(res)))
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
                "type": "Success",
                "groupList": []
            }
            if (messageCount + msgCount) > len(groups):
                maxRange = len(groups)
            else:
                maxRange = messageCount + msgCount
            for i in range(messageCount, maxRange):
                with lock:
                    res[groupList].add(groups[i])
            clientSocket.send(str.encode(json.dumps(res)))
        elif subcommand == SUB_Q:
            #exits AG moder
            res = responseBuilder("Success", "Exit SG Mode successfully.")
            clientSocket.send(str.encode(json.dumps(res)))
            return True
        else:
            #bad command
            res = responseBuilder("Error", "Bad command. Please refer to help")
            clientSocket.send(str.encode(json.dumps(res)))

def enterRG(clientSocket, userID, msgCount, groupName):
    """
    Read Group Mode, Allows user to use special commands [id], r, n, p, q
    """
    global groups
    messageCount = 0
    res = {}
    currentGroup = {}
    currentGroup = loadCurrentGroup(groupName)
    #build initial posting response ie. posts 1-msgCount
    while True:
        res = {}
        req = bytes.decode(clientSocket.recv(PACKET_LENGTH))
        message = json.loads(req)
        msgType = message["type"].lower()
        if msgType != REQUEST_RG:
            res = responseBuilder("Error", "Wrong mode type, in RG requesting " + msgType)
            clientSocket.send(str.encode(json.dumps(res)))
            return False
        subcommand = message["subcommand"].lower()
        if subcommand == SUB_ID:
            #enter read post mode - this can be handled completely by the client side
            res = responseBuilder("Error", "Client should store and handle the data read post mode, no need for server comm.")
            clientSocket.send(str.encode(json.dumps(res)))
        elif subcommand == SUB_R:
            #mark post read
            postSubject = message["postSubject"]
            postNum = message["postNumber"]
            markPost(userID, groupName, postSubject, postNum, "r")
        elif subcommand == SUB_N:
            #lists next N posts in groupName
            #TODO this needs to confirm there arent new posts with the server...if no new posts, client handles it...if new posts, resend the post lists
            if not isGroupCurrent(currentGroup, groupName):
                currentGroup = loadCurrentGroup
                res = {
                    "type": "Error",
                    "body": "Updated Data",
                    "thread": currentGroup
                }
                clientSocket.send(str.encode(json.dumps(res)))
            else:
                res = responseBuilder("Success", "Data is current")
                clientSocket.send(str.encode(json.dumps(res)))
        elif subcommand == SUB_P:
            #makes a new post in groupName
            postData = message["body"]
            createPost(userID, postData)
        elif subcommand == SUB_Q:
            #exits AG mode
            res = responseBuilder("Success", "Exit RG Mode successfully.")
            clientSocket.send(str.encode(json.dumps(res)))
            return True
        else:
            #bad command
            res = responseBuilder("Error", "Bad command. Please refer to help")
            clientSocket.send(str.encode(json.dumps(res)))

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
                                res = responseBuilder("Success", "Post marked")
                                clientSocket.send(str.encode(json.dumps(res)))
                            else:
                                #error, postNumbers not aligned
                                res = responseBuilder("Error", "Post Numbers Not Aligned")
                                clientSocket.send(str.encode(json.dumps(res)))

def createPost(userID, groupName, postData):
    """
    Creates a post from user
    """
    #TODO
    global groups
    for d in groups:
        if d["name"] == groupName:
            with open(d["path"], "rw") as f:
                subjects = json.loads(f.read())


def isGroupCurrent(currentGroup, groupName):
    """
    Checks if currentGroup data is up to date with groupName
    """
    global lock
    cgTime = currentGroup["last_modified"]
    with lock:
        for d in groups:
            if d["name"] == groupName:
                if cgTime == d["last_modified"]:
                    return True
                else:
                    return False

def loadCurrentGroup(groupName):
    """
    Returns specific group data
    """
    global lock
    ret = {}
    with lock:
        for d in groups:
            if d["name"] == groupName:
                ret = d
    return ret

def delay(t):
    """
    Sleep for time t.
    """
    time.sleep(t)

def beginListening(serverSocket):
    """
    Listens for clients, spawns and sends client to new thread.
    """
    typePrint(("Server started listening on port " + str(PORT_NUMBER) + "\n"), COLOR_IMPORTANT)
    threadCount = 0
    while True:
        sys.stdout.write(colored("Waiting for clients...\n", COLOR_IMPORTANT))
        sys.stdout.flush()
        #accept client
        clientSocket, clientAddr = serverSocket.accept()
        newThread = clientHandler(str(threadCount), clientSocket, clientAddr)
        threadCount = threadCount + 1
        newThread.start()

def main():
    """
    Def Main
    """
    """
    String Messages
    """
    global IO_ERROR
    IO_ERROR = "IO Error, terminating connection.\n"

    """
    Color definitions
    """
    global COLOR_ERROR
    global COLOR_IMPORTANT
    global COLOR_OUTGOING
    global COLOR_TASK_START
    global COLOR_TASK_FINISH
    COLOR_ERROR = "red"
    COLOR_IMPORTANT = "cyan"
    COLOR_OUTGOING = "magenta"
    COLOR_TASK_START = "blue"
    COLOR_TASK_FINISH = "white"

    """
    Client commands
    """
    global REQUEST_LOGIN
    global REQUEST_AG
    global REQUEST_HELP
    global REQUEST_LOGOUT
    global REQUEST_SG
    global REQUEST_RG
    REQUEST_LOGIN = "login"
    REQUEST_LOGOUT = "logout"
    REQUEST_HELP = "help"
    REQUEST_AG = "ag"
    REQUEST_SG = "sg"
    REQUEST_RG = "rg"
    global SUB_S
    global SUB_U
    global SUB_N
    global SUB_Q
    global SUB_ID
    global SUB_R
    global SUB_P
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
    global PACKET_LENGTH
    global PORT_NUMBER
    PACKET_LENGTH = 4096
    PORT_NUMBER = 9390

    """
    Default Server Values
    """
    global CLIENT_DATA_FILE
    global GROUPS_PATH
    global GROUPS_DATA_FILE
    global DEFAULT_N
    global DELAY_PRINT
    global MAX_CLIENTS
    CLIENT_DATA_FILE = "clients/ids.json"
    GROUPS_PATH = "groups/"
    GROUPS_DATA_FILE = GROUPS_PATH + "groups.json"
    DEFAULT_N = 3
    DELAY_PRINT = 0.025
    MAX_CLIENTS = 50

    """
    Server data
    """
    global lock
    global offline_clients
    global online_clients
    global groups
    lock = threading.Lock()
    offline_clients = []
    online_clients = []
    groups = {} #pull from groups directory, each subdir is a group with *.txt files for each thread
    #preload group and client information
    typePrint("Launching Discussion Server...\n", 'yellow')
    loadGroups()
    loadClients()
    serverSocket = socket(AF_INET, SOCK_STREAM)
    serverSocket.bind(("", PORT_NUMBER))
    serverSocket.listen(MAX_CLIENTS)
    beginListening(serverSocket)
    #cleanup
    serverSocket.close()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        raise SystemExit
