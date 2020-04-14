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
import tobii_research as tr

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
            obj = self.unPickle(chunk)

            record = logging.makeLogRecord(obj)

            self.handleLogRecord(record)


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

def EyeFrame(b, key):
    data = b[key]
    time_data = {
        "device" : b["device_time_stamp"],
        "system" : b["system_time_stamp"]
    }
    gaze = b[key]["gaze_point"]

    record = {
        "gaze" : {
            "x" : gaze["position_on_display_area"][0],
            "y" : gaze["position_on_display_area"][1]
        },
        "pos" : {
            "x" : gaze["position_in_user_coordinates"][0],
            "y" : gaze["position_in_user_coordinates"][1],
            "z" : gaze["position_in_user_coordinates"][2]
        },
        "time" : time_data,
        "valid" : gaze["validity"]
    }

    return record

class WindowsGazeListener:
    def __init__(self):
        found_eyetrackers = tr.find_all_eyetrackers()
        for (i, eyetracker) in enumerate(found_eyetrackers):
            print("Address: " + eyetracker.address)
            print("Model: " + eyetracker.model)
            print("Name (It's OK if this is empty): " + eyetracker.device_name)
            print("Serial number: " + eyetracker.serial_number)
        
        self.eyetracker = None
        if not len(found_eyetrackers):
            print("none supported tracker found")
        else:
            self.eyetracker = found_eyetrackers[0]
        
        self.recent_gazes = deque(QUEUE_SIZE*"", QUEUE_SIZE)
    
    def getTopRecords(self):
        return self.recent_gazes

    def gaze_data_handler(self, b):
        # print("Left eye: ({gaze_left_eye}) \t Right eye: ({gaze_right_eye})".format(
        #     gaze_left_eye=gaze_data['left_gaze_point_on_display_area'],
        #     gaze_right_eye=gaze_data['right_gaze_point_on_display_area'])
        l, r = EyeFrame(b, 'Left'), EyeFrame(b, 'Right')

        main_gaze = l["valid"] and r["valid"]

        message = '''{},
                    {},{},
                    {},{},
                    {},{},{},
                    {},{},{},
                    {}'''.format(
                            time.time(),
                            l["gaze"]["x"], l["gaze"]["y"], 
                            r["gaze"]["x"], r["gaze"]["y"],
                            l["pos"]["x"], l["pos"]["y"], l["pos"]["z"],
                            r["pos"]["x"], r["pos"]["y"], r["pos"]["z"],
                            int(main_gaze),
                            )
        message = "".join(message.split())

        self.recent_gazes.appendleft(message)

    def server_close(self):
        if self.eyetracker:
            self.eyetracker.unsubscribe_from(tr.EYETRACKER_GAZE_DATA, self.gaze_data_handler)

    def serve_until_stopped(self, stop):
        if self.eyetracker:
            self.eyetracker.subscribe_to(tr.EYETRACKER_GAZE_DATA,  self.gaze_data_handler, as_dictionary=True)

def main():
    win_listener = WindowsGazeListener()
    win_listener.serve_until_stopped(False)
    time.sleep(5)
    win_listener.server_close()

if __name__ == "__main__":
    main()