import time 
import locale 
import json
import math

ERROR = 1
WARNING = 2
INFO = 3
LOCALE = {}
with open("_locale.json", "r") as f:
    LOCALE = json.load(f)

LOCALE["__empty"] = {
    "ru" : "",
    "en" : ""
}


def props(cls):   
  return [i for i in cls.__dict__.keys() if i[:1] != '_']

def get_local_str(key):
        lang = "ru"
        local_def = locale.getdefaultlocale()
        if len(local_def) and local_def[0]:
           sys_locale = local_def[0].split("_")[0]
           if sys_locale in ["en", "ru"]:
               lang = sys_locale
        
        if key in LOCALE:
            return LOCALE.get(key)[lang]

        return LOCALE["__empty"][lang]


def findClosestGazeFrame(gazes, tm, nano):
  
  gaze = gazes[0].split(",")

  timestamp = lambda x : time.mktime(time.strptime(x[0], "%H:%M:%S")) + float("0." + x[1])

  ctrl_timestamp = time.mktime(time.strptime(tm, "%H:%M:%S")) + nano/100.0
  
  if gaze[0]:
    diff = math.fabs(ctrl_timestamp - timestamp(gaze))

    for i in range(1,len(gazes)):
      if gazes[i][0]:
        arr = gazes[i].split(",")
        ts = timestamp(arr)
        pt_diff = math.fabs(ctrl_timestamp - ts)
        if pt_diff < diff:
          diff = pt_diff
          gaze = arr

  str_gaze = gaze[:-1].copy()
  str_gaze[0] = "\"" + str_gaze[0] + "\""

  for i in range(2,12):
    gaze[i]=float(gaze[i])

  filename = "capture-{}.png".format("-".join(tm.split(":")))

  result = {
    "log" : "time: {} gaze nano: {}, ({:.2},{:.2}), ({:.2}, {:.2})\n\n".format(tm, gaze[1], gaze[2], gaze[3], gaze[4], gaze[5]),
    "gaze" : ",".join(str_gaze) + ",\"" + filename + "\"\n",
    "filename": filename
  }
  return result

def getCSVHeaders():
      return '''"time","nano_sec","gaze_left_x", "gaze_left_y", "gaze_right_x", "gaze_right_y","pos_left_x", "pos_left_y", "pos_left_z","pos_right_x","pos_right_y", "pos_right_z","is_main_gaze", "image" \n'''

def createlog(text, logtype = INFO):
  str_logtype = {
      INFO : "INFO",
      ERROR : "ERROR",
      WARNING: "WARNING"
  }
  # timestr = time.strftime("%Y/%m/%d %H:%M:%S")
  log = "{}: {}".format(str_logtype.get(logtype, INFO), text)
  return log

def getSessionName():
  return "ets-{}".format(time.strftime("%m_%d_%H_%M_%S"))
