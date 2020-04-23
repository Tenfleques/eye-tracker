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

from  video_gen_kivy import *
from query_set_kivy import *

from pathlib import Path
PATH = str(Path(__file__).parent.absolute()).replace('\\','/')+'/'
print("current dir:", PATH)

class StarMenu(Screen):
    def __init__(self, **kwargs):
        super(StarMenu, self).__init__(**kwargs)
        blay = BoxLayout(orientation = 'vertical')
        blay.add_widget(Button(text = 'Video generation', on_press = self.TurnVideoGen))
        blay.add_widget(Button(text = 'Stimulus setup', on_press = self.TurnQuerySet))
        blay.add_widget(Button(text = 'Result analysis'))
        
        self.add_widget(blay)
    
    def TurnVideoGen(self, instance):
        sm.current = 'videogen'
    def TurnQuerySet(self, instance):
        sm.current = 'qset'

class StimulusSetup(Screen):
    pass

class ResultAnalysis(Screen):
    pass


sm = ScreenManager()


class StimGen(App):
    def build(self):
        men = StarMenu(name = 'menu')
        vid = VideoGenerator(name='videogen')
        qset = QuerySet(name = 'qset')
        sm.add_widget(men)
        sm.add_widget(vid)
        sm.add_widget(qset)
        #s2 = Parameter(label = 'Start radius:', startval = 100)
        return sm
    
            
if __name__ == '__main__':
    StimGen().run()