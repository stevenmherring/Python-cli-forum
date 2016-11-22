from socket import *
from termcolor import colored
import sys, os, json, math, time

def establishConnection(ipaddr, port):
    """
    Establish and return connection socket to server
    """
    cl_socket = socket(AF_INET, SOCK_STREAM)
    cl_socket.connect((ipaddr, port))
    return cl_socket

def receiveData(cSocket):
    """
    Receive all packets from server and return complete JSON object
    """
    rec = cSocket.recv(DEFAULT_SIZE)
    rec = bytes.decode(rec)
    rec = rec.rstrip(END_PACKET)
    rec = rec.split(END_PACKET)
    inc = json.loads(rec[0])
    del rec[0]
    incomingPackets = inc["incoming"]
    ret = ""
    for d in rec:
        ret = ret + d
    incomingPackets = incomingPackets - len(rec)
    if incomingPackets == 1:
        ret = ret + bytes.decode(cSocket.recv(DEFAULT_SIZE))
        ret = ret.rstrip(END_PACKET)
    else:
        while incomingPackets > 0:
            incomingPackets == incomingPackets - 1
            ret = ret + bytes.decode(cSocket.recv(DEFAULT_SIZE))
            ret = ret.rstrip(END_PACKET)
    return json.loads(ret)

def sendData(clientSocket, data):
    """
    Divides data into sizable packets and sends them
    """
    data = json.dumps(data)
    packetsToSend = math.ceil(len(data) / DEFAULT_SEND_SIZE)
    currentPos = 0
    initMessage = {
        "incoming": packetsToSend
    }
    clientSocket.send(str.encode(json.dumps(initMessage) + END_PACKET))
    time.sleep(1)
    while packetsToSend > 0:
        endPos = currentPos + DEFAULT_SIZE
        if packetsToSend == 1:
            clientSocket.send(str.encode(data[currentPos:] + END_PACKET))
        else:
            clientSocket.send(str.encode(data[currentPos:endPos]))
        currentPos = endPos
        packetsToSend = packetsToSend - 1

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
    DEFAULT_PORT    = 9390
    INPUT_LOGIN     = "login"
    INPUT_LOGOUT    = "logout"
    INPUT_HELP      = "help"
    INPUT_QUIT      = "quit"
    INPUT_Q         = "q"
    SUCCESS         = "success"
    ERROR           = "error"

    END_PACKET      = "/*/!/$/*"
    DEFAULT_SEND_SIZE = DEFAULT_SIZE - len(END_PACKET)

    logged = False
    usr_nm = ''

    ipaddr = ''

    #fetch arguments
    if len(sys.argv) < 1:
        print("Not enough arguments, must include IP...IE: python discussionClient.py 127.0.0.1")
        sys.exit(1)
    ipaddr = sys.argv[1]
    cl_socket = establishConnection(ipaddr, DEFAULT_PORT)
    try:
        #print "Attempting to connect to " + ipaddr + ":" + DEFAULT_PORT
        while True:
            usr_input = input("> ").split(' ')
            sys.stdout.write(colored(("Input: " + str(usr_input[0]) + "\n"), 'red'))
            sys.stdout.flush()
            if usr_input[0] == INPUT_HELP:
                message = {
                    "type":"help"
                }
                sendData(cl_socket, message)
                rec = receiveData(cl_socket)
                print (rec["body"])
            elif usr_input[0] == INPUT_QUIT or usr_input[0] == INPUT_Q:
                message = {
                    "type":"quit"
                }
                sendData(cl_socket, message)
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
                        sendData(cl_socket, message)
                        rec = receiveData(cl_socket)
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
                    sendData(cl_socket, message)
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
