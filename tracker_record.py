from ctypes import cdll, c_float, c_bool, c_double, c_int, c_int64, Structure, POINTER
from eye_utilities.helpers import props
import time
import json

class Point2D(Structure): 
    _fields_ = [('x', c_float), ('y', c_float)]
    @classmethod
    def from_param(cls, self):
        if not isinstance(self, cls):
            raise TypeError
        return self
    

class Point3D(Point2D):
    _fields_ = [('z', c_float)]
    @classmethod
    def from_param(cls, self):
        if not isinstance(self, cls):
            raise TypeError
        return self

class Eye(Structure):
    _fields_ = [('left', Point3D), ('right', Point3D)]
    @classmethod
    def from_param(cls, self):
        if not isinstance(self, cls):
            raise TypeError
        return self

class Record(Structure):
    _fields_ = [('gaze', Point2D), 
        ('origin', Eye), ('pos', Eye),
        ('gaze_timestamp_us', c_int64), ('origin_timestamp_us', c_int64), 
        ('pos_timestamp_us', c_int64), ('sys_clock', c_double),
        ('gaze_valid', c_bool), ('pos_valid', c_bool), ('origin_valid', c_bool)]

    def toDict(self):
        return {
            "gaze" : {
                "x" : self.gaze.x,
                "y" : self.gaze.y,
                "timestamp" : self.gaze_timestamp_us,
                "valid" : self.gaze_valid
            },
            "pos" : {
                "left" : {
                    "x" : self.pos.left.x,
                    "y" : self.pos.left.y,
                    "z" : self.pos.left.z
                },
                "right" : {
                    "x" : self.pos.right.x,
                    "y" : self.pos.right.y,
                    "z" : self.pos.right.z   
                },
                "timestamp" : self.pos_timestamp_us,
                "valid" : self.pos_valid
            },
            "origin" : {
                "left" : {
                    "x" : self.origin.left.x,
                    "y" : self.origin.left.y,
                    "z" : self.origin.left.z
                },
                "right" : {
                    "x" : self.origin.right.x,
                    "y" : self.origin.right.y,
                    "z" : self.origin.right.z   
                },
                "timestamp" : self.origin_timestamp_us,
                "valid" : self.origin_valid
            },
            "timestamp" : self.sys_clock
        }
    def toString(self):
        message = '''gaze: \t   {}, {}, {}, {},\n origin: \t {}, {}, {}, {}, {},{}, {}, {},\n pos: \t    {}, {}, {}, {}, {}, {}, {}, {} \n clock {}, pyclock {}
                    '''.format(self.gaze.x, self.gaze.y, self.gaze_timestamp_us, self.gaze_valid,
                    
                    self.origin.left.x, self.origin.left.y, self.origin.left.z, 
                    self.origin.right.x, self.origin.right.y, self.origin.right.z, 
                    self.origin_timestamp_us, self.origin_valid,

                    self.pos.left.x, self.pos.left.y, self.pos.left.z, 
                    self.pos.right.x, self.pos.right.y, self.pos.right.z, 
                    self.pos_timestamp_us, self.pos_valid,
                    self.sys_clock, time.time()
                    )
        return message
    
    def csvString(self, frame_id, tm, diff):
        message = '''{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{}'''.format(frame_id, tm, 
        self.gaze.x, self.gaze.y, self.gaze_valid,
                    
        self.origin.left.x, self.origin.left.y, self.origin.left.z, 
        self.origin.right.x, self.origin.right.y, self.origin.right.z, self.origin_valid,

        self.pos.left.x, self.pos.left.y, self.pos.left.z, 
        self.pos.right.x, self.pos.right.y, self.pos.right.z, self.pos_valid, diff)
        return message

if __name__ == "__main__":
    tobii_dll_path = "TobiiEyeLib\\x64\\Debug\\TobiiEyeLib.dll"
    lib = cdll.LoadLibrary(tobii_dll_path)

    lib.stop.restype = c_int
    lib.start.restype = c_int
    lib.getLatest.restype = POINTER(Record)

    lib.start()
    i = 0
    while i < 3:
        output = lib.getLatest()
        print(output[0].toString())
        time.sleep(1)
        i += 1

    print(lib.stop())
