#! /usr/bin/env python3
import sys, os, socket, params, time
from threading import Thread, Lock
from framedSock import FramedStreamSock

switchesVarDefaults = (
    (('-l', '--listenPort') ,'listenPort', 50001),
    (('-d', '--debug'), "debug", True), # boolean (set if present)
    (('-?', '--usage'), "usage", False), # boolean (set if present)
    )


progname = "echoserver"
paramMap = params.parseParams(switchesVarDefaults)

debug, listenPort = paramMap['debug'], paramMap['listenPort']

if paramMap['usage']:
    params.usage()

lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # listener socket
bindAddr = ("127.0.0.1", listenPort)
lsock.bind(bindAddr)
lsock.listen(5)
print("listening on:", bindAddr)

class ServerThread(Thread):
    requestCount = 0            # one instance / class
    mutex = Lock()
    def __init__(self, sock, debug):
        Thread.__init__(self, daemon=True)
        self.fsock, self.debug = FramedStreamSock(sock, debug), debug
        self.start()
    def run(self):
        while True:
            ServerThread.mutex.acquire()
            print("Mutex acquired")
            try:
                msg = self.fsock.receivemsg()
                if not msg:
                    if self.debug: print(self.fsock, "server thread done")
                    return
                filename = msg.decode()
                if os.path.exists('server-files/' + filename):
                    print("File already exists on server")
                    self.fsock.sendmsg(b"Error: File already exists on server")
                    #framedSend(sock, b"Error: File already exists on server", debug)
                    return
                requestNum = ServerThread.requestCount
                time.sleep(0.001)
                ServerThread.requestCount = requestNum + 1
                #msg = ("%s! (%d)" % (msg, requestNum)).encode()
                #self.fsock.sendmsg(msg)
                self.fsock.sendmsg(b"SUCCESS")
                #framedSend(sock, b"SUCCESS", debug)
                f = open('server-files/' + filename, "wb")
                #line = framedReceive(sock, debug)
                line = self.fsock.receivemsg()
                while(line.decode() != "done"):
                    print("Server line: " + line.decode())
                    f.write(line)
                    #time.sleep(0.001)
                    #line = framedReceive(sock, debug)
                    line = self.fsock.receivemsg()
                f.close()
                #framedSend(sock, payload, debug)
                self.fsock.sendmsg(msg)
            finally:
                ServerThread.mutex.release()
                print("Mutex released")

while True:
    sock, addr = lsock.accept()
    ServerThread(sock, debug)
