#! /usr/bin/env python3

# Echo client program
import socket, sys, re, os
import params
from framedSock import FramedStreamSock
from threading import Thread, Lock
import time

switchesVarDefaults = (
    (('-s', '--server'), 'server', "localhost:50001"),
    (('-d', '--debug'), "debug", False), # boolean (set if present)
    (('-?', '--usage'), "usage", False), # boolean (set if present)
    )

fileName = input("Enter file name:\n")
if not os.path.isfile(fileName):
    print("File does not exist.")
    sys.exit()

progname = "framedClient"
paramMap = params.parseParams(switchesVarDefaults)

server, usage, debug  = paramMap["server"], paramMap["usage"], paramMap["debug"]

if usage:
    params.usage()


try:
    serverHost, serverPort = re.split(":", server)
    serverPort = int(serverPort)
except:
    print("Can't parse server:port from '%s'" % server)
    sys.exit(1)

class ClientThread(Thread):
    def __init__(self, serverHost, serverPort, debug):
        Thread.__init__(self, daemon=False)
        self.serverHost, self.serverPort, self.debug = serverHost, serverPort, debug
        self.start()
    def run(self):
       s = None
       for res in socket.getaddrinfo(serverHost, serverPort, socket.AF_UNSPEC, socket.SOCK_STREAM):
           af, socktype, proto, canonname, sa = res
           try:
               print("creating sock: af=%d, type=%d, proto=%d" % (af, socktype, proto))
               s = socket.socket(af, socktype, proto)
           except socket.error as msg:
               print(" error: %s" % msg)
               s = None
               continue
           try:
               print(" attempting to connect to %s" % repr(sa))
               s.connect(sa)
           except socket.error as msg:
               print(" error: %s" % msg)
               s.close()
               s = None
               continue
           break

       if s is None:
           print('could not open socket')
           sys.exit(1)

       fs = FramedStreamSock(s, debug=debug)


       print("sending FILE NAME")
       fs.sendmsg(fileName.encode())
       r = fs.receivemsg()
       print("received:", r.decode())
       if(r.decode() == "SUCCESS"):
           f = open(fileName, 'rb')
           line = f.read(100)
           while(line):
               #s.send(line)
               print("Client line: " + line.decode())
               fs.sendmsg(line)
               #framedSend(s, line, debug)
               line = f.read(100)
           #framedSend(s, b"done", debug)
           print("Outside while")
           fs.sendmsg(b"done")
           print("received:", fs.receivemsg())
       #fs.sendmsg(b"hello world")
       #print("received:", fs.receivemsg())

for i in range(2):
    ClientThread(serverHost, serverPort, debug)
