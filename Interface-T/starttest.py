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
from kivy.core.window import Window

from pathlib import Path
PATH = str(Path(__file__).parent.absolute()).replace('\\','/')+'/'
print("current dir:", PATH)

class Menu(BoxLayout):
    def __init__(self, **kwargs):
        super(Menu, self).__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint = [0.2, 0.2]
        self.add_widget(Button(text = 'Launch', on_press = self.launchplay))
        self.add_widget(Button(text = 'Return', on_press = self.Return))
        
    def launchplay(self, instance):
        print('l1')
        self.parent.parent.launchplay()
        
    def Return(self, instance):
        self.parent.parent.parent.current = 'menu'


class StarTestMenu(Screen):
    
    
    def __init__(self, **kwargs):
        super(StarTestMenu, self).__init__(**kwargs)
        self.video = Video()
        self.anch = AnchorLayout()
        self.contol = Menu()
        self.anch.add_widget(self.contol)
        
        self.add_widget(self.anch)
        
        
        
    def launchplay(self):
        print('l2')
        self.anch.clear_widgets()
        self.anch.add_widget(self.video)
        self.video.source = PATH+'gen_video2.mp4'
        self.video.state = 'play'