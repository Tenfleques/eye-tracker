import os
import sys
from ctypes import cdll

lib = cdll.LoadLibrary('./winservice/bin/x64/cs_sample_streams.dll')

lib.cs_sample_streams()