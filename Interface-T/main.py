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
Window.fullscreen = False
Config.set('graphics', 'fullscreen', 'false')
Config.set('graphics', 'width', 1367)
Config.set('graphics', 'height', 678)
Config.write()

from ident import *
from starttest import *
import random




#from  video_gen_kivy import *
#from query_set_kivy import *

from pathlib import Path
PATH = str(Path(__file__).parent.absolute()).replace('\\','/')+'/'
print("current dir:", PATH)

class StarMenu(Screen):
    def __init__(self, **kwargs):
        super(StarMenu, self).__init__(**kwargs)
        blay = BoxLayout(orientation = 'vertical')
        blay.add_widget(Button(text = 'Identification', on_press = self.TurnIndentification))
        blay.add_widget(Button(text = 'Launch test', on_press = self.TurnTest))
        blay.add_widget(Button(text = 'Settings(admin only)', on_press = self.TurnSet))
        
        self.add_widget(blay)
    
    def TurnIndentification(self, instance):
        sm.current = 'Identification'
    def TurnTest(self, instance):
        sm.current = 'Launch'
    def TurnSet(self, instance):
        sm.current = 'Settings'

sm = ScreenManager()


class InterT(App):
    def build(self):
        self.ID = -1
        men = StarMenu(name = 'menu')
        idt = IdentMenu(name = 'Identification')
        stt = StarTestMenu(name = 'Launch')
        sm.add_widget(men)
        sm.add_widget(idt)
        sm.add_widget(stt)
        return sm
    
            
if __name__ == '__main__':
    InterT().run()