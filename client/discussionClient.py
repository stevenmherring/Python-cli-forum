from socket import *
from termcolor import colored
import sys, os, json

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

logged = False
usr_nm = ''

ipaddr = input("IP Address: ")
try:
    #print "Attempting to connect to " + ipaddr + ":" + DEFAULT_PORT

    cl_socket = socket(AF_INET, SOCK_STREAM)
    cl_socket.connect((DEFAULT_IP,int(DEFAULT_PORT)))

    while True:
        usr_input = input("> ").split(' ')
        sys.stdout.write(colored(("Input: " + str(usr_input[0]) + "\n"), 'red'))
        sys.stdout.flush()
        if usr_input[0] == INPUT_HELP:
            message = {
                "type":"help"
            }
            cl_socket.send(str.encode(json.dumps(message)))
            rec = json.loads(bytes.decode(cl_socket.recv(DEFAULT_SIZE)))
            print (rec["body"])

        elif logged is False:
            if usr_input[0] == INPUT_LOGIN :
                if len(usr_input) > 1:
                    usr_nm = usr_input[1]
                    logged = True
                    message =  {
                        "type":"login",
                        "userID":usr_nm
                    }
                    cl_socket.send(str.encode(json.dumps(message)))
                    rec = json.loads(bytes.decode(cl_socket.recv(DEFAULT_SIZE)))
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
                cl_socket.send(str.encode(json.dumps(message)))
                break
            elif usr_input[0] == INPUT_QUIT or usr_input[0] == INPUT_Q:
                message = {
                    "type":"quit"
                }
                cl_socket.send(str.encode(json.dumps(message)))
                sys.stdout.write(colored("Goodbye!\n", 'cyan'))
                sys.stdout.flush()
                cl_socket.close()
                sys.exit(0)

    print ("User " + usr_nm + " succesfully logged out")
except IOError as err:
    print(str(err))
    print ("An error has occurred with the connection to " + str(ipaddr) + ":" + str(DEFAULT_PORT))
