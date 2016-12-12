#!/usr/bin/env python
# discussionServer.py
"""
Python Discussion Application: Server
"""

from socket import *
from termcolor import colored  # for setting output color source: https://pypi.python.org/pypi/termcolor
from da_protocols import senddata, receivedata
import threading, sys, os, time, json, random


class ClientHandler(threading.Thread):
    """
    Handles new Client connections
    """
    def __init__(self, threadid, clientsocket, clientaddr, lock):
        threading.Thread.__init__(self)
        self.threadid = threadid
        self.clientsocket = clientsocket
        self.clientaddr = clientaddr
        self.lock = lock
        self.alive = True

    def stop(self):
        updateprint(("Client: " + str(self.clientaddr) + " disconnected\n"), COLOR_IMPORTANT)
        self.alive = False

    def run(self):
        global threadid
        global loggedin
        clientsocket = self.clientsocket
        clientaddr = self.clientaddr
        threadid = self.threadid
        lock = self.lock
        loggedin = False
        current_client = {}
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
                        userid = message["userID"]
                        loggedin, current_client = loginclient(clientsocket, userid, lock)
                        print("logged in")
                        print(str(current_client))
                    elif msgType == REQUEST_HELP:
                        res = helpmenu()
                        senddata(clientsocket, res, PACKET_LENGTH, END_PACKET)
                    elif msgType == REQUEST_LOGOUT:
                        loggedin = logoutclient(clientsocket, userid, current_client, lock)
                        loggedin = False
                        print("logged out")
                        print(str(current_client))
                        current_client = {}
                        updateclients()
                        delay(0.5)  # need delay to give the client time to receive transmission and close.
                    elif msgType == REQUEST_QUIT:
                        if loggedin:
                            loggedin = not logoutclient(clientsocket, userid, current_client, lock)
                        delay(0.5)  # need delay to give the client time to receive transmission and close.
                        self.stop()
                    elif loggedin:
                        if "N" not in message:
                            n = DEFAULT_N
                        else:
                            n = int(message["N"])
                        if msgType == REQUEST_AG:
                            # available mode
                            flag = enter_ag_mode(clientsocket, current_client, n, groups, lock)
                            if not flag:
                                loggedin = False
                                current_client = {}
                        elif msgType == REQUEST_SG:
                            # subscribe mode
                            enter_sg_mode(clientsocket, current_client, n, groups, lock)
                        elif msgType == REQUEST_RG:
                            # read mode
                            groupName = req["groupList"]
                            enter_rg_mode(clientsocket, current_client, groupName, lock)
                        else:
                            sys.stdout.write(colored(("Unsupported command: " + msgType + " by client " + userid + "\n")
                                                     , COLOR_ERROR))
                            sys.stdout.flush()
                            res = responsebuilder(threadid, "Error", ("Unsupported command: " + msgType + " by client "
                                                                      + userid))
                            senddata(clientsocket, res, PACKET_LENGTH, END_PACKET)
                    else:
                        sys.stdout.write(colored(("Unsupported command: " + msgType + " by client " + userid + "\n"),
                                                 COLOR_ERROR))
                        sys.stdout.flush()
                        res = responsebuilder(threadid, "Error", ("Unsupported command: " + msgType + " by client "
                                                                  + userid))
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
    print(str(response))
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


def loadgroups(lock):
    """
    Loads the groups on startup
    """
    # load groups & groups content
    typeprint("Populating discussion groups....\n", COLOR_TASK_START)
    with lock:
        with open(os.path.join(__location__, GROUPS_DATA_FILE), "r") as f:
            groupsdata = json.loads(f.read())
            groups = groupsdata["groups"]
        for g in groups:
            try:
                with open(os.path.join(__location__, GROUPS_PATH + g["path"])) as f:
                    temp_content = json.loads(f.read())
                    temp_group = {
                        "name": g["name"],
                        "content": temp_content
                    }
                    groupsContent.append(temp_group)
            except IOError as err:
                debugprint("no data file for " + g["name"] + "\n")
                continue
    typeprint(".......Discussion groups populated!!!\n", COLOR_TASK_FINISH)
    return groups, groupsContent


def loadclients(lock):
    """
    Loads the clients on startup from client file
    """
    global id_list
    # load clients
    typeprint("Populating client data....\n", COLOR_TASK_START)
    with lock:
        with open(os.path.join(__location__, CLIENT_DATA_FILE), "r") as f:
            clientdata = json.loads(f.read())
            clients = clientdata["clients"]
            id_list = []
            for user in clients:
                if user["id"] not in id_list:
                    id_list.append(user["id"])
                else:
                    print("Users with multiple IDs exist " + str(user["id"]))
    typeprint(".......Client data populated!!!\n", COLOR_TASK_FINISH)
    return clients


def createclient(clientID, lock):
    """
    Creates a default client and adds it to the list
    """
    global clients
    global id_list
    print("client_create")
    new_id = -1
    while True:
        new_id = random.randint(0000, 9999)  # generate a new ID for the user
        if new_id not in id_list:  # found a vacant ID
            break

    # Create the json addition
    addition = {}
    addition.update({"id": new_id})
    addition.update({"name": clientID})
    addition.update({"subscriptions": []})
    addition.update({"logged_flag": 0})
    print(addition)

    id_list.append(new_id)
    clients.append(addition)
    updateclients()
    return addition


def updateclients():
    """
    Updates the client data files
    """
    temp = CLIENT_FILE_STRUCT
    temp["clients"] = clients
    with open(os.path.join(__location__, CLIENT_DATA_FILE), "w") as f:
        json.dump(temp, f)


def loginclient(clientsocket, userid, lock):
    """
    Checks if the user is logged off & exits then logs them in
    """
    global clients
    with lock:
        clientdata = next((client for client in clients if client["id"] == userid), None)
        if clientdata is not None:
            clientdata["logged_flag"] = 1  # 1 = loggedin, 0 = loggedout

            # online_clients.append(clientdata)
            # offline_clients[:] = [client for client in offline_clients if client.get("id") != userid]
            res = responsebuilder(threadid, "Success", ("User ID: " + userid + " logged in successfully."))
            res.update({"client": clientdata})
            senddata(clientsocket, res, PACKET_LENGTH, END_PACKET)
            return True, clientdata
        else:
            # user doesn't exists
            #res = responsebuilder(threadid, "Error", ("User ID: " + userid + " does not exist."))
            #senddata(clientsocket, res, PACKET_LENGTH, END_PACKET)
           
            print("login area")
            
            clientdata = createclient(userid, lock)
            # We will create the user pool
            clientdata["logged_flag"] = 1
            res = responsebuilder(threadid, "Success", ("User ID: " + userid + " was created and logged in."))
            res.update({"client": clientdata})
            senddata(clientsocket, res, PACKET_LENGTH, END_PACKET)
            return True, clientdata


def logoutclient(clientsocket, userid, current_client, lock):
    """
    Checks if the user is logged in and logs them out
    """
    global clients
    if current_client == {}:
        res = responsebuilder(threadid, "Error", "No users logged in")
        senddata(clientsocket, res, PACKET_LENGTH, END_PACKET)
        return False
    with lock:
        # lientdata = next((client for client in online_clients if client["id"] == userid), None)
        # if clientdata is not None:
        for c in clients:
            if c["id"] == current_client["id"]:
                c["logged_flag"] = 0
                res = responsebuilder(threadid, "Success", ("User ID: " + userid + " logged out successfully."))
                senddata(clientsocket, res, PACKET_LENGTH, END_PACKET)
                return True

        else:
            # user doesn't exists
            res = responsebuilder(threadid, "Error", ("User ID: " + userid + " does not exist."))
            senddata(clientsocket, res, PACKET_LENGTH, END_PACKET)
            return False


def enter_ag_mode(clientsocket, current_client, msgcount, groups, lock):
    """
    Available Group Mode, Allows user to use special commands s, u, n, q
    """
    messagecount = 0
    res = {
        "type": "Success",
        "groupList": groups
    }
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
            # subscribe groups
            selections = message["selections"]
            subs = []
            for s in selections:
                if s not in current_client["subscriptions"]:
                    current_client["subscriptions"].append(s)
                    subs.append(s)
            updateclients()
            res = {
                "type": "Success",
                "body": ("Client " + str(current_client["id"]) + " subscribed to " + str(subs)),
                "clientdata": current_client
            }
            senddata(clientsocket, res, PACKET_LENGTH, END_PACKET)
        elif subcommand == SUB_U:
            # unsubscribed
            selections = message["selections"]
            subs = []
            for s in selections:
                current_client["subscriptions"].remove(s)
                subs.append(s)
            updateclients()
            res = {
                "type": "Success",
                "body": ("Client " + str(current_client["id"]) + " unsubscribed from " + str(subs)),
                "clientdata": current_client
            }
            senddata(clientsocket, res, PACKET_LENGTH, END_PACKET)
        elif subcommand == SUB_N:
            # lists next N groups
            res = {
                "type": "Success",
                "groupList": groups
            }
            senddata(clientsocket, res, PACKET_LENGTH, END_PACKET)
        elif subcommand == SUB_Q or subcommand == REQUEST_QUIT:
            # exits AG moder
            res = responsebuilder(threadid, "Success", "Exit AG Mode successfully.")
            senddata(clientsocket, res, PACKET_LENGTH, END_PACKET)
            debugprint("left ag mode")
            return True
        elif subcommand == REQUEST_LOGOUT:
            logoutclient(clientsocket, current_client["id"], current_client, lock)
            debugprint("logged out")
            print(str(current_client))
            current_client = {}
            delay(0.5)  # need delay to give the client time to receive transmission and close.
            return False
        else:
            # bad command
            res = responsebuilder(threadid, "Error", "Bad command. Please refer to help")
            senddata(clientsocket, res, PACKET_LENGTH, END_PACKET)


def enter_sg_mode(clientsocket, current_client, msgCount, groups, lock):
    """
    Subscribed Group Mode, Allows user to use special commands u, n, q
    """
    messageCount = 0
    res = {
        "type": "Success"
    }
    temp_list = []
    for g in groups:
        if g["name"] in current_client["subscriptions"]:
            temp_list.append(loadcurrentgroup(g["name"], lock))
    res.update({"groupList": temp_list})
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
            subs = []
            for s in selections:
                if s in current_client["subscriptions"]:
                    current_client["subscriptions"].remove(s)
                    subs.append(s)
            updateclients()
            res = {
                "type": "Success",
                "body": ("Client " + str(current_client["id"]) + " unsubscribed from " + str(subs)),
                "clientdata": current_client
                }
            senddata(clientsocket, res, PACKET_LENGTH, END_PACKET)
        elif subcommand == SUB_N:
            # lists next N groups
            res = {
                "type": "Success",
                "groupList": groups
            }
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


def enter_rg_mode(clientsocket, current_client, groupName, lock):
    """
    Read Group Mode, Allows user to use special commands [id], r, n, p, q
    """
    print(groupName)

    userid = current_client["id"]
    current_group = loadcurrentgroup(groupName, lock)
    # build initial posting response ie. posts 1-msgCount

    res = { "type": "Success", "groupData": current_group }
    senddata(clientsocket, res, PACKET_LENGTH, END_PACKET)

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
            markpostread(clientsocket, userid, current_group, postSubject, postNum, lock)
        elif subcommand == SUB_N:
            # lists next N posts in groupName
            # TODO this needs to confirm there arent new posts with the server...if no new posts, client handles it...if new posts, resend the post lists
            client_mod_time = message["last_modification_time"]
            if not isgroupcurrent(client_mod_time, groupName, lock):
                current_group = loadcurrentgroup(groupName, lock)
                res = {
                    "type": "Error",
                    "body": "Updated Data",
                    "group": current_group,
                    "groupList": groups
                }
                senddata(clientsocket, res, PACKET_LENGTH, END_PACKET)
            else:
                res = responsebuilder(threadid, "Success", "Data is current")
                senddata(clientsocket, res, PACKET_LENGTH, END_PACKET)
        elif subcommand == SUB_P:
            # makes a new post in groupName
            postData = message["body"]
            # createpost(userid, postData)
        elif subcommand == SUB_Q:
            # exits AG mode
            res = responsebuilder(threadid, "Success", "Exit RG Mode successfully.")
            senddata(clientsocket, res, PACKET_LENGTH, END_PACKET)
            return True
        else:
            # bad command
            res = responsebuilder(threadid, "Error", "Bad command. Please refer to help")
            senddata(clientsocket, res, PACKET_LENGTH, END_PACKET)


def markpostread(clientsocket, userid, current_group, postSubject, postNumber, lock):
    """
    Marks a post as Read, Unread etc...based on 'r', 'u'
    Holy shit, super neg on the O(n) but that's okay, n*k very small.
    """
    post_thread = None
    postNumber += 1  # Offset index
    with lock:
        cg = current_group["content"]
        for s in cg["subjects"]:
            if s["name"] == postSubject:
                post_thread = s["thread"]
                break
        if post_thread is not None:
            if userid not in post_thread[postNumber]["usersViewed"]:
                post_thread[postNumber]["usersViewed"].append(userid)
                update_groups_data(current_group)
                res = responsebuilder(threadid, "Success", "Post marked")
                senddata(clientsocket, res, PACKET_LENGTH, END_PACKET)
            else:
                # error, postNumbers not aligned
                res = responsebuilder("Error", "Post not found")
                senddata(clientsocket, res, PACKET_LENGTH, END_PACKET)


def createpost(clientsocket, current_client, current_group, postData, lock):
    """
    Creates a post from user
    """
    #TODO
    post_thread = None
    with lock:
        cg = current_group["content"]
        for s in cg["subjects"]:
            if s["name"] == postData["subject"]:
                post_thread = s["thread"]
                break
        if post_thread is not None:
            new_post = {}
            new_post.update({"postNumber": post_thread["postCount"]})
            new_post.update({"usersViewed": [current_client["id"]]})
            post_thread["postCount"] += 1
            for key, value in postData.items():
                new_post.update({key: value})
            post_thread["thread"].add(new_post)
            update_groups_data(current_group)
            res = responsebuilder(threadid, "Success", "Post created")
            senddata(clientsocket, res, PACKET_LENGTH, END_PACKET)
        else:
            #TODO: Add post creation for a new subject here
            res = responsebuilder(threadid, "Error", "Post could not be created, subject does not exist")
            senddata(clientsocket, res, PACKET_LENGTH, END_PACKET)

def update_groups_data(current_group):
    """
    Updates current group data structures
    """
    global group_data_dirty
    group_data_dirty = True
    temp_group = {}
    current_group["last_modified"] = get_time()
    for g in groups:
        if g["name"] == current_group["name"]:
            temp_group = g
    with open(os.path.join(__location__, GROUPS_PATH + temp_group["path"]), "w") as f:
        json.dump(current_group, f)


def isgroupcurrent(client_time, groupname, lock):
    """
    Checks if currentGroup data is up to date with groupName
    """
    cg_time = client_time
    with lock:
        for d in groupsContent:
            if d["name"] == groupname:
                if cg_time == d["last_modified"]:
                    return True
                else:
                    return False


def get_time():
    """
    Returns a string format of the current time
    """
    ret = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
    return ret


def loadcurrentgroup(groupName, lock):
    """
    Returns specific group data
    """
    ret = {}
    with lock:
        for d in groupsContent:
            if d["name"] == groupName:
                ret = d
    return ret


def loadauthors(path):
    """
    Loads author information from ../AUTHORS
    """
    typeprint("Loading Application Information...\n", COLOR_TASK_START)
    try:
        with open(path, "r") as f:
            authors = f.read().splitlines()
    except IOError as err:
        debugprint(str(err))
    typeprint("....Application Information Loaded!!\n", COLOR_TASK_FINISH)
    return authors


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


def beginlistening(serverSocket, lock):
    """
    Listens for clients, spawns and sends client to new thread.
    """
    typeprint(("Server started listening on port " + str(PORT_NUMBER) + "\n"), COLOR_IMPORTANT)
    threadCount = 0
    while True:
        sys.stdout.write(colored("Waiting for clients...\n", COLOR_IMPORTANT))
        sys.stdout.flush()
        # accept client
        clientsocket, clientaddr = serverSocket.accept()
        newThread = ClientHandler(str(threadCount), clientsocket, clientaddr, lock)
        threadCount += 1
        newThread.start()


def main():
    """
    Def Main
    """

    """
    Default APP info
    """
    global __location__
    global AUTHOR_FILE
    global authors
    AUTHOR_FILE = "../AUTHORS"

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
    global REQUEST_QUIT
    REQUEST_LOGIN = "login"
    REQUEST_LOGOUT = "logout"
    REQUEST_HELP = "help"
    REQUEST_AG = "ag"
    REQUEST_SG = "sg"
    REQUEST_RG = "rg"
    REQUEST_QUIT = "quit"

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
    global END_PACKET
    global DEFAULT_SEND_SIZE
    PACKET_LENGTH = 4096
    PORT_NUMBER = 9399
    END_PACKET = "/*/!/$/*"
    DEFAULT_SEND_SIZE = PACKET_LENGTH - len(END_PACKET)

    """
    Default Server Values
    """
    global CLIENT_DATA_FILE
    global GROUPS_PATH
    global GROUPS_DATA_FILE
    global DEFAULT_N
    global DELAY_PRINT
    global MAX_CLIENTS
    global CLIENT_FILE_STRUCT
    CLIENT_FILE_STRUCT = {
        "clients": []
    }
    global GROUP_FILE_STRUCT
    GROUP_FILE_STRUCT = {
        "total_posts": 0,
        "last_modified": "",
        "subjects": []
    }
    CLIENT_DATA_FILE = "clients/ids.json"
    GROUPS_PATH = "groups/"
    GROUPS_DATA_FILE = GROUPS_PATH + "groups.json"
    DEFAULT_N = 3
    DELAY_PRINT = 0.025
    MAX_CLIENTS = 50

    """
    Server data
    """
    global id_list
    global groups
    global groupsContent
    groupsContent = []
    mainlock = threading.Lock()
    global clients
    clients = []
    id_list = []
    groups = {}  # pull from groups directory, each subdir is a group with *.txt files for each thread

    """
    Dirty Flags
    """
    global group_data_dirty
    global client_data_dirty
    group_data_dirty = False
    group_client_dirty = False #TODO: track data changes in the code, to switch flag True, before data use check and fetch data.

    """
    Debug Stuff
    """
    global debugMode
    global COLOR_DEBUG
    debugMode = False
    COLOR_DEBUG = "red"

    print(get_time())
    # preload group and client information
    for s in sys.argv:
        if s == '-d':
            debugMode = True
            debugprint("DEBUG MODE ENABLED\nDebug messages will appear similar to this one.\n")
    typeprint("Launching Discussion Server...\n", 'yellow')
    __location__ = initlocation()
    authors = loadauthors(os.path.join(__location__, AUTHOR_FILE))
    groups, groupsContent = loadgroups(mainlock)
    debugprint(str(groups) + "\n")
    clients = loadclients(mainlock)
    server_socket = socket(AF_INET, SOCK_STREAM)
    server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    server_socket.bind(("", PORT_NUMBER))
    server_socket.listen(MAX_CLIENTS)
    beginlistening(server_socket, mainlock)
    # cleanup
    server_socket.close()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        raise SystemExit
