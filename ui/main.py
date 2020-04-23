#!/usr/bin/python
from kivy.app import App
from kivy.lang import Builder 

import os
import time
import threading 
from threading import Thread, current_thread
import sys

# Builder.load_file('components/filebrowser.kv') 
# Builder.load_file('components\infobar.kv')

class Tracker(App):
    pass
    # def build(self):
    #     return self

    # def on_stop():
    #     pass

if __name__ == '__main__':
    tracker = Tracker()
    tracker.run()

