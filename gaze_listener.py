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
from ctypes import cdll, c_double, c_bool, c_int, Structure, POINTER

from collections import deque

QUEUE_SIZE = 10 

def props(cls):   
  return [i for i in cls.__dict__.keys() if i[:1] != '_']

tobii_dll_path = "TobiiEyeLib\\x64\\Debug\\TobiiEyeLib.dll"

class WinInteractiveRecord(Structure):
    _fields_ = [('x', c_double),
            ('y', c_double),
            ('timestamp', c_double),
            ('engineTimestamp', c_double),
            ('valid', c_bool),
            # ('lgaze_x', c_double), 
            # ('lgaze_y', c_double),
            # ('rgaze_x', c_double), 
            # ('rgaze_y', c_double),
            # ('lpos_x', c_double), 
            # ('lpos_y', c_double),
            # ('lpos_z', c_double),
            # ('rpos_x', c_double),
            # ('rpos_y', c_double),
            # ('rpos_z', c_double)
        ]

class TobiiWinGazeWatcher():
    """
        simple API to the gaze watcher on windows platforms
    """
    recent_gazes = deque(QUEUE_SIZE*"", QUEUE_SIZE)
    
    def __init__(self):
        self.tobiiEyeLib = cdll.LoadLibrary(tobii_dll_path)

        self.tobiiEyeLib.stop.restype = c_int
        self.tobiiEyeLib.start.restype = c_int
        started = self.tobiiEyeLib.start()
        print("listener started", started)
        # getLatest returns latest 10 records of the gaze data 
        self.tobiiEyeLib.getLatest.restype = POINTER(WinInteractiveRecord)

    def getTopRecords(self):
        return self.recent_gazes

    def server_close(self):
        stopped = self.tobiiEyeLib.stop()
        print("listener stopped", stopped)
        self.play = 0

    def serve_until_stopped(self, stop):
        while not stop():
            output = self.tobiiEyeLib.getLatest()
            # print(output[0].x, output[0].y)

            for i in range(QUEUE_SIZE):
                message = '''{},
                        {},{},
                        {},{},
                        {},{},{},
                        {},{},{},
                        {}'''.format(
                                output[i].timestamp,
                                output[i].x, output[i].y,
                                .0, .0,
                                .0, .0, .0,
                                .0, .0, .0,
                                # output[i].lgaze_x, output[i].lgaze_y, 
                                # output[i].rgaze_x, output[i].rgaze_y, 
                                # output[i].lpos_x, output[i].lpos_y, output[i].lpos_z, 
                                # output[i].rpos_x, output[i].rpos_y, output[i].rpos_z,
                                int(output[i].valid))

                self.recent_gazes.appendleft(message)
            self.play = not stop()



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
