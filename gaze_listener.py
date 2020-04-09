import pickle
import logging
import logging.handlers
import socketserver
import struct
import select
import time
from threading import Thread, current_thread
import sys

from collections import deque


def props(cls):   
  return [i for i in cls.__dict__.keys() if i[:1] != '_']

RECENT_GAZES = deque(100*"", 100)

class LogRecordStreamHandler(socketserver.StreamRequestHandler):
    """Handler for a streaming logging request.
    """

    def handle(self):
        """
        Handle multiple requests - each expected to be a 4-byte length,
        followed by the LogRecord in pickle format. 
        """
        while True:
            chunk = self.connection.recv(4)
            if len(chunk) < 4:
                break
            slen = struct.unpack(">L", chunk)[0]
            chunk = self.connection.recv(slen)
            while len(chunk) < slen:
                chunk = chunk + self.connection.recv(slen - len(chunk))
            obj = self.unPickle(chunk)

            record = logging.makeLogRecord(obj)
            self.handleLogRecord(record)

    def unPickle(self, data):
        return pickle.loads(data)

    def handleLogRecord(self, record):
        # if a name is specified, we use the named logger rather than the one
        # implied by the record.
        if self.server.logname is not None:
            name = self.server.logname
        else:
            name = record.name

        # print(name, record.getMessage())
        RECENT_GAZES.appendleft(record.getMessage())
        # logger = logging.getLogger(name)
        # logger.handle(record)

class LogRecordSocketReceiver(socketserver.ThreadingTCPServer):
    """
        simple TCP socket-based logging receiver.
    """

    allow_reuse_address = 1

    def __init__(self, host='localhost',
                 port=logging.handlers.DEFAULT_TCP_LOGGING_PORT,
                 handler=LogRecordStreamHandler):

        socketserver.ThreadingTCPServer.__init__(self, (host, port), handler)
        
        self.abort = 0
        self.timeout = 1
        self.logname = None
    def __del__(self):
        print("self files", self.files)

    def getTopRecords(self):
        global RECENT_GAZES
        return RECENT_GAZES

    def serve_until_stopped(self, stop):
        abort = 0
        while not abort and not stop():
            rd, wr, ex = select.select([self.socket.fileno()],
                                       [], [],
                                       self.timeout)
            if rd:
                self.handle_request()
            abort = self.abort
        
        self.server_close()


def main():
    # logging.basicConfig(
    #     format="%(relativeCreated)5d %(name)-15s %(levelname)-8s %(message)s")
    tcpserver = LogRecordSocketReceiver()
    print("About to start TCP server...")
    socket_thread_alive = True

    socket_thread = Thread(target=tcpserver.serve_until_stopped, args=(lambda : socket_thread_alive, ))
    try:
        # Start the thread
        socket_thread.start()
        # If the child thread is still running
        # while socket_thread.is_alive():
            # Try to join the child thread back to parent for 0.5 seconds
            # socket_thread.join(0.5)
        for i in range(15):
            TOP_LOGS = tcpserver.getTopRecords()
            print(RECENT_GAZES)

            if len(TOP_LOGS):
                print(TOP_LOGS[0].split(",")[0])

            print("sleeping {}".format(i))
            
            time.sleep(5)
        socket_thread.alive = False
        # Exit with error code
        sys.exit(0)
    # When ctrl+c is received
    except KeyboardInterrupt as e:
        # Set the alive attribute to false
        socket_thread.alive = False
        # Exit with error code
        sys.exit(e)

if __name__ == "__main__":
    main()