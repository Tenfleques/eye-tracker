import os
import sys
from ctypes import cdll, c_double, c_bool, c_int, Structure, POINTER
from numpy.ctypeslib import ndpointer
from helpers import props
import time
import numpy as np


class Record(Structure):
    _fields_ = [('x', c_double),
            ('y', c_double),
            ('timestamp', c_double),
            ('engineTimestamp', c_double),
            ('valid', c_bool)
        ]

path = "C:\\Users\\tendai\\source\\repos\\TobiiEyeLib\\x64\\Debug\\TobiiEyeLib.dll"
lib = cdll.LoadLibrary(path)

lib.stop.restype = c_int

lib.getLatest.restype = POINTER(Record)

print(lib.start())
i = 0
while i < 4:
    output = lib.getLatest()
    print(output[0].x, output[0].y, output[0].valid, output[0].timestamp)
    time.sleep(1)
    i += 1

print(lib.stop())
