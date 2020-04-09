from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.core.window import Window
from kivy.uix.button import Button

from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
Window.show_cursor = True
# Create both screens. Please note the root.manager.current: this is how
# you can control the ScreenManager from kv. Each screen has by default a
# property manager that gives you the instance of the ScreenManager used.
from kivy.config import Config
from kivy.uix.video import Video
from VideoGenerator import *

Config.set('graphics', 'fullscreen', 'false')
Config.set('graphics', 'width', 800)
Config.set('graphics', 'height', 600)
Config.write()

import random

def decision(probability):
    return random.random() < probability

VideoGen_params = {}

video = Video()


class Parameter(BoxLayout):
    def __init__(self, label = "label1", startval = -1, **kwargs):
        super(Parameter, self).__init__(**kwargs)
        print(label)
        self.ids['l_val'].text = label
        self.name = label
        
        self.ids['t_val'].text = str(startval)
        VideoGen_params[label] = str(startval)
        self.value = str(startval)
        pass
        
    def press(self):
        print(self.value)
        
        
    def change_text(self):
        key = self.name
        value = self.value
        VideoGen_params[key] = value
        pass
    pass
        

class Changer(BoxLayout):
    def __init__(self, label = "label1", startval = -1, **kwargs):
        super(Changer, self).__init__(**kwargs)
        print(label)
        self.ids['l_val'].text = label
        self.name = label
        
        self.ids['b_val'].text = str(startval)
        VideoGen_params[label] = str(startval)
        self.value = str(startval)
        pass
        
    def press(self):
        print(self.value)
        
        
    def change_mode(self):
        print('modechange')
        pass
    pass


class TextEditor(BoxLayout):
    def __init__(self, **kwargs):
        super(TextEditor, self).__init__(**kwargs)
        self.tal_id = 0
        self.ids['bpan_id'].add_widget(Button(text = 'align', on_press = self.SetAlign))
        self.ids['bpan_id'].add_widget(Button(text = 'Rand', on_press = self.MergeAndRandomize))
        
    def MergeAndRandomize(self, instance):
        T = self.ids['t_id'].text
        T = T.split(' ')
        rate = 0.1
        for i,t in enumerate(T):
            if decision(rate):
                T[i] = '[b]'+T[i]+'[/b]'
        T = ''.join(T)
        self.ids['t_id'].text = T
        pass
        
    def SetAlign(self,instance):
        l = ['left','center','right']
        self.tal_id = self.tal_id+1 if self.tal_id < 2 else 0
        self.ids['t_id'].halign = l[self.tal_id]
    
    def SetBold(self):
        pass
    
    def SetItalic(self):
        pass

class StimGen(App):
    
    modes = ['Spiral','Text']
    currmode = 0
    
    def LoadGlobset(self):
        self.g_lay = BoxLayout(orientation = 'vertical', padding = 5, spacing = 5)
        
        self.b_lay = BoxLayout(spacing = 10)
        
        self.globset_lay = BoxLayout(orientation = 'vertical')
        
        s1 = Parameter(label = 'Name of file:', startval = 'G:/Main/AnacondaWF/NeuroLab/EyeTracker/generated_video')
        s2 = Parameter(label = 'Duration:', startval = 10)
        s3 = Parameter(label = 'Framerate:', startval = 60)
        s4 = Parameter(label = 'Width:', startval = 1366)
        s5 = Parameter(label = 'Heigth:', startval = 768)
        self.bmode = Changer(label = 'Mode:', startval = 'Spiral')
        self.bmode.ids['b_val'].on_press = self.ChangeMode;
        
        self.globset_lay.add_widget(s1)
        self.globset_lay.add_widget(s2)
        self.globset_lay.add_widget(s3)
        self.globset_lay.add_widget(s4)
        self.globset_lay.add_widget(s5)
        self.globset_lay.add_widget(self.bmode)
        
        
        
    def LoadControlPanel(self):
        self.control_lay = BoxLayout(orientation = 'vertical')
        b1 = Button(text = 'Generate video', on_press = self.GenVideo)
        b2 = Button(text = 'Play video', on_press = self.PlayVideo)
        b3 = Button(text = 'Quit')
        self.control_lay.add_widget(b1)
        self.control_lay.add_widget(b2)
        self.control_lay.add_widget(b3)
        
        
    def LoadVideosetSpiral(self):
        self.videoset_lay.clear_widgets()
        self.video_lay.clear_widgets()
        
        
        s2 = Parameter(label = 'Start radius:', startval = 100)
        s3 = Parameter(label = 'dR:', startval = 0)
        s4 = Parameter(label = 'dphi:', startval = 5)
        
        self.videoset_lay.add_widget(s2)
        self.videoset_lay.add_widget(s3)
        self.videoset_lay.add_widget(s4)
        
        
    def LoadVideoText(self):
        self.videoset_lay.clear_widgets()
        self.video_lay.clear_widgets()
        
        
        p = TextEditor()
    
        self.video_lay.add_widget(p)
        
        #TextEditor = TextInput()
        
        
        #self.video_lay.add_widget(TextEditor)
        #self.video_lay.add_widget(Label(text = TextEditor.text))
        
        
        
    def build(self):
        self.videoset_lay = BoxLayout(orientation = 'vertical')
        self.video_lay = AnchorLayout()
        self.LoadGlobset()
        self.LoadControlPanel()
        self.LoadVideosetSpiral()
        
        self.b_lay.add_widget(self.globset_lay)
        self.b_lay.add_widget(self.videoset_lay)
        self.b_lay.add_widget(self.control_lay)
        
        
        self.g_lay.add_widget(self.video_lay)
        self.g_lay.add_widget(self.b_lay)
        
        return self.g_lay
    
    def GenVideo(self, instance):
        name = VideoGen_params['Name of file:']
        time = int(VideoGen_params['Duration:'])
        fps = int(VideoGen_params['Framerate:'])
        width = int(VideoGen_params['Width:'])
        heigth = int(VideoGen_params['Heigth:'])
        
        sR = int(VideoGen_params['Start radius:'])
        dR = int(VideoGen_params['dR:'])
        dPh = int(VideoGen_params['dphi:'])
        
        for k in VideoGen_params:
            print(k, VideoGen_params[k])
            
        GenerateVideo(name, time, width, heigth, fps, sR, dR, dPh)
        
    def PlayVideo(self,instance):
        self.video_lay.clear_widgets()
        self.video_lay.add_widget(video)
        video.state = 'stop'
        video.source = VideoGen_params['Name of file:']+'.mp4'
        video.state = 'play'
        
        
    def ChangeMode(self):
        self.currmode = self.currmode = self.currmode+1 if self.currmode < len(self.modes)-1 else 0
        self.bmode.ids['b_val'].text = self.modes[self.currmode]
        
        if self.currmode == 0:
            self.LoadVideosetSpiral()
            
        else:
            self.LoadVideoText()
            
if __name__ == '__main__':
    StimGen().run()