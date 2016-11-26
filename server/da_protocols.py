"""
Protocol Module for 310 Discussion Server & Client
"""
import math, json


def receivedata(socketstream, packetlength, delimeter):
    """
    Receive all packets from server and return complete JSON object
    """
    rec = socketstream.recv(packetlength)
    rec = bytes.decode(rec)
    rec = rec.rstrip(delimeter)
    rec = rec.split(delimeter)
    inc = json.loads(rec[0])
    del rec[0]
    incomingpackets = inc["incoming"]
    ret = ""
    for d in rec:
        ret += d
    incomingpackets -= - len(rec)
    if incomingpackets == 1:
        ret += bytes.decode(socketstream.recv(packetlength))
        ret = ret.rstrip(delimeter)
    else:
        while incomingpackets > 0:
            incomingpackets -= 1
            ret += bytes.decode(socketstream.recv(packetlength))
            ret = ret.rstrip(delimeter)
    return json.loads(ret)


def senddata(socketstream, data, packetlength, delimeter):
    """
    Divides data into sizable packets and sends them
    """
    shiplength = packetlength - len(delimeter)
    data = json.dumps(data)
    outgoingpackets = math.ceil(len(data) / shiplength)
    currentposition = 0
    initMessage = {
        "incoming": outgoingpackets
    }
    socketstream.send(str.encode(json.dumps(initMessage) + delimeter))
    while outgoingpackets > 0:
        endposition = currentposition + shiplength
        if outgoingpackets == 1:
            socketstream.send(str.encode(data[currentposition:] + delimeter))
        else:
            socketstream.send(str.encode(data[currentposition:endposition]))
        currentposition = endposition
        outgoingpackets -= 1
