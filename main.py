#!/usr/bin/python
from kivy.app import App
from kivy.properties import ObjectProperty

from kivy.factory import Factory
from kivy.uix.popup import Popup

from kivy.uix.floatlayout import FloatLayout
from kivy.properties import ObjectProperty
from kivy.uix.popup import Popup
from kivy.clock import Clock, mainthread

import tobii_research as tr

import os
import json
from collections import deque
import time
import threading 
from threading import Thread, current_thread
import sys
from gaze_listener import LogRecordSocketReceiver
from helpers import props, createlog, ERROR, WARNING, INFO, get_local_str, findClosestGazeFrame, getCSVHeaders, getSessionName


from collections import deque

from helpers import props
from kivy.core.window import Window

Window.clearcolor = (1, 1, 1, 1)

tcpserver = LogRecordSocketReceiver()

class LoadDialog(FloatLayout):
    load = ObjectProperty(None)
    cancel = ObjectProperty(None)
    get_local_str = ObjectProperty(None)


class Root(FloatLayout):
    stop = threading.Event()
    
    def init_listeners(self):
        self.RECENT_FRAMES = deque({}, 90)
        self.camera = self.ids['camera']
        self.camera.play = True 
        self.clock_nano = 0
        self.control_nano = time.strftime("%H:%M:%S")
        self.ready_device= False
        self.session_name = None

        Clock.schedule_interval(self.updateNano,1/100)

    def updateNano(self, r):
        current = time.strftime("%H:%M:%S")
        if current == self.control_nano:
            self.clock_nano += 1
        else:
            self.control_nano = current
            self.clock_nano = 0

        if not self.ready_device:
            self.eyetracker_ready()

    def save_dir_ready(self):
        lbl_output_dir = self.ids['lbl_output_dir']
        
        ready = 'save_path' in props(self)
        if not ready:
            lbl_output_dir.color = (1,0,0,1)
            self.applog(self.get_local_str("_directory_not_selected"))
        else:
            lbl_output_dir.color = (0,0,0,1)

        return ready

    def eyetracker_ready(self):
        recent_gazes = tcpserver.getTopRecords()

        self.ready_device= len(recent_gazes) and recent_gazes[0]

        error_log = self.get_local_str("_gaze_device_not_ready")

        if not self.ready_device:
            self.applog(error_log, WARNING)
        else:
            self.applog(self.get_local_str("_gaze_device_ready"), INFO)

        return self.ready_device

    def get_local_str(self, key):
        return get_local_str(key)

    def applog(self, text, logtype = INFO):
        log = createlog(text, logtype)
        app_log = self.ids['app_log']
        app_log.text = log

    def btn_session_click(self):
        if not self.save_dir_ready():
            return 

        session = getSessionName()
        path = os.sep.join(self.save_path.split(os.sep)[:-1])
        self.save_path = os.path.join(path,session)
        os.makedirs(self.save_path, exist_ok=True)

        session_label = self.ids["session_label"]
        session_label.text = get_local_str("_session") + ": " + session
        self.initSession()

    def initSession(self):
        with open(os.path.join(self.save_path, "results.csv"), "w") as f:
            f.write(getCSVHeaders())
            f.close()

    def btn_play_click(self):
        frame = self.camera.export_as_image()
        gaze_log = self.ids['gaze_log']
        if not self.save_dir_ready():
            return 

        if not self.eyetracker_ready():
            return

        recent_gazes = tcpserver.getTopRecords()
        result = findClosestGazeFrame(recent_gazes, time.strftime("%H:%M:%S"), self.clock_nano)

        gaze_log.text = result["log"] + gaze_log.text
        frame.save(os.path.join(self.save_path, result["filename"]))
        
        with open(os.path.join(self.save_path, "results.csv"), "a") as f:
            f.write(result["gaze"])
            f.close()

    def capture(self):
        '''
        Callback Function to capture:
            the camera image
            with the respective gaze record, 
            signal data and give them the names
        according to their captured time and date and record all to log.
        '''

        if not self.save_dir_ready():
            return
        # get the top gaze data, find the record whose time closest or equal to call time. 
        # get top frames, find the frame whose time closest or equal to call time. 
        # save the respective data, signal data, gaze data, frame data 

    def dismiss_popup(self):
        self._popup.dismiss()

    def show_load(self):
        content = LoadDialog(load=self.load, cancel=self.dismiss_popup, get_local_str = self.get_local_str)
        self._popup = Popup(title=self.get_local_str("_select_directory"), content=content,size_hint=(0.9, 0.9))
        self._popup.open()


    def load(self, path, filename):
        session = getSessionName()
        self.save_path = os.path.join(path,session)
        os.makedirs(self.save_path, exist_ok=True)
        
        lbl_output_dir = self.ids['lbl_output_dir']
        lbl_output_dir.text = path
        self.dismiss_popup()

        self.save_dir_ready()
        session_label = self.ids["session_label"]
        session_label.text = get_local_str("_session") + ": " + session
        self.initSession()
        


class Tracker(App):
    def build(self):
        print("building")
        Factory.register('Root', cls=Root)
        Factory.register('LoadDialog', cls=LoadDialog)

        self.STOP_THREADS = False
        print("About to start TCP server...")
        self.socket_thread = Thread(target=tcpserver.serve_until_stopped,  args =(lambda : self.STOP_THREADS, ))
        # frames_thread = 
        try:
            # Start the thread
            self.socket_thread.start()
        # When ctrl+c is received
        except KeyboardInterrupt as e:
            # Set the alive attribute to false
            self.socket_thread.alive = False
            self.socket_thread.join()
            sys.exit(e)

    def on_stop(self):
        self.STOP_THREADS = True
        self.root.camera.play = False
        self.root.stop.set()
        self.socket_thread.alive = False
        
        del self.socket_thread

        print(props(self))
        sys.exit(0)
        quit()

if __name__ == '__main__':
    tracker = Tracker()
    tracker.run()
