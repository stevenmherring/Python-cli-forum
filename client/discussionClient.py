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
    DEFAULT_SIZE    = 4096
    DEFAULT_IP      = "127.0.0.1"
    DEFAULT_PORT    = 9397
    INPUT_LOGIN     = "login"
    INPUT_LOGOUT    = "logout"
    INPUT_HELP      = "help"
    INPUT_QUIT      = "quit"
    INPUT_AG        = "ag"
    INPUT_Q         = "q"
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
                    "type":"help"
                }
                senddata(cl_socket, message, DEFAULT_SIZE, END_PACKET)
                rec = receivedata(cl_socket, DEFAULT_SIZE, END_PACKET)
                print (rec["body"])
            elif usr_input[0] == INPUT_QUIT or usr_input[0] == INPUT_Q:
                message = {
                    "type":"quit"
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
                            "type":"login",
                            "userID":usr_nm
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
                            if len(usr_input) == 3:
                                message.update({"subcommand" : usr_input[2]})
                        else:
                            message.update({"subcommand" : usr_input[1]})
                    senddata(cl_socket, message, DEFAULT_SIZE, END_PACKET)
                    rec = receivedata(cl_socket, DEFAULT_SIZE, END_PACKET)
                    print(rec["body"])
                    counter = 1
                    for a in rec["groups"]:
                        print(counter + "      " + a["name"])
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
