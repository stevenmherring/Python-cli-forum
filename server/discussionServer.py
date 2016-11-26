#!/usr/bin/env python
# discussionServer.py
"""
Python Discussion Application: Server
"""

from socket import *
from termcolor import colored # for setting output color source: https://pypi.python.org/pypi/termcolor
from da_protocols import senddata, receivedata
import threading, sys, os, time, json


class clientHandler(threading.Thread):
    """
    Handles new Client connections
    """
    def __init__(self, threadid, clientsocket, clientaddr):
        threading.Thread.__init__(self)
        self.threadid = threadid
        self.clientsocket = clientsocket
        self.clientaddr = clientaddr
        self.alive = True

    def stop(self):
        updateprint(("Client: " + str(self.clientaddr) + " disconnected\n"), COLOR_IMPORTANT)
        self.alive = False

    def run(self):
        clientsocket = self.clientsocket
        clientaddr = self.clientaddr
        threadid = self.threadid
        loggedin = False
        global loggedin
        updateprint((".....New Client Connected: " + str(clientaddr) + "\n"), COLOR_OUTGOING)
        userid = ""
        try:
            while self.alive:
                try:
                    req = receivedata(clientsocket, PACKET_LENGTH, END_PACKET)
                    print("REQ: " + str(req) + "\n")
                    message = req
                    msgType = message["type"].lower()
                    if not loggedin and msgType == REQUEST_LOGIN:
                        userid = message["userid"]
                        loginclient(clientsocket, userid, offline_clients, online_clients, loggedin)
                    elif msgType == REQUEST_HELP:
                        res = helpmenu()
                        res = str.encode(json.dumps(res))
                        senddata(clientsocket, res, PACKET_LENGTH, END_PACKET)
                    elif msgType == REQUEST_LOGOUT:
                        logoutclient(clientsocket, userid, offline_clients, online_clients, loggedin)
                        delay(0.5) # need delay to give the client time to receive transmission and close.
                        self.stop()
                    elif msgType == REQUEST_QUIT:
                        if loggedin:
                            logoutclient(clientsocket, userid, offline_clients, online_clients, loggedin)
                        delay(0.5) # need delay to give the client time to receive transmission and close.
                        self.stop()
                    elif loggedin:
                        if message["N"] is None:
                            n = DEFAULT_N
                        else:
                            n = int(message["N"])
                        if msgType == REQUEST_AG:
                            # available mode
                            enter_ag_mode(clientsocket, userid, n)
                        elif msgType == REQUEST_SG:
                            # subscribe mode
                            enter_sg_mode(clientsocket, userid, n)
                        elif msgType == REQUEST_RG:
                            # read mode
                            enter_rg_mode(clientsocket, userid, n)
                        else:
                            sys.stdout.write(colored(("Unsupported command: " + msgType + " by client " + userid + "\n"), COLOR_ERROR))
                            sys.stdout.flush()
                            res = responsebuilder(threadid, "Error", ("Unsupported command: " + msgType + " by client " + userid))
                            senddata(clientsocket, res, PACKET_LENGTH, END_PACKET)
                    else:
                        sys.stdout.write(colored(("Unsupported command: " + msgType + " by client " + userid + "\n"), COLOR_ERROR))
                        sys.stdout.flush()
                        res = responsebuilder(threadid, "Error", ("Unsupported command: " + msgType + " by client " + userid))
                        senddata(clientsocket, res, PACKET_LENGTH, END_PACKET)

                except IOError as err:
                    sys.stdout.write(colored(err, COLOR_ERROR))
                    sys.stdout.flush()
                    res = {
                        "type": "Error",
                        "body": IO_ERROR
                    }
                    senddata(clientsocket, res, PACKET_LENGTH, END_PACKET)
        finally:
            clientsocket.close()


def responsebuilder(threadid, mtype, body):
    """
    Build and returns a json style response as basic protocol. Message Type and its body
    """
    response = {
        "type": mtype,
        "body": body
    }
    sys.stdout.write(colored(("Thread: " + threadid + json.dumps(response) + "\n"), COLOR_OUTGOING))
    sys.stdout.flush()
    return response


def helpmenu():
    """
    Returns json style help menu
    """
    usage = "310 Discussion Application\nDeveloped by: "
    for a in authors:
        usage = (usage + a + ", ")
    usage = usage[:-2] + """\nServer supported commands
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


def typeprint(message, color):
    """
    Typed out 'loading' style print w/ color
    """
    for c in message:
        delay(DELAY_PRINT)
        sys.stdout.write(colored(c, color))
        sys.stdout.flush()


def updateprint(message, color):
    """
    Quick print w/ color
    """
    sys.stdout.write(colored(message, color))
    sys.stdout.flush()


def debugprint(message):
    """
    Debug messaging function, only prints if debug mode is enabled
    """
    if debugMode:
        sys.stdout.write(colored(message, COLOR_DEBUG, None, ['underline']))
        sys.stdout.flush()


def loadgroups():
    """
    Loads the groups on startup
    """
    global groups
    global lock
    #l oad groups
    typeprint("Populating discussion groups....\n", COLOR_TASK_START)
    with lock:
        with open(os.path.join(__location__, GROUPS_DATA_FILE), "r") as f:
            groupsData = json.loads(f.read())
            groups = groupsData["groups"]
    typeprint(".......Discussion groups populated!!!\n", COLOR_TASK_FINISH)


def loadclients():
    """
    Loads the clients on startup from client file
    """
    global offline_clients
    global lock
    # load clients
    typeprint("Populating client data....\n", COLOR_TASK_START)
    with lock:
        with open(os.path.join(__location__, CLIENT_DATA_FILE), "r") as f:
            clientdata = json.loads(f.read())
            offline_clients = clientdata["clients"]
    typeprint(".......Client data populated!!!\n", COLOR_TASK_FINISH)


def loginclient(clientsocket, userid, offline_clients, online_clients, loggedin):
    """
    Checks if the user is logged off & exits then logs them in
    """
    global lock
    with lock:
        clientdata = next((client for client in offline_clients if client["id"] == userid), None)
        if clientdata != None:
            online_clients.append(clientdata)
            offline_clients[:] = [client for client in offline_clients if client.get("id") != userid]
            loggedin = True
            res = responsebuilder(threadid, "Success", ("User ID: " + userid + " logged in successfully."))
            senddata(clientsocket, res, PACKET_LENGTH, END_PACKET)
            return True
        else:
            # user doesn't exists
            res = responsebuilder(threadid, "Error", ("User ID: " + userid + " does not exist."))
            senddata(clientsocket, res, PACKET_LENGTH, END_PACKET)
            return False


def logoutclient(clientsocket, userid, offline_clients, online_clients, loggedin):
    """
    Checks if the user is logged in and logs them out
    """
    global lock

    with lock:
        clientdata = next((client for client in online_clients if client["id"] == userid), None)
        if clientdata != None:
            offline_clients.append(clientdata)
            online_clients[:] = [client for client in online_clients if client.get("id") != userid]
            loggedin = False
            res = responsebuilder(threadid, "Success", ("User ID: " + userid + " logged out successfully."))
            senddata(clientsocket, res, PACKET_LENGTH, END_PACKET)
            return True
        else:
            #user doesn't exists
            res = responsebuilder(threadid, "Error", ("User ID: " + userid + " does not exist."))
            senddata(clientsocket, res, PACKET_LENGTH, END_PACKET)
            return False


def enter_ag_mode(clientsocket, userid, msgcount):
    """
    Available Group Mode, Allows user to use special commands s, u, n, q
    """
    global groups
    messagecount = 0
    res = {
        "type": "Success",
        "groupList": []
    }
    if (messagecount + msgcount) > len(groups):
        maxrange = len(groups)
    else:
        maxrange = messagecount + msgcount
    for i in range(messagecount, maxrange):
        with lock:
            res[groupList].add(groups[i])
    senddata(clientsocket, res, PACKET_LENGTH, END_PACKET)
    while True:
        message = receivedata(clientsocket, PACKET_LENGTH, END_PACKET)
        msgtype = message["type"].lower()
        if msgtype != REQUEST_AG:
            res = responsebuilder(threadid, "Error", "Wrong mode type, in AG requesting " + msgtype)
            senddata(clientsocket, res, PACKET_LENGTH, END_PACKET)
            return False
        subcommand = message["subcommand"].lower()
        if subcommand == SUB_S:
            #subscribe groups
            selections = message["selections"]
            for s in selections:
                if s not in clients[userid]["subscriptions"]:
                    clients[userid]["subscriptions"].append(s)
        elif subcommand == SUB_U:
            #unsubscribed
            selections = message["selections"]
            for s in selections:
                if s in clients[userid]["subscriptions"]:
                    clients[userid]["subscriptions"].remove(s)
        elif subcommand == SUB_N:
            #lists next N groups
            msgcount = int(message["N"])
            res = {
                "type": "Success",
                "groupList": []
            }
            if (messagecount + msgcount) > len(groups):
                maxrange = len(groups)
            else:
                maxrange = messagecount + msgcount
            for i in range(messagecount, maxrange):
                with lock:
                    res[groupList].add(groups[i])
            senddata(clientsocket, res, PACKET_LENGTH, END_PACKET)
        elif subcommand == SUB_Q:
            # exits AG moder
            res = responsebuilder(threadid, "Success", "Exit AG Mode successfully.")
            senddata(clientsocket, res, PACKET_LENGTH, END_PACKET)
            return True
        else:
            # bad command
            res = responsebuilder(threadid, "Error", "Bad command. Please refer to help")
            senddata(clientsocket, res, PACKET_LENGTH, END_PACKET)


def enter_sg_mode(clientsocket, userid, msgCount):
    """
    Subscribed Group Mode, Allows user to use special commands u, n, q
    """
    global groups
    global groupList
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
    senddata(clientsocket, res, PACKET_LENGTH, END_PACKET)
    while True:
        message = receivedata(clientsocket, PACKET_LENGTH, END_PACKET)
        msgType = message["type"].lower()
        if msgType != REQUEST_SG:
            res = responsebuilder(threadid, "Error", "Wrong mode type, in SG requesting " + msgType)
            senddata(clientsocket, res, PACKET_LENGTH, END_PACKET)
            return False
        subcommand = message["subcommand"].lower()
        if subcommand == SUB_U:
            # unsubscribed
            selections = message["selections"]
            for s in selections:
                if s in clients[userid]["subscriptions"]:
                    clients[userid]["subscriptions"].remove(s)
        elif subcommand == SUB_N:
            # lists next N groups
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
            senddata(clientsocket, res, PACKET_LENGTH, END_PACKET)
        elif subcommand == SUB_Q:
            # exits AG moder
            res = responsebuilder(threadid, "Success", "Exit SG Mode successfully.")
            senddata(clientsocket, res, PACKET_LENGTH, END_PACKET)
            return True
        else:
            # bad command
            res = responsebuilder(threadid, "Error", "Bad command. Please refer to help")
            senddata(clientsocket, res, PACKET_LENGTH, END_PACKET)


def enter_rg_mode(clientsocket, userid, msgCount, groupName):
    """
    Read Group Mode, Allows user to use special commands [id], r, n, p, q
    """
    global groups
    currentGroup = loadcurrentgroup(groupName)
    # build initial posting response ie. posts 1-msgCount
    while True:
        message = receivedata(clientsocket, PACKET_LENGTH, END_PACKET)
        msgType = message["type"].lower()
        if msgType != REQUEST_RG:
            res = responsebuilder(threadid, "Error", "Wrong mode type, in RG requesting " + msgType)
            senddata(clientsocket, res, PACKET_LENGTH, END_PACKET)
            return False
        subcommand = message["subcommand"].lower()
        if subcommand == SUB_ID:
            # enter read post mode - this can be handled completely by the client side
            res = responsebuilder(threadid, "Error", "Client should store and handle the data read post mode, no need for server comm.")
            senddata(clientsocket, res, PACKET_LENGTH, END_PACKET)
        elif subcommand == SUB_R:
            # mark post read
            postSubject = message["postSubject"]
            postNum = message["postNumber"]
            markpost(clientsocket, userid, groupName, postSubject, postNum, "r")
        elif subcommand == SUB_N:
            # lists next N posts in groupName
            # TODO this needs to confirm there arent new posts with the server...if no new posts, client handles it...if new posts, resend the post lists
            if not isgroupcurrent(currentGroup, groupName):
                currentGroup = loadcurrentgroup
                res = {
                    "type": "Error",
                    "body": "Updated Data",
                    "thread": currentGroup
                }
                senddata(clientsocket, res, PACKET_LENGTH, END_PACKET)
            else:
                res = responsebuilder(threadid, "Success", "Data is current")
                senddata(clientsocket, res, PACKET_LENGTH, END_PACKET)
        elif subcommand == SUB_P:
            # makes a new post in groupName
            postData = message["body"]
            createpost(userid, postData)
        elif subcommand == SUB_Q:
            # exits AG mode
            res = responsebuilder(threadid, "Success", "Exit RG Mode successfully.")
            senddata(clientsocket, res, PACKET_LENGTH, END_PACKET)
            return True
        else:
            # bad command
            res = responsebuilder(threadid, "Error", "Bad command. Please refer to help")
            senddata(clientsocket, res, PACKET_LENGTH, END_PACKET)


def markpost(clientsocket, userid, groupName, postSubject, postNumber, mark):
    """
    Marks a post as Read, Unread etc...based on 'r', 'u'
    Holy shit, super neg on the O(n) but that's okay, n*k very small.
    """
    global lock
    with lock:
        for d in groups:
            if d["name"] == groupName:
                with open(os.path.join(__location__, d["path"]), "rw") as f:
                    subjects = json.loads(f.read())
                    for s in subjects:
                        if s["name"] == postSubject:
                            p = s["thread"][postNumber]
                            if p["postNumber"] == postNumber:
                                p["usersViewed"].append(userid)
                                res = responsebuilder(threadid, "Success", "Post marked")
                                senddata(clientsocket, res, PACKET_LENGTH, END_PACKET)
                            else:
                                # error, postNumbers not aligned
                                res = responsebuilder("Error", "Post Numbers Not Aligned")
                                senddata(clientsocket, res, PACKET_LENGTH, END_PACKET)


def createpost(userid, groupName, postData):
    """
    Creates a post from user
    """
    #TODO
    global groups
    for d in groups:
        if d["name"] == groupName:
            with open(os.path.join(__location__, d["path"]), "rw") as f:
                subjects = json.loads(f.read())


def isgroupcurrent(currentGroup, groupName):
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


def loadcurrentgroup(groupName):
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


def loadauthors():
    """
    Loads author information from ../AUTHORS
    """
    global authors
    typeprint("Loading Application Information...\n", COLOR_TASK_START)
    try:
        with open(os.path.join(__location__, AUTHOR_FILE), "r") as f:
            authors = f.read().splitlines()
    except IOError as err:
        debugprint(str(err))
    typeprint("....Application Information Loaded!!\n", COLOR_TASK_FINISH)


def initlocation():
    """
    Initialize and return CWD of the process, so we can reliably open files we know should exist
    """
    ret = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))
    return ret


def delay(t):
    """
    Sleep for time t.
    """
    time.sleep(t)


def beginlistening(serverSocket):
    """
    Listens for clients, spawns and sends client to new thread.
    """
    typeprint(("Server started listening on port " + str(PORT_NUMBER) + "\n"), COLOR_IMPORTANT)
    threadCount = 0
    while True:
        sys.stdout.write(colored("Waiting for clients...\n", COLOR_IMPORTANT))
        sys.stdout.flush()
        #accept client
        clientsocket, clientaddr = serverSocket.accept()
        newThread = clientHandler(str(threadCount), clientsocket, clientaddr)
        threadCount = threadCount + 1
        newThread.start()


def main():
    """
    Def Main
    """

    """
    Default APP info
    """
    AUTHOR_FILE = "../AUTHORS"
    global AUTHOR_FILE

    """
    String Messages
    """
    IO_ERROR = "IO Error, terminating connection.\n"
    global IO_ERROR

    """
    Color definitions
    """
    COLOR_ERROR = "red"
    COLOR_IMPORTANT = "cyan"
    COLOR_OUTGOING = "magenta"
    COLOR_TASK_START = "blue"
    COLOR_TASK_FINISH = "white"
    global COLOR_ERROR
    global COLOR_IMPORTANT
    global COLOR_OUTGOING
    global COLOR_TASK_START
    global COLOR_TASK_FINISH

    """
    Client commands
    """
    REQUEST_LOGIN = "login"
    REQUEST_LOGOUT = "logout"
    REQUEST_HELP = "help"
    REQUEST_AG = "ag"
    REQUEST_SG = "sg"
    REQUEST_RG = "rg"
    REQUEST_QUIT = "quit"
    global REQUEST_LOGIN
    global REQUEST_AG
    global REQUEST_HELP
    global REQUEST_LOGOUT
    global REQUEST_SG
    global REQUEST_RG
    global REQUEST_QUIT

    SUB_S = "s"
    SUB_U = "u"
    SUB_N = "n"
    SUB_Q = "q"
    SUB_ID = "id"
    SUB_R = "r"
    SUB_P = "p"
    global SUB_S
    global SUB_U
    global SUB_N
    global SUB_Q
    global SUB_ID
    global SUB_R
    global SUB_P

    """
    Socket Information
    """
    PACKET_LENGTH = 4096
    PORT_NUMBER = 9390
    END_PACKET = "/*/!/$/*"
    DEFAULT_SEND_SIZE = PACKET_LENGTH - len(END_PACKET)
    global PACKET_LENGTH
    global PORT_NUMBER
    global END_PACKET
    global DEFAULT_SEND_SIZE

    """
    Default Server Values
    """
    CLIENT_DATA_FILE = "clients/ids.json"
    GROUPS_PATH = "groups/"
    GROUPS_DATA_FILE = GROUPS_PATH + "groups.json"
    DEFAULT_N = 3
    DELAY_PRINT = 0.025
    MAX_CLIENTS = 50
    global CLIENT_DATA_FILE
    global GROUPS_PATH
    global GROUPS_DATA_FILE
    global DEFAULT_N
    global DELAY_PRINT
    global MAX_CLIENTS

    """
    Server data
    """
    lock = threading.Lock()
    offline_clients = []
    online_clients = []
    groups = {} # pull from groups directory, each subdir is a group with *.txt files for each thread
    global lock
    global offline_clients
    global online_clients
    global groups

    """
    Debug Stuff
    """
    debugMode = False
    COLOR_DEBUG = "red"
    global debugMode
    global COLOR_DEBUG

    # preload group and client information
    for s in sys.argv:
        if s == '-d':
            debugMode = True
            debugprint("DEBUG MODE ENABLED\nDebug messages will appear similar to this one.\n")
    typeprint("Launching Discussion Server...\n", 'yellow')
    __location__ = initlocation()
    global __location__
    loadauthors()
    loadgroups()
    debugprint(str(groups) + "\n")
    loadclients()
    debugprint(str(offline_clients) + "\n")
    serverSocket = socket(AF_INET, SOCK_STREAM)
    serverSocket.bind(("", PORT_NUMBER))
    serverSocket.listen(MAX_CLIENTS)
    beginlistening(serverSocket)
    # cleanup
    serverSocket.close()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        raise SystemExit
