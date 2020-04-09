#!/usr/bin/python
from kivy.app import App
from kivy.properties import ObjectProperty

from kivy.factory import Factory
from kivy.uix.popup import Popup

from kivy.uix.floatlayout import FloatLayout
from kivy.properties import ObjectProperty
from kivy.uix.popup import Popup
from kivy.clock import Clock

import tobii_research as tr
import locale

import os
import json
from collections import deque
import time 
from threading import Thread, current_thread
import sys
from gaze_listener import LogRecordSocketReceiver
from helpers import props, createlog, ERROR, WARNING, INFO 

LOCALE = {}
with open("_locale.json", "r") as f:
    LOCALE = json.load(f)

LOCALE["__empty"] = {
    "ru" : "",
    "en" : ""
}

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
    def init_listeners(self):
        self.RECENT_FRAMES = deque({}, 10)
        self.camera = self.ids['camera']

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

        ready = len(recent_gazes) and recent_gazes[0]

        error_log = self.get_local_str("_gaze_device_not_ready")

        if not ready:
            self.applog(error_log, WARNING)
        else:
            self.applog(self.get_local_str("_gaze_device_ready"), INFO)

        return ready


    def applog(self, text, logtype = INFO):
        log = createlog(text, logtype)
        app_log = self.ids['app_log']
        app_log.text = log + app_log.text

    def btn_play_click(self):
        toggle_play = self.ids['toggle_play']

        if not self.save_dir_ready():
            toggle_play.state = 'normal'
            return 

        if not self.eyetracker_ready():
            toggle_play.state = 'normal'
            return
            
        if self.camera.play:
            # next click will subscribe to tracker 
            toggle_play.text = self.get_local_str('_start')
            
        else:
            # will be subscribing to tracker
            toggle_play.text = self.get_local_str('_stop')
        
        recent_gazes = tcpserver.getTopRecords()

        print(recent_gazes[0].split(",")[0])


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
        self._popup = Popup(title=self.get_local_str("_select_directory"), content=content,
                            size_hint=(0.9, 0.9))
        self._popup.open()

    def get_local_str(self, key):
        lang = "ru"
        local_def = locale.getdefaultlocale()
        if len(local_def) and local_def[0]:
           sys_locale = local_def[0].split("_")[0]
           if sys_locale in ["en", "ru"]:
               lang = sys_locale
        
        if key in LOCALE:
            return LOCALE.get(key)[lang]

        return LOCALE["__empty"][lang]

    def load(self, path, filename):
        self.save_path = path
        lbl_output_dir = self.ids['lbl_output_dir']
        lbl_output_dir.text = self.save_path
        self.save_dir_ready()
        self.dismiss_popup()


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
            # Exit with error code
            
            # sys.exit(e)

    def on_stop(self):
        self.STOP_THREADS = True
        self.root.camera.play = False
        self.socket_thread.alive = False
        del self.socket_thread

        print(props(self))
        sys.exit(0)
        quit()

if __name__ == '__main__':
    tracker = Tracker()
    tracker.run()
