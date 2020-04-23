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
VideoGen_params = {}

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

class IdentMenu(Screen):
    def __init__(self, **kwargs):
        super(IdentMenu, self).__init__(**kwargs)
        blay = BoxLayout(orientation = 'vertical')
        blay.add_widget(Parameter(label = 'Name:', startval = ""))
        blay.add_widget(Parameter(label = 'Surname:', startval = ""))
        blay.add_widget(Parameter(label = 'Age:', startval = ""))
        
        blay2 = BoxLayout()
        blay2.add_widget(Button(text = 'Return', on_press = self.Return))
        blay2.add_widget(Button(text = 'Login'))
        blay.add_widget(blay2)
        self.add_widget(blay)
        
    def Return(self,instance):
        self.parent.current = 'menu'
        