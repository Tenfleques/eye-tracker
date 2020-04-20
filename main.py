#!/usr/bin/python
from kivy.app import App
from kivy.properties import ObjectProperty

from kivy.factory import Factory
from kivy.uix.popup import Popup
from kivy.uix.floatlayout import FloatLayout
from floatInput import FloatInput
from kivy.uix.image import Image
from kivy.graphics.texture import Texture

from kivy.properties import ObjectProperty
from kivy.uix.popup import Popup
from kivy.clock import Clock, mainthread
import copy 

import os
import json
from collections import deque
import time
import threading 
from threading import Thread, current_thread
import sys

import cv2

from gaze_listener import WindowsRecordSocketReceiver, LogRecordSocketReceiver
from helpers import props, createlog, ERROR, WARNING, INFO, get_local_str, findClosestGazeFrame, getCSVHeaders, getSessionName, getVideoFPS


from collections import deque

from helpers import props
from kivy.core.window import Window

Window.size = (1200, 800)
Window.clearcolor = (1, 1, 1, 1)

# tcpserver = WindowsRecordSocketReceiver(port = 11000)
tcpserver = LogRecordSocketReceiver(port =11000)

class LoadDialog(FloatLayout):
    load = ObjectProperty(None)
    cancel = ObjectProperty(None)
    get_local_str = ObjectProperty(None)


class Root(FloatLayout):
    stop = threading.Event()
    
    def init_listeners(self):
        self.session_frames = deque()
        self.ready_device= False
        self.session_name = None
        self.initVideo()
        self.check_tracker = Clock.schedule_interval(self.updateNano,1/2)


    def updateNano(self, r):
        if self.eyetracker_ready():
            self.check_tracker.cancel()

    def save_dir_ready(self):
        lbl_output_dir = self.ids['lbl_output_dir']
        self.save_path = self.ids['lbl_output_dir'].text

        ready = os.path.isdir(self.save_path)       
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
            self.applog(error_log, WARNING, 'device_log')
        else:
            current = time.time()
            last_reading = float(recent_gazes[0].split(",")[0])
            
            time_diff = current - last_reading


            if time_diff > 2:
                self.applog(self.get_local_str("_gaze_device_out_of_sync"), INFO, 'device_log')
                return False

            self.applog(self.get_local_str("_gaze_device_ready"), INFO, 'device_log')

        return self.ready_device

    def get_local_str(self, key):
        return get_local_str(key)

    def applog(self, text, logtype = INFO, loglabel = 'app_log'):
        log = createlog(text, logtype)
        app_log = self.ids[loglabel]
        app_log.text = log


    def initSession(self):
        self.session_name = getSessionName()
        self.session_frames = deque()
        session_label = self.ids["session_label"]
        session_label.text = get_local_str("_session") + ": " + self.session_name

        os.makedirs(os.path.join(self.save_path, self.session_name), exist_ok=True)
        with open(os.path.join(self.save_path, "results-{}.csv".format(self.session_name)), "w") as f:
            f.write(getCSVHeaders())
            f.close()

    def getImageFilename(self, x): 
        return os.path.join(self.save_path, 
            "{}{}frame-{}.png".format(self.session_name,os.sep, x))

    def btn_play_click(self):
        if not self.eyetracker_ready():
            return
        if not self.save_dir_ready():
            return

        if self.ids['lbl_src_video'].text:
            if not self.video_play == None:
                self.video_play.cancel()
                # self.ids["camera"].play = False
                self.initVideo()
            else:
                # self.ids["camera"].play = True
                self.ids['gaze_log'].text = ""
                self.playVideo()
        else:
            self.applog(self.get_local_str("_load_stimuli_video"))

    def initVideo(self):
        self.video_player = self.ids['video_player']
        self.video_play = None
        
        self.ids["btn_capture"].text = self.get_local_str("_start")
        self.frame_id = 0

        v_path = self.ids['lbl_src_video'].text
        if v_path:
            if os.path.exists(v_path):
                self.capture = cv2.VideoCapture(v_path)
                if self.capture.isOpened():
                    self.video_update(None)
            
    def playVideo(self):
        if "capture" in props(self):
            self.ids['gaze_log'].text = ""
            
            fps = self.capture.get(cv2.CAP_PROP_FPS)
            if self.ids["txt_box_capture_rate"].text:
                if not self.ids["chkbx_use_video_fps"].active:
                    fps = float(self.ids["txt_box_capture_rate"].text)
            
            self.ids["txt_box_capture_rate"].text = str(fps)

            if self.capture.isOpened() and fps:
                self.initSession()
                delay = 1/fps
                self.ids["btn_capture"].text = self.get_local_str("_stop")
                self.video_play = Clock.schedule_interval(self.video_update, delay)
                self.applog("")
            else:
                self.applog(self.get_local_str("_video_error"))

    def video_update(self, dt):
        ret, frame = self.capture.read()
        # convert it to texture
        if not ret:
            if not self.video_play == None:
                self.video_play.cancel()

            # self.ids["camera"].play = False
            self.initVideo()
        else:
            if not dt == None:
                self.record(self.frame_id)
                self.frame_id += 1
                

            buf1 = cv2.flip(frame, 0)
            buf = buf1.tostring()
            texture1 = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='bgr') 
            #if working on RASPBERRY PI, use colorfmt='rgba' here instead, but stick with "bgr" in blit_buffer. 
            texture1.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
            # display image from the texture
            self.video_player.texture = texture1

    def record(self, frame_id):
        '''
            capture camera image
            get the video frame
            with the closest respective gaze record,
            and give them the names according to their captured time and date and record all to file and log.
        '''
        # get the top gaze data, find the record whose time closest or equal to call time.
        tm = time.time()
        frame = self.ids["camera"].export_as_image()
        recent_gazes = copy.copy(tcpserver.getTopRecords())
        
        # get top frames, find the frame whose time closest or equal to call time. 
        # # save the respective data, signal data, gaze data, frame data in thread with save_capture_cb as callback

        result = findClosestGazeFrame(recent_gazes, frame_id, tm)
        frame.save(self.getImageFilename(frame_id))

        self.ids['gaze_log'].text = result["log"] + self.ids['gaze_log'].text

        with open(os.path.join(self.save_path, "results-{}.csv".format(self.session_name)), "a") as f:
            f.write(result["gaze"] + "," + self.ids['lbl_src_video'].text +"\n")
            f.close()

    def dismiss_popup(self):
        self._popup.dismiss()

    def show_load(self):
        content = LoadDialog(load=self.load, cancel=self.dismiss_popup, get_local_str = self.get_local_str)
        self._popup = Popup(title=self.get_local_str("_select_directory"), content=content,size_hint=(0.9, 0.9))
        self._popup.open()
    
    def show_load_video(self):
        content = LoadDialog(load=self.load_video, cancel=self.dismiss_popup, get_local_str = self.get_local_str)
        self._popup = Popup(title=self.get_local_str("_select_src_video"), content=content,size_hint=(0.9, 0.9))
        self._popup.open()

    def get_video_src(self):
        return self.ids['lbl_src_video'].text

    def load_video(self, path, filenames):
        lbl_src_video = self.ids['lbl_src_video']
        video_path = ""
        if len(filenames):
            if not filenames[0] == path:
                video_path = os.path.join(path, filenames[0])
    
                self.ids["txt_box_capture_rate"].text = str(getVideoFPS(video_path))
                lbl_src_video.text = video_path
                self.initVideo()
        
        self.dismiss_popup()

    def load(self, path, filename):
        self.save_path = path        
        lbl_output_dir = self.ids['lbl_output_dir']
        lbl_output_dir.text = path
        self.dismiss_popup()

        self.save_dir_ready()
        self.applog(self.get_local_str("_save_directory_set"))


class Tracker(App):
    def build(self):
        Factory.register('Root', cls=Root)
        Factory.register('LoadDialog', cls=LoadDialog)
        self.root.init_listeners()
        self.STOP_THREADS = False
        
       
        self.socket_thread = Thread(target=tcpserver.serve_until_stopped,  args =(lambda : self.STOP_THREADS, ))
        try:
            # Start the thread
            print("should be threading here")
            self.socket_thread.start()
        # When ctrl+c is received
        except KeyboardInterrupt as e:
            tcpserver.server_close()
            sys.exit(e)

    def on_stop(self):
        self.STOP_THREADS = True
        self.root.stop.set()
        
        tcpserver.server_close()

        print("waiting server to close...")
        

if __name__ == '__main__':
    tracker = Tracker()
    tracker.run()

