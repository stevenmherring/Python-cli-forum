from socket import *
from termcolor import colored
from da_protocols import senddata, receivedata
import sys, os, json, time


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
    DEFAULT_SIZE    = 4096
    DEFAULT_IP      = "127.0.0.1"
    DEFAULT_PORT    = 9390
    INPUT_LOGIN     = "login"
    INPUT_LOGOUT    = "logout"
    INPUT_HELP      = "help"
    INPUT_QUIT      = "quit"
    INPUT_Q         = "q"
    SUCCESS         = "success"
    ERROR           = "error"
    END_PACKET      = "/*/!/$/*"
    global DEFAULT_SIZE
    global END_PACKET
    global DEFAULT_SEND_SIZE

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
                        logged = True
                        message =  {
                            "type":"login",
                            "userID":usr_nm
                        }
                        senddata(cl_socket, message, DEFAULT_SIZE, END_PACKET)
                        rec = receivedata(cl_socket, DEFAULT_SIZE, END_PACKET)
                        if rec["type"].lower() == SUCCESS:
                            print ("User " + usr_nm + " succesfully logged in")
                        else:
                            print ("Error, User " + usr_nm + " not logged in")
                else:
                    print("Not logged in\n")
            else:
                if usr_input[0] == INPUT_LOGOUT :
                    message =  {
                        "type":"logout"
                    }
                    senddata(cl_socket, message, DEFAULT_SIZE, END_PACKET)
                    break
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
