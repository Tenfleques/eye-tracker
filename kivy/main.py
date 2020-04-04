#!/usr/bin/python
from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.factory import Factory
from kivy.properties import ObjectProperty
from kivy.uix.popup import Popup

from kivy.clock import Clock

import os
import json
import tobii_research as tr

from kivy.core.window import Window
import time

Window.clearcolor = (1, 1, 1, 1)

ERROR = 1
WARNING = 2
INFO = 3
LOCALE = {}
with open("_locale.json", "r") as f:
    LOCALE = json.load(f)

LOCALE["__empty"] = {
    "ru" : "",
    "en" : ""
}

def props(cls):   
  return [i for i in cls.__dict__.keys() if i[:1] != '_']


class LoadDialog(FloatLayout):
    load = ObjectProperty(None)
    cancel = ObjectProperty(None)
    get_local_str = ObjectProperty(None)


class Root(FloatLayout):        
    def init_tracker(self):
        if 'eyetracker' not in props(self):
            found_eyetrackers = tr.find_all_eyetrackers()
            if found_eyetrackers:
                self.eyetracker = found_eyetrackers[0]
                self.eyetracker.subscribe_to(tr.EYETRACKER_GAZE_DATA, self.capture, as_dictionary=True)
            
                self.capture_up = True
                fps = 0.3
                # Clock.schedule_interval(self.capture, 1.0/fps)
            else:
                self.applog(self.get_local_str("_tobii_not_found"), WARNING)

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
        ready = 'eyetracker' in props(self)

        error_log = self.get_local_str("_tobii_not_found")

        if not ready:
            self.applog(error_log, ERROR)
        
        return ready

    def applog(self, text, logtype = INFO):
        str_logtype = {
            INFO : "INFO",
            ERROR : "ERROR",
            WARNING: "WARNING"
        }
        timestr = time.strftime("%Y/%m/%d %H:%M:%S")
        app_log = self.ids['app_log']
        log = "{}\t {} \n {} \n".format(str_logtype.get(logtype, INFO), timestr, text)

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
            self.eyetracker.unsubscribe_from(tr.EYETRACKER_GAZE_DATA, self.capture)
        else:
            # will be subscribing to tracker
            toggle_play.text = self.get_local_str('_stop')
            self.capture_up = True
            self.eyetracker.subscribe_to(tr.EYETRACKER_GAZE_DATA, self.capture, as_dictionary=True)
            
        camera.play = not camera.play

    def capture(self,gaze_data):
        '''
        Callback Function to capture the images with the respective gaze record and give them the names
        according to their captured time and date and record all to log.
        '''

        if not self.save_dir_ready():
            return

       
        timestr = time.strftime("%Y%m%d_%H%M%S")
        filename = "IMG_{}.png".format(timestr)

        camera = self.ids['camera']
        camera.export_to_png(os.path.join(self.save_path,filename))

        timestr = time.strftime("%Y/%m/%d %H:%M:%S") # for log format as user friendly date 

        record = "{timestr}, {gaze_left_eye}, {gaze_right_eye}, {frame} \n".format(
            timestr=timestr,
            gaze_left_eye=gaze_data['left_gaze_point_on_display_area'],
            gaze_right_eye=gaze_data['right_gaze_point_on_display_area'],
            frame=filename)
        
        # write log to file
        with open(os.path.join(self.save_path,"log.csv"), "a") as f:
            f.write(record)
            f.close()

        gaze_log = self.ids['gaze_log']
        gaze_log.text = record + gaze_log.text

    def dismiss_popup(self):
        self._popup.dismiss()

    def show_load(self):
        content = LoadDialog(load=self.load, cancel=self.dismiss_popup, get_local_str = self.get_local_str)
        self._popup = Popup(title=self.get_local_str("_select_directory"), content=content,
                            size_hint=(0.9, 0.9))
        self._popup.open()

    def get_local_str(self, key):
        lang = "ru"
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
    pass


Factory.register('Root', cls=Root)
Factory.register('LoadDialog', cls=LoadDialog)

if __name__ == '__main__':
    Tracker().run()