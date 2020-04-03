from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.factory import Factory
from kivy.properties import ObjectProperty
from kivy.uix.popup import Popup

from kivy.clock import Clock

import os
import tobiiresearch as tr

from kivy.core.window import Window
import time

Window.clearcolor = (1, 1, 1, 1)

def props(cls):   
  return [i for i in cls.__dict__.keys() if i[:1] != '_']

class LoadDialog(FloatLayout):
    load = ObjectProperty(None)
    cancel = ObjectProperty(None)


class Root(FloatLayout):
    loadfile = ObjectProperty(None)
    text_input = ObjectProperty(None)

    def init_tracker(self):
        if 'eyetracker' not in props(self):
            # found_eyetrackers = tr.find_all_eyetrackers()
            # self.eyetracker = found_eyetrackers[0]
            # self.eyetracker.subscribe_to(tr.EYETRACKER_GAZE_DATA, self.capture, as_dictionary=True)
            self.eyetracker = "tracker 1"
            self.capture_up = True
            fps = 0.3
            Clock.schedule_interval(self.capture, 1.0/fps)
       
        print("done building here ")

    def save_dir_ready(self):
        lbl_output_dir = self.ids['lbl_output_dir']
        
        ready = 'save_path' in props(self)
        if not ready:
            lbl_output_dir.color = (1,0,0,1)
        else:
            lbl_output_dir.color = (0,0,0,1)

        return ready

    def btn_play_click(self):
        camera = self.ids['camera']
        toggle_play = self.ids['toggle_play']
        
        if not self.save_dir_ready():
            return 
        
        if camera.play:
            # next click will subscribe to tracker 
            toggle_play.text = 'Play'
            self.capture_up = False
            # eyetracker.unsubscribe_from(tr.EYETRACKER_GAZE_DATA, gaze_data_callback)
            print("next click will be subscribing")
        else:
            # will be subscribing to tracker
            toggle_play.text = 'Stop'
            self.capture_up = True
            # eyetracker.subscribe_to(tr.EYETRACKER_GAZE_DATA, gaze_data_callback, as_dictionary=True)
            print("next click will be unsubscribing")
            
        camera.play = not camera.play

    def capture(self,gaze_data):
        '''
        Function to capture the images and give them the names
        according to their captured time and date.
        '''

        #  simulation using clock 
        gaze_data = {
            'left_gaze_point_on_display_area': 24,
            'right_gaze_point_on_display_area': 200,
        }

        if not self.save_dir_ready():
            return

        if 'capture_up' in props(self):            
            if not self.capture_up:
                return 

            timestr = time.strftime("%Y%m%d_%H%M%S")
            filename = "IMG_{}.png".format(timestr)

            camera = self.ids['camera']
            camera.export_to_png(os.path.join(self.save_path,filename))

            record = "{timestr}, {gaze_left_eye}, {gaze_right_eye}, {frame} \n".format(
                timestr=timestr,
                gaze_left_eye=gaze_data['left_gaze_point_on_display_area'],
                gaze_right_eye=gaze_data['right_gaze_point_on_display_area'],
                frame=filename)
            
            gaze_log = self.ids['gaze_log']
            gaze_log.text = gaze_log.text + record

    def dismiss_popup(self):
        self._popup.dismiss()

    def show_load(self):
        content = LoadDialog(load=self.load, cancel=self.dismiss_popup)
        self._popup = Popup(title="Select directory", content=content,
                            size_hint=(0.9, 0.9))
        self._popup.open()

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