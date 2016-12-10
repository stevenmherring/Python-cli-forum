from socket import *
from termcolor import colored
from da_protocols import senddata, receivedata
import sys, os, json, time
import re


def printformat (N_VALUE, N_TICK, CURRENT_READ, CURRENT_MODE):
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
                print(frmt % (i+1,".", str(4), CURRENT_READ[i]["name"]))
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
    INPUT_Q         = "q"
    INPUT_S         = "s"
    INPUT_U         = "u"
    INPUT_N         = "n"
    SUCCESS         = "success"
    ERROR           = "error"
    END_PACKET      = "/*/!/$/*"

    global client_data
    client_data     = {}

    # DEFAULT_SEND_SIZE = DEFAULT_SIZE - len(END_PACKET)

    logged = False
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
                if CURRENT_MODE == MODE_AG or CURRENT_MODE == MODE_SG:
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
                            print(str(rec["body"]))
                            printformat(N_VALUE, N_TICK-1, CURRENT_READ, CURRENT_MODE)

                    elif (usr_input[0] == INPUT_N):
                        if(N_TICK * N_VALUE >= len(CURRENT_READ)):
                            message.update({"subcommand":INPUT_Q})
                            senddata(cl_socket,message,DEFAULT_SIZE,END_PACKET)
                            CURRENT_MODE = MODE_ST
                            rec = receivedata(cl_socket, DEFAULT_SIZE, END_PACKET)
                            print (rec["body"])
                        else:
                            printformat(N_VALUE, N_TICK, CURRENT_READ, CURRENT_MODE)
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
                    
                    printformat(N_VALUE, N_TICK, CURRENT_READ, CURRENT_MODE)
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
            
                    printformat(N_VALUE, N_TICK, CURRENT_READ, CURRENT_MODE)
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
