import os
import sys
from ctypes import cdll, c_double, c_float
from numpy.ctypeslib import ndpointer
from helpers import props
import time

path = "C:\\Users\\tendai\\source\\repos\\TobiiEyeLib\\x64\\Debug\\TobiiEyeLib.dll"
lib = cdll.LoadLibrary(path)

lib.getLatest.restype = ndpointer(dtype=c_double, shape=(10, 4))

print(lib.start())
i = 0
while i < 4:
    output = lib.getLatest()
    print(output[0])
    time.sleep(5)
    i += 1

print(lib.stop())
