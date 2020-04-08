#!/usr/bin/python
from kivy.app import App
from kivy.properties import ObjectProperty

from kivy.factory import Factory
from kivy.uix.popup import Popup


import locale

import os
import json
from collections import deque
import time 
from threading import Thread, current_thread
import sys

from root import Root, LoadDialog

from kivy.core.window import Window
import time

Window.clearcolor = (1, 1, 1, 1)


class Tracker(App):
    pass


Factory.register('Root', cls=Root)
Factory.register('LoadDialog', cls=LoadDialog)

if __name__ == '__main__':
    Tracker().run()
