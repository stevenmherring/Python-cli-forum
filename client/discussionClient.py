from socket import *
from termcolor import colored
from da_protocols import senddata, receivedata
import sys, os, json, time
import re


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
    INPUT_Q         = "q"
    INPUT_S         = "s"
    INPUT_U         = "u"
    INPUT_N         = "n"
    SUCCESS         = "success"
    ERROR           = "error"
    END_PACKET      = "/*/!/$/*"

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
                if CURRENT_MODE == MODE_AG:
                    message = {"type":INPUT_AG, "userID":usr_nm}
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

                    elif usr_input[0] == INPUT_S or usr_input[0] == INPUT_U:
                        message.update({"subcommand":INPUT_S})
                        pattern = re.compile("\d+")
                        select = []
                        for x in range(1, (len(usr_input))):
                            if pattern.match(usr_input[x]) and int(usr_input[x])-1 < len(CURRENT_READ):
                                select.append(CURRENT_READ[int(usr_input[x])-1]["name"])
                        message.update({"selections":select})
                        print(str(message))
                        senddata(cl_socket, message, DEFAULT_SIZE, END_PACKET)
                continue

            print("HI")
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
                    if len(usr_input) > 2:
                        pattern = re.compile("\d+")
                        if pattern.match(usr_input[1]):
                            message.update({"N" : usr_input[1]})
                    senddata(cl_socket, message, DEFAULT_SIZE, END_PACKET)
                    rec = receivedata(cl_socket, DEFAULT_SIZE, END_PACKET)
                    print("All Groups Available")
                    counter = 1
                    CURRENT_READ = rec["groupList"]
                    CURRENT_MODE = MODE_AG
                    for a in rec["groupList"]:
                        print(str(counter) + ". (" + " "+ ") " + a["name"])
                        counter = counter + 1
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
