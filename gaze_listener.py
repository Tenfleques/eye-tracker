import pickle
import logging
import logging.handlers
import socketserver
import struct
import select
import time
from threading import Thread, current_thread
import sys
import socket

from collections import deque

QUEUE_SIZE = 10 

def props(cls):   
  return [i for i in cls.__dict__.keys() if i[:1] != '_']

class LogRecordStreamHandler(socketserver.StreamRequestHandler):
    """Handler for a streaming logging request.
    """

    def handle(self):
        """
        Handle multiple requests - each expected to be a 4-byte length,
        followed by the LogRecord in pickle format. 
        """
        while self.server.play:
            chunk = self.connection.recv(4)
            
            if len(chunk) < 4:
                break

            slen = struct.unpack(">L", chunk)[0]
            chunk = self.connection.recv(slen)

            while len(chunk) < slen:
                if not self.server.play:
                    break
                chunk = chunk + self.connection.recv(slen - len(chunk))

            print(chunk)
            # obj = self.unPickle(chunk)

            #record = logging.makeLogRecord(obj)

            #self.handleLogRecord(record)


    def unPickle(self, data):
        return pickle.loads(data)

    def handleLogRecord(self, record):
        if record.name == self.server.logname:
            self.server.recent_gazes.appendleft(record.getMessage())
        # logger = logging.getLogger(name)
        # logger.handle(record)

class LogRecordSocketReceiver(socketserver.ThreadingTCPServer):
    """
        simple TCP socket-based logging receiver.
    """

    allow_reuse_address = 1
    timeout = 3
    recent_gazes = deque(QUEUE_SIZE*"", QUEUE_SIZE)
    
    def __init__(self, host='localhost',
                 port=logging.handlers.DEFAULT_TCP_LOGGING_PORT,
                 handler=LogRecordStreamHandler):
        
        self.handler = handler
        print(port)
        
        socketserver.ThreadingTCPServer.__init__(self, (host, port), self.handler)
        
        self.play = 1
        self.logname = "gaze_logger"

    def getTopRecords(self):
        return self.recent_gazes


    def server_close(self):
        self.play = 0

    def serve_until_stopped(self, stop):
        while not stop():
            rd, wr, ex = select.select([self.socket.fileno()],
                                       [], [],
                                       self.timeout)
            if rd:
                self.handle_request()
            self.play = not stop()

    #    self.serve_forever(poll_interval=1/100)



def talonGazeListener():
    # logging.basicConfig(
    #     format="%(relativeCreated)5d %(name)-15s %(levelname)-8s %(message)s")
    tcpserver = LogRecordSocketReceiver()
    print("About to start TCP server...")
    socket_thread_alive = True

    socket_thread = Thread(target=tcpserver.serve_until_stopped, args=(lambda : not socket_thread_alive, ))
    try:
        # Start the thread
        socket_thread.start()
        # If the child thread is still running
        # while socket_thread.is_alive():
            # Try to join the child thread back to parent for 0.5 seconds
            # socket_thread.join(0.5)
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
        self.update_thread = None
        self.stop = lambda : False

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
        if self.update_thread:
            self.update_thread._stop()
        self.s.close()
        self.s = None

    def continuousUpdate(self, stop):
        while (not stop()) and self.s:
            data = self.s.recv(1024)
            print(data, " received")
            record = repr(data)
            self.recent_gazes.append(record)
            self.play = not stop()

    def serve_until_stopped(self, stop):
         if self.s is None:
            print('could not open socket')
            return
         self.stop = stop

         with self.s:
            self.s.sendall(b'stream')
            self.update_thread = Thread(self.continuousUpdate)
            self.update_thread.start()


def winEyeGazeListener():
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


tcpserver = LogRecordSocketReceiver(port =11000)
def main():
    socket_thread = Thread(target=tcpserver.serve_until_stopped,  args =(lambda : False, ))
    try:
        # Start the thread
        print("should be threading here")
        socket_thread.start()
        print("thread started...")
    # When ctrl+c is received
    except KeyboardInterrupt as e:
        tcpserver.server_close()
        sys.exit(e)

if __name__ == "__main__":
    # winEyeGazeListener()
    main()
