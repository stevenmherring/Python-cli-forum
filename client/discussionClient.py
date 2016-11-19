from socket import *
from termcolor import colored
import sys, os, json

DEFAULT_SIZE    = 4096
DEFAULT_IP      = "127.0.0.1"
DEFAULT_PORT    = 9390
INPUT_LOGIN     = "login"
INPUT_LOGOUT    = "logout"
INPUT_HELP      = "help"

logged = False
usr_nm = ''

ipaddr = raw_input("IP Address: ")
try:
    #print "Attempting to connect to " + ipaddr + ":" + DEFAULT_PORT

    cl_socket = socket(AF_INET, SOCK_STREAM)
    cl_socket.connect((DEFAULT_IP,int(DEFAULT_PORT)))

    while True:
        usr_input = raw_input("> ").split(' ')
        sys.stdout.write(colored(("Input: " + str(usr_input[0]) + "\n"), 'red'))
        sys.stdout.flush()
        if usr_input[0] == INPUT_HELP:
            message = {
                "type":"help"
            }
            cl_socket.send(json.dumps(message))
            rec = json.loads(bytes.decode(cl_socket.recv(DEFAULT_SIZE)))
            print rec["body"]

        elif logged is False:
            if usr_input[0] == INPUT_LOGIN :
                if len(usr_input) > 1:
                    usr_nm = usr_input[1]
                    print "User " + usr_nm + " succesfully logged in"
                    logged = True
                    message =  {
                        "type":"login",
                        "userId":usr_nm
                    }
                    cl_socket.send(json.dumps(message))
            else:
                print("Not logged in\n")
        else:
            if usr_input[0] == INPUT_LOGOUT :
                message =  {
                    "type":"logout"
                }
                cl_socket.send(json.dumps(message))
                break

    print "User " + usr_nm + " succesfully logged out"
except IOError as err:
    print(str(err))
    print ("An error has occurred with the connection to " + str(ipaddr) + ":" + str(DEFAULT_PORT))
