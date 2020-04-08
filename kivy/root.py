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

from helpers import props, createlog, ERROR, WARNING, INFO 

LOCALE = {}
with open("_locale.json", "r") as f:
    LOCALE = json.load(f)

LOCALE["__empty"] = {
    "ru" : "",
    "en" : ""
}


class LoadDialog(FloatLayout):
    load = ObjectProperty(None)
    cancel = ObjectProperty(None)
    get_local_str = ObjectProperty(None)


class Root(FloatLayout):
    def init_impulse_gen(self):
        self.RECENT_GAZES = deque("", 100)

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
        recent_gazes = props(self)

        ready = 'RECENT_GAZES' in recent_gazes

        error_log = self.get_local_str("_gaze_device_not_ready")

        if not ready:
            self.applog(error_log, WARNING)
        
        if not recent_gazes[0]:
            self.applog(error_log, WARNING)
        
        return ready


    def applog(self, text, logtype = INFO):
        log = createlog(text, logtype)
        app_log = self.ids['app_log']
        app_log.text = log + app_log.text

    def btn_play_click(self):
        camera = self.ids['camera']
        toggle_play = self.ids['toggle_play']
    
        if not self.save_dir_ready():
            toggle_play.state = 'normal'
            return 

        if not self.eyetracker_ready():
            toggle_play.state = 'normal'
            return
            
        if camera.play:
            # next click will subscribe to tracker 
            toggle_play.text = self.get_local_str('_start')
            self.capture_up = False
        else:
            # will be subscribing to tracker
            toggle_play.text = self.get_local_str('_stop')
            
        camera.play = not camera.play


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