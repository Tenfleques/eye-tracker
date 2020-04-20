# Echo client program
import socket
import sys
import pickle
import socketserver
import struct
import select
import time
from threading import Thread, current_thread
import sys

from collections import deque

QUEUE_SIZE = 10 


class WindowsRecordSocketReceiver(socketserver.ThreadingTCPServer):
    """
        simple TCP socket-based logging receiver.
    """
    allow_reuse_address = 1
    timeout = 3
    recent_gazes = deque(QUEUE_SIZE*"", QUEUE_SIZE)
    
    def __init__(self,host = 'localhost',    # The remote host
                      port = 11000):   
        self.s = None

        for res in socket.getaddrinfo(host, port, socket.AF_UNSPEC, socket.SOCK_STREAM):
            af, socktype, proto, canonname, sa = res
            try:
                self.s = socket.socket(af, socktype, proto)
            except OSError as msg:
                self.s = None
                continue
            try:
                self.s.connect(sa)
            except OSError as msg:
                self.s.close()
                self.s = None
                continue
            break
     
    def getTopRecords(self):
        return self.recent_gazes

    def server_close(self):
        self.s.close()
        self.s = None

    def serve_until_stopped(self, stop):
         if self.s is None:
            print('could not open socket')
            return
         with self.s:
            self.s.sendall(b'stream')
            while (not stop()) and self.s:
                data = self.s.recv(1024)
                record = repr(data)
                self.recent_gazes.append(record)
                self.play = not stop()


def eyeGazeListener():
    tcpserver = WindowsRecordSocketReceiver()
    print("About to start TCP server...")
    socket_thread_alive = True
    socket_thread = Thread(target=tcpserver.serve_until_stopped, args=(lambda : not socket_thread_alive, ))
    try:
        # Start the thread
        socket_thread.start()
        for i in range(4):
            RECENT_GAZES = tcpserver.getTopRecords()
            if len(RECENT_GAZES):
                print(RECENT_GAZES[0])

            print("sleeping {}".format(i))
            
            time.sleep(1.5)

        socket_thread_alive = False
        tcpserver.server_close()
        print("waiting to close")
        sys.exit(0)
        print("should be closed now")
    # When ctrl+c is received
    except KeyboardInterrupt as e:
        # Set the alive attribute to false
        socket_thread_alive = False
        # Exit with error code
        sys.exit(e)

if __name__ == "__main__":
     eyeGazeListener()
