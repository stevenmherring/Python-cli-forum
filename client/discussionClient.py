from datetime import datetime
from socket import *
from termcolor import colored
from da_protocols import senddata, receivedata
import sys, os, json, time, operator
import re


def loadvalue   (usr_id):
    tmp = False
    with open("data.txt", "r") as file_read:
        load = json.loads(file_read.read())
        val = load["client"]
        for a in val :
            if( a["usr"] == usr_id):
                tmp = True
                break
    if(tmp is False):
        val.append({"usr":usr_id, "data":{}})    
    
    return load


def updatecheck (usr_id, group):
    val = loadvalue(usr_id)
    with open("data.txt", "w") as f:
        #Start by iterating over all instances in val for the correct username
        for i in val["client"]:
            if(i["usr"] == usr_id):
                #print (group)
                if(group["name"] not in i["data"]):
                    i["data"].update(
                        {group["name"]:{"total_posts":group["total_posts"], "subs":{}}}
                    )
                i["data"][group["name"]]["total_posts"] = group["total_posts"]
        json.dump(val, f)
    return


def updatevalue (usr_id, group, subject):
    createvalue(usr_id, group, subject)

    val = loadvalue(usr_id)
    with open("data.txt", "w") as f:
        #Start by iterating over all instances in val for the correct username
        for i in val["client"]:
            if(i["usr"] == usr_id):
                #print (group)
                if(group["name"] not in i["data"]):
                    i["data"].update(
                        {group["name"]:{"total_posts":group["content"]["total_posts"], "subs":{}}}
                    )
                i["data"][group["name"]]["subs"][subject["name"]] += 1
        json.dump(val, f)
    return

def createvalue (usr_id, group, subject):
    val = loadvalue(usr_id)
    with open("data.txt", "w") as f:
        #Start by iterating over all instances in val for the correct username
        for i in val["client"]:
            if(i["usr"] == usr_id):
                #print (group)
                if(group["name"] not in i["data"]):
                    i["data"].update(
                        {group["name"]:{"total_posts":group["content"]["total_posts"], "subs":{}}}
                    )
                if(subject["name"] not in i["data"][group["name"]]["subs"]):
                    i["data"][group["name"]]["subs"].update({subject["name"]:0})
        json.dump(val, f)
    return


def check_new (group, current_subject, usr_id):
    group_name = group["name"]
    val = loadvalue(usr_id)
    found = False
    for i in val["client"]:
        if(i["usr"] == usr_id):
            print(i)
            if("subs" in i["data"][group_name]):
                print(current_subject["name"])
                if(current_subject["name"] in i["data"][group_name]["subs"]):
                    if(i["data"][group_name]["subs"][current_subject["name"]] == current_subject["postCount"]):
                        return False
            else:
                createvalue(usr_id, group, current_subject)
    return True        
                            

def printread (N_VALUE, N_TICK, CURRENT_READ, usr_id):
    read = CURRENT_READ["subjects"]
    loadposts(CURRENT_READ, usr_id)    

    val = N_TICK*N_VALUE+1
    for i in range(N_TICK*N_VALUE, (N_TICK+1)*N_VALUE):
        if(i < len(sort_group)):
            print("%d. %s  %s  %s" % (val, sort_group[i]["new"], sort_group[i]["date"], sort_group[i]["name"]))
            val = val + 1

def loadposts (CURRENT_READ, usr_id):
    del sort_group[:]
    data = []
    read = []
    tick = 0
    for i in CURRENT_READ["subjects"] :
        for k in i["thread"]:
            new = " "
            if( usr_id not in k["usersViewed"] ):
                new = "N"    
            value = {
                "date": k["date"],
                "name": i["name"],
                "cont": k,
                "new" : new
            }
            if(new == " "):
                read.append(value)
            else:
                data.append(value)
    data.sort(key=lambda x: datetime.strptime(x["date"], "%Y-%m-%d %H:%M:%S"))
    read.sort(key=lambda x: datetime.strptime(x["date"], "%Y-%m-%d %H:%M:%S"))

    for k in data:
        sort_group.append(k)
    for k in read:
        sort_group.append(k)

def printformat (N_VALUE, N_TICK, CURRENT_READ, CURRENT_MODE, usr_id):
    if(CURRENT_MODE == MODE_AG):
        frmt = "%d. (%s)   %s"
    else:
        frmt = "%d%-5s%s    %s"
    for i in range(N_TICK*N_VALUE, (N_TICK+1)*N_VALUE):
        if ( i < len(CURRENT_READ) ):
            if(CURRENT_MODE == MODE_AG):
                if(CURRENT_READ[i]["name"] in client_data["subscriptions"]):
                    sub = "s"
                else:
                    sub = " "
                print(frmt % (i+1, sub , CURRENT_READ[i]["name"]))
            else:
                cur = None
                tmp = loadvalue(usr_id)
                for g in tmp["client"]:
                    if(g["usr"] == usr_id):
                        cur = g

                #print(CURRENT_READ[i])

                if("content" in CURRENT_READ[i]):
                    CURRENT_READ[i].update({"total_posts":CURRENT_READ[i]["content"]["total_posts"]})

                if(CURRENT_READ[i]["name"] not in cur["data"] or "total_posts" not in cur["data"][CURRENT_READ[i]["name"]]):
                    tot = CURRENT_READ[i]["total_posts"]
                else:
                    tot = CURRENT_READ[i]["total_posts"] - cur["data"][CURRENT_READ[i]["name"]]["total_posts"]
                updatecheck(usr_id, CURRENT_READ[i])
                print(frmt % (i+1,".", str(tot), CURRENT_READ[i]["name"]))
    return



def establishconnection(ipaddr, port):
    """
    Establish and return connection socket to server
    """
    cl_socket = socket(AF_INET, SOCK_STREAM)
    cl_socket.connect((ipaddr, port))
    return cl_socket


def main():
    """
    Main function
    """

    """
    Vars
    """
    global DEFAULT_SIZE
    global END_PACKET
    global DEFAULT_SEND_SIZE

    N_VALUE         = 5
    N_TICK          = -1
    N_DEFAULT       = 5


    global MODE_ST
    global MODE_AG
    global MODE_SG
    global MODE_RG

    MODE_ST         = 0
    MODE_AG         = 1
    MODE_SG         = 2
    MODE_RG         = 3
    MODE_RG_R       = 4
    CURRENT_MODE    = MODE_ST
    CURRENT_READ    = {}


    DEFAULT_SIZE    = 4096
    DEFAULT_IP      = "127.0.0.1"
    DEFAULT_PORT    = 9399
    INPUT_LOGIN     = "login"
    INPUT_LOGOUT    = "logout"
    INPUT_HELP      = "help"
    INPUT_QUIT      = "quit"
    INPUT_AG        = "ag"
    INPUT_SG        = "sg"
    INPUT_RG        = "rg"
    INPUT_Q         = "q"
    INPUT_S         = "s"
    INPUT_U         = "u"
    INPUT_N         = "n"
    INPUT_R         = "r"
    INPUT_P         = "p"
    SUCCESS         = "success"
    ERROR           = "error"
    END_PACKET      = "/*/!/$/*"

    global client_data
    client_data     = {}

    global group_data
    group_data      = {}

    global sort_group
    sort_group      = []
    

    with open("data.txt", "a+") as f:
        print("Cache Loaded")


    # DEFAULT_SEND_SIZE = DEFAULT_SIZE - len(END_PACKET)

    logged = False
    global usr_nm
    usr_nm = ''

    # fetch arguments
    if len(sys.argv) < 1:
        print("Not enough arguments, must include IP...IE: python discussionClient.py 127.0.0.1")
        sys.exit(1)
    ipaddr = sys.argv[1]
    cl_socket = establishconnection(ipaddr, DEFAULT_PORT)
    try:
        # print "Attempting to connect to " + ipaddr + ":" + DEFAULT_PORT
        while True:
            usr_input = input("> ").split(' ')
            sys.stdout.write(colored(("Input: " + str(usr_input[0]) + "\n"), 'red'))
            sys.stdout.flush()

            if usr_input[0] == INPUT_HELP:
                message = {
                    "type": "help"
                }
                senddata(cl_socket, message, DEFAULT_SIZE, END_PACKET)
                rec = receivedata(cl_socket, DEFAULT_SIZE, END_PACKET)
                print (rec["body"])
                continue

            if CURRENT_MODE != MODE_ST:
                if CURRENT_MODE == MODE_RG:
                    message = {"type":INPUT_RG, "userID":usr_nm}
                    if usr_input[0] == INPUT_Q:
                        message.update({"subcommand":INPUT_Q})
                        CURRENT_MODE = MODE_ST
                        senddata(cl_socket, message, DEFAULT_SIZE, END_PACKET)
                        rec = receivedata(cl_socket, DEFAULT_SIZE, END_PACKET)
                        print (rec["body"])
                    elif usr_input[0] == INPUT_R:
                        message.update({"subcommand":INPUT_R})
                        pattern_1 = re.compile("\d+")
                        pattern_2 = re.compile("\d+-\d+")
                        
                        print(sort_group)

                        if(pattern_1.match(usr_input[1])):
                            locate = int(usr_input[1])
                            message.update({"postSubject":sort_group[locate-1]["name"]})
                            message.update({"postNumber":sort_group[locate-1]["cont"]["postNumber"]})
  
                        elif(pattern_2.match(usr_input[1])):
                            split = usr_input[1].split("-")
                            for locate in range(int(split[0]), int(split[1])+1):
                                message.update({"postSubject":sort_group[locate-1]["name"]})
                                message.update({"postNumber":sort_group[locate-1]["cont"]["postNumber"]})                            
                        

                        senddata(cl_socket, message, DEFAULT_SIZE, END_PACKET)
                   # elif usr_input[0] == INPUT_P:
                        # Create post - Author/Content/Subject - Server handles the rest.

 
                elif CURRENT_MODE == MODE_AG or CURRENT_MODE == MODE_SG:
                    if CURRENT_MODE == MODE_AG:
                        message = {"type":INPUT_AG, "userID":usr_nm}
                    else:
                        message = {"type":INPUT_SG, "userID":usr_nm}

                    if usr_input[0] == INPUT_Q:
                        message.update({"subcommand":INPUT_Q})
                        CURRENT_MODE = MODE_ST
                        senddata(cl_socket, message, DEFAULT_SIZE, END_PACKET)
                        rec = receivedata(cl_socket, DEFAULT_SIZE, END_PACKET)
                        print (rec["body"])
                    elif usr_input[0] == INPUT_QUIT:
                        # leave ag mode
                        message.update({"subcommand": INPUT_Q})
                        senddata(cl_socket, message, DEFAULT_SIZE, END_PACKET)
                        rec = receivedata(cl_socket, DEFAULT_SIZE, END_PACKET)
                        print (rec["body"])
                        # and quit
                        message = {
                             "type": "quit"
                            }
                        senddata(cl_socket, message, DEFAULT_SIZE, END_PACKET)
                        sys.stdout.write(colored("Goodbye!\n", 'cyan'))
                        sys.stdout.flush()
                        cl_socket.close()
                        sys.exit(0)
                    elif usr_input[0] == INPUT_LOGOUT:
                        # leave ag mode
                        CURRENT_MODE = MODE_ST
                        message.update({"subcommand": INPUT_Q})
                        senddata(cl_socket, message, DEFAULT_SIZE, END_PACKET)
                        rec = receivedata(cl_socket, DEFAULT_SIZE, END_PACKET)
                        print (rec["body"])
                        # and logout
                        message = {
                            "type": "logout"
                        }
                        logged = False;
                        senddata(cl_socket, message, DEFAULT_SIZE, END_PACKET)
                        rec = receivedata(cl_socket, DEFAULT_SIZE, END_PACKET)
                        print(str(rec))

                    elif (CURRENT_MODE == MODE_AG and usr_input[0] == INPUT_S) or usr_input[0] == INPUT_U:
                        if usr_input[0] == INPUT_U:
                            message.update({"subcommand":INPUT_U})
                        else:
                            message.update({"subcommand":INPUT_S})
                        pattern = re.compile("\d+")
                        select = []
                        for x in range(1, (len(usr_input))):
                            index = int(usr_input[x])-1
                            if pattern.match(usr_input[x]) and index < (N_VALUE*(N_TICK)) and index >= (N_VALUE*(N_TICK-1)):
                                occur = False
                                if( usr_input[0] == INPUT_S and CURRENT_READ[int(usr_input[x])-1]["name"] not in client_data["subscriptions"]):
                                    client_data["subscriptions"].append(CURRENT_READ[int(usr_input[x])-1]["name"])
                                    occur = True
                                elif (usr_input[0] == INPUT_U and CURRENT_READ[int(usr_input[x])-1]["name"] in client_data["subscriptions"]):
                                    client_data["subscriptions"].remove(CURRENT_READ[int(usr_input[x])-1]["name"])
                                    occur = True
                                if(occur):
                                    select.append(CURRENT_READ[int(usr_input[x])-1]["name"])
                        if(len(select) == 0):
                            print("Invalid Selection")
                        else:
                            message.update({"selections":select})
                            print(str(message))
                            senddata(cl_socket, message, DEFAULT_SIZE, END_PACKET)
                            rec = receivedata(cl_socket, DEFAULT_SIZE, END_PACKET)
                            printformat(N_VALUE, N_TICK-1, CURRENT_READ, CURRENT_MODE, usr_nm)

                    elif (usr_input[0] == INPUT_N):
                        if(N_TICK * N_VALUE >= len(CURRENT_READ)):
                            message.update({"subcommand":INPUT_Q})
                            senddata(cl_socket,message,DEFAULT_SIZE,END_PACKET)
                            CURRENT_MODE = MODE_ST
                            rec = receivedata(cl_socket, DEFAULT_SIZE, END_PACKET)
                            print (rec["body"])
                        else:
                            printformat(N_VALUE, N_TICK, CURRENT_READ, CURRENT_MODE, usr_nm)
                            N_TICK = N_TICK + 1
                
                continue


            if usr_input[0] == INPUT_QUIT or usr_input[0] == INPUT_Q:
                message = {
                    "type": "quit"
                }
                senddata(cl_socket, message, DEFAULT_SIZE, END_PACKET)
                sys.stdout.write(colored("Goodbye!\n", 'cyan'))
                sys.stdout.flush()
                cl_socket.close()
                sys.exit(0)
            elif logged is False:
                if usr_input[0] == INPUT_LOGIN :
                    if len(usr_input) > 1:
                        usr_nm = usr_input[1]
                        message =  {
                            "type": "login",
                            "userID": usr_nm
                        }
                        senddata(cl_socket, message, DEFAULT_SIZE, END_PACKET)
                        rec = receivedata(cl_socket, DEFAULT_SIZE, END_PACKET)
                        if rec["type"].lower() == SUCCESS:
                            logged = True
                            print ("User " + usr_nm + " succesfully logged in")
                            client_data = rec["client"]
                            print(str(client_data))

                        else:
                            logged = False
                            print ("Error, User " + usr_nm + " not logged in")
                            usr_nm = ""
                else:
                    print("Not logged in\n")
            else:
                if usr_input[0] == INPUT_LOGOUT :
                    message = {
                        "type":"logout"
                    }
                    logged = False;
                    senddata(cl_socket, message, DEFAULT_SIZE, END_PACKET)
                    rec = receivedata(cl_socket, DEFAULT_SIZE, END_PACKET)
                    print(str(rec))
                    #break
                elif usr_input[0] == INPUT_AG:
                    print(len(usr_input))
                    message = {
                        "type":"ag",
                        "userID":usr_nm    
                    }
                    if len(usr_input) > 1:
                        pattern = re.compile("\d+")
                        if pattern.match(usr_input[1]):
                            message.update({"N" : usr_input[1]})
                            N_VALUE = int(usr_input[1])
                        else:
                            N_VALUE = N_DEFAULT
                    else:
                        N_VALUE = N_DEFAULT
                    N_TICK = 0
                    senddata(cl_socket, message, DEFAULT_SIZE, END_PACKET)
                    rec = receivedata(cl_socket, DEFAULT_SIZE, END_PACKET)
                    print("All Groups Available")
                    counter = 1
                    CURRENT_READ = rec["groupList"]
                    CURRENT_MODE = MODE_AG
                    
                    printformat(N_VALUE, N_TICK, CURRENT_READ, CURRENT_MODE, usr_nm)
                    N_TICK = N_TICK + 1
                elif usr_input[0] == INPUT_SG:
                    print(len(usr_input))
                    message = {
                        "type":"sg",
                        "userID":usr_nm
                    }
                    if len(usr_input) > 1:
                        pattern = re.compile("\d+")
                        if pattern.match(usr_input[1]):
                            message.update({"N" : usr_input[1]})
                            N_VALUE = int(usr_input[1])
                        else:
                            N_VALUE = N_DEFAULT
                    else:
                        N_VALUE = N_DEFAULT
                    N_TICK = 0
                    senddata(cl_socket, message, DEFAULT_SIZE, END_PACKET)
                    rec = receivedata(cl_socket, DEFAULT_SIZE, END_PACKET)
                    print("Subscribed Groups")
                    CURRENT_READ = rec["groupList"]
                    CURRENT_MODE = MODE_SG
                    printformat(N_VALUE, N_TICK, CURRENT_READ, CURRENT_MODE, usr_nm)
                    N_TICK = N_TICK + 1
                elif usr_input[0] == INPUT_RG:
                    message = {
                        "type":"rg",
                        "userID":usr_nm,
                        "groupList":usr_input[1]
                    }
                    #print(message)
                    if len(usr_input) > 2:
                        pattern = re.compile("\d+")
                        if pattern.match(usr_input[2]):
                            message.update({"N" : usr_input[2]})
                            N_VALUE = int(usr_input[2])
                        else:
                            N_VALUE = N_DEFAULT
                    else:
                        N_VALUE = N_DEFAULT
                    N_TICK = 0
                    senddata(cl_socket, message, DEFAULT_SIZE, END_PACKET)
                    rec = receivedata(cl_socket, DEFAULT_SIZE, END_PACKET)
                    
                    CURRENT_READ = rec["groupData"]
 
                    #updatevalue(usr_nm, CURRENT_READ, CURRENT_READ["content"]["subjects"][0])
                   
                    CURRENT_MODE = MODE_RG
                    printread(N_VALUE, N_TICK, CURRENT_READ, usr_nm)
                    N_TICK = N_TICK + 1      
        cl_socket.close()
        print ("User " + usr_nm + " succesfully logged out")
    except IOError as err:
        print(str(err))
        print ("An error has occurred with the connection to " + str(ipaddr) + ":" + str(DEFAULT_PORT))

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        raise SystemExit
