# this file is to be copied to the ~./talon/user directory to monitor the gaze 

from talon import ctrl, tap, ui
from talon_plugins.eye_mouse import tracker, mouse
from talon.track.geom import Point2d, Point3d, EyeFrame

import time
import os

import glob
import logging
import logging.handlers

main = ui.main_screen()

def is_on_main(p):
    return (main.x <= p.x < main.x + main.width and
            main.y <= p.y < main.y + main.height)

class MonSnap:
    def __init__(self):
        tap.register(tap.MMOVE, self.on_move)
        tracker.register('gaze', self.on_gaze)

        self.gaze_logger = logging.getLogger('gaze_logger')
        self.gaze_logger.setLevel(logging.INFO)

        socketHandler = logging.handlers.SocketHandler('localhost',
                    logging.handlers.DEFAULT_TCP_LOGGING_PORT)

        self.gaze_logger.addHandler(socketHandler)

        self.saved_mouse = None
        self.main_mouse = False
        self.main_gaze = False
        self.restore_counter = 0

        os.makedirs("./logs", exist_ok=True)

    def logPieces(self,m):
        """Used to check contents of a variable in the test.log files """
        with open("test.log", "w") as f:
            f.write(m)
            f.close()

    def on_gaze(self, b):
        l, r = EyeFrame(b, 'Left'), EyeFrame(b, 'Right')

        p = (l.gaze + r.gaze) / 2
        main_gaze = -0.02 < p.x < 1.02 and -0.02 < p.y < 1.02 and bool(l or r)

        message = '''{},
                    {},{},
                    {},{},
                    {},{},{},
                    {},{},{},
                    {}'''.format(
                            time.strftime("%H:%M:%S"), 
                            l.gaze.x, l.gaze.y, 
                            r.gaze.x, r.gaze.y,
                            l.pos.x, l.pos.y, l.pos.z,
                            r.pos.x, r.pos.y, r.pos.z,
                            int(main_gaze))
                            
        message = "".join(message.split())
        self.logPieces(message)

        self.gaze_logger.info(message)

        if self.main_gaze and self.main_mouse and not main_gaze:
            self.restore_counter += 1
            if self.restore_counter > 5:
                self.restore()
        else:
            self.restore_counter = 0
            self.main_gaze = main_gaze

    def restore(self):
        if self.saved_mouse:
            mouse.last_ctrl = self.saved_mouse
            ctrl.mouse(self.saved_mouse.x, self.saved_mouse.y)
            self.saved_mouse = None
            self.main_gaze = False

    def on_move(self, typ, e):
        if typ != tap.MMOVE: return
        p = Point2d(e.x, e.y)
        on_main = is_on_main(p)
        if not on_main:
            self.saved_mouse = p
        self.main_mouse = on_main

# snap = MonSnap()
