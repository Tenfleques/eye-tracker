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
from kivy.uix.popup import Popup
from VideoGenerator import *
import random
from pathlib import Path
from os import path

PATH = str(Path(__file__).parent.absolute()).replace('\\','/')+'/'
video = Video()
def decision(probability):
    return random.random() < probability

class Parameter(BoxLayout):
    def __init__(self, label = "label1", startval = -1, **kwargs):
        super(Parameter, self).__init__(**kwargs)
        print(label)
        self.ids['l_val'].text = label
        self.name = label
        
        self.ids['t_val'].text = str(startval)
        #self.parent.ValueDict[label] = str(startval)
        self.value = str(startval)
        pass
        
    def press(self):
        print(self.value)
        
        
    def change_text(self):
        key = self.name
        value = self.value
        print(key, value)
        self.parent.ValueDict[key] = value
        pass
    pass
        

class Changer(BoxLayout):
    def __init__(self, label = "label1", startval = -1, **kwargs):
        super(Changer, self).__init__(**kwargs)
        print(label)
        self.ids['l_val'].text = label
        self.name = label
        
        self.ids['b_val'].text = str(startval)
        self.parent.ValueDict[label] = str(startval)
        self.value = str(startval)
        pass
        
    def press(self):
        print(self.value)
        
        
    def change_mode(self):
        print('modechange')
        pass
    pass


class SettingBox(BoxLayout):
    ValueDict = {}
    def __init__(self, label = "label1", startval = -1, **kwargs):
        super(SettingBox, self).__init__(**kwargs)
        
    def update(self):
        for i, l in enumerate(self.children):
            if type(l) is Parameter:
                self.children[i].change_text()

class TrajEditor(BoxLayout):
    def __init__(self, **kwargs):
        super(TrajEditor, self).__init__(**kwargs)
        self.orientation = 'vertical'
        self.video_lay = AnchorLayout()
        
        self.params = SettingBox()
        
        s2 = Parameter(label = 'Start radius:', startval = 100)
        s3 = Parameter(label = 'dR:', startval = 0)
        s4 = Parameter(label = 'dphi:', startval = 36)
        
      
        self.params.add_widget(s2)
        self.params.add_widget(s3)
        self.params.add_widget(s4)
       
        s2.change_text()
        s3.change_text()
        s4.change_text()
        
        self.params.add_widget(Button(text = 'generate', on_press = self.GenVideo))
        
        self.add_widget(self.video_lay)
        self.add_widget(self.params)

    def GenVideo(self, instance):
        name = self.parent.parent.parent.b_lay.ValueDict['Name of file:']
        
        time = int(GlobVideoSet.ValueDict['Duration:'])
        fps = int(GlobVideoSet.ValueDict['Framerate:'])
        width = int(GlobVideoSet.ValueDict['Width:'])
        heigth = int(GlobVideoSet.ValueDict['Heigth:'])
        
        sR = int(self.params.ValueDict['Start radius:'])
        dR = int(self.params.ValueDict['dR:'])
        dPh = int(self.params.ValueDict['dphi:'])
        
        print(sR, dR, dPh)
        GenerateVideo(name, time, width, heigth, fps, sR, dR, dPh)


GlobVideoSet = SettingBox(orientation = 'vertical');
def InitGlobSet():
    s2 = Parameter(label = 'Duration:', startval = 10)
    s3 = Parameter(label = 'Framerate:', startval = 60)
    s4 = Parameter(label = 'Width:', startval = 1366)
    s5 = Parameter(label = 'Heigth:', startval = 768)
        
    GlobVideoSet.add_widget(s2)
    GlobVideoSet.add_widget(s3)
    GlobVideoSet.add_widget(s4)
    GlobVideoSet.add_widget(s5)
      
    s2.change_text()
    s3.change_text()
    s4.change_text()
    s5.change_text()



class MyPopUp(Popup):
    def __init__(self, **kwargs):
        super(MyPopUp, self).__init__(**kwargs)
        b = BoxLayout(orientation = 'vertical')
        self.add_widget(b)
        b.add_widget(GlobVideoSet)
        b.add_widget(Button(text = 'close', on_press = self.close))
        
    def close(self, instance):
        
        self.dismiss()
        
class MyPopPlayer(Popup):
    def __init__(self, **kwargs):
        super(MyPopPlayer, self).__init__(**kwargs)
        b = BoxLayout(orientation = 'vertical')
        b.add_widget(video)
        b.add_widget(Button(text = 'close', size_hint = (1.0, 0.05), on_press = self.dismiss))
        self.add_widget(b)
    
    
    
class VideoGenerator(Screen):
    modes = ['Spiral','Text']
    currmode = 0
    setting_box = MyPopUp(size=(400, 400));
    video_fs_box = MyPopPlayer()
    def LoadVideoText(self):
        self.video_lay.clear_widgets()
        p = TextEditor()
        self.video_lay.add_widget(p)
        
        
    def LoadVideoSpiral(self):
        self.video_lay.clear_widgets()
        p = TrajEditor()
        self.video_lay.add_widget(p)

        
        
    def __init__(self, **kwargs):
        super(VideoGenerator, self).__init__(**kwargs)
        InitGlobSet()
        self.g_lay = BoxLayout(orientation = 'vertical', padding = 5, spacing = 5)
        self.b_lay = SettingBox(spacing = 10,size_hint = (1.0, 0.1))
        
        
        
        self.video_lay = AnchorLayout()
        
        self.g_lay.add_widget(self.video_lay)
        self.g_lay.add_widget(self.b_lay)
        
        s2 = Parameter(label = 'Name of file:', startval = 'gen_video2')
        
        self.b_lay.add_widget(s2)
        self.b_lay.add_widget(Button(text = 'settings', on_press = self.GSettings))
        self.modechanger = Button(text = 'mode', on_press = self.ChangeMode)
        self.b_lay.add_widget(self.modechanger)
        self.b_lay.add_widget(Button(text = 'Play', on_press = self.Play))
        self.b_lay.add_widget(Button(text = 'Upload', on_press = self.Upload))
        self.b_lay.add_widget(Button(text = 'return', on_press = self.Return))
        s2.change_text()
        self.add_widget(self.g_lay)
        self.LoadVideoSpiral()
        

    def ChangeMode(self, instance):
        self.currmode = self.currmode = self.currmode+1 if self.currmode < len(self.modes)-1 else 0
        self.modechanger.text = self.modes[self.currmode]
        
        print("Current mode:", self.modes[self.currmode])
        if self.currmode == 0:
            pass
            self.LoadVideoSpiral()
            
        else:
            pass
            self.LoadVideoText()
         
            
    def Upload(self, instance):
        pass
    
    def Play(self, instance):
        self.b_lay.update()
        name = PATH+self.b_lay.ValueDict['Name of file:']+'.mp4'
        width = int(GlobVideoSet.ValueDict['Width:'])
        heigth = int(GlobVideoSet.ValueDict['Heigth:'])
        
        if path.exists(name):
            video.state = 'stop'
            self.video_fs_box.size = (width,heigth)
            self.video_fs_box.open()
            video.source = name
            video.state = 'play'
        else:
            pp = Popup(title='Error!')
            bb = Button(text='No such file!', on_press = pp.dismiss)
            pp.add_widget(bb)
            pp.open()
    def GSettings(self,instance):
        self.setting_box.open()
        
            
    def Return(self,instance):
        self.parent.current = 'menu'
            

class TextEditor(BoxLayout):
    def __init__(self, **kwargs):
        super(TextEditor, self).__init__(**kwargs)
        self.tal_id = 0
        

        
        self.ids['bpan_id'].add_widget(Button(text = 'Save', on_press = self.SaveVideo))
        self.ids['bpan_id'].add_widget(Button(text = 'align', on_press = self.SetAlign))
        self.ids['bpan_id'].add_widget(Button(text = 'Rand', on_press = self.MergeAndRandomize))
        
    def SaveVideo(self, instance):
        
        name = VideoGen_params['Name of file:']
        time = int(VideoGen_params['Duration:'])
        fps = int(VideoGen_params['Framerate:'])
        FullPath = PATH+name+'.png'
        print(FullPath)
        self.ids['l_id'].export_to_png(PATH+name+'.png')
        
        
        GenerateVideoText(PATH+name, time, fps, PATH+name+'.png')
        
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