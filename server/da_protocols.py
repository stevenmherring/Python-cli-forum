"""
Protocol Module for 310 Discussion Server & Client
"""
import math, json

def receiveData(cSocket, packetLength, packetDelimeter):
    """
    Receive all packets from server and return complete JSON object
    """
    rec = cSocket.recv(packetLength)
    rec = bytes.decode(rec)
    rec = rec.rstrip(packetDelimeter)
    rec = rec.split(packetDelimeter)
    inc = json.loads(rec[0])
    del rec[0]
    incomingPackets = inc["incoming"]
    ret = ""
    for d in rec:
        ret = ret + d
    incomingPackets = incomingPackets - len(rec)
    if incomingPackets == 1:
        ret = ret + bytes.decode(cSocket.recv(packetLength))
        ret = ret.rstrip(packetDelimeter)
    else:
        while incomingPackets > 0:
            incomingPackets == incomingPackets - 1
            ret = ret + bytes.decode(cSocket.recv(packetLength))
            ret = ret.rstrip(packetDelimeter)
    return json.loads(ret)

def sendData(clientSocket, data, packetLength, packetDelimeter):
    """
    Divides data into sizable packets and sends them
    """
    packetShipLength = packetLength - len(packetDelimeter)
    data = json.dumps(data)
    packetsToSend = math.ceil(len(data) / packetShipLength)
    currentPos = 0
    initMessage = {
        "incoming": packetsToSend
    }
    clientSocket.send(str.encode(json.dumps(initMessage) + packetDelimeter))
    while packetsToSend > 0:
        endPos = currentPos + packetShipLength
        if packetsToSend == 1:
            clientSocket.send(str.encode(data[currentPos:] + packetDelimeter))
        else:
            clientSocket.send(str.encode(data[currentPos:endPos]))
        currentPos = endPos
        packetsToSend = packetsToSend - 1
