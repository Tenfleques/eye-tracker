import time 
import locale 
import json
import math
import os
import copy 
import cv2


ERROR = 1
WARNING = 2
INFO = 3
LOCALE = {}
with open("_locale.json", "r", encoding="utf8") as f:
    LOCALE = json.load(f)

LOCALE["__empty"] = {
    "ru" : "",
    "en" : ""
}

timestamp = lambda x : time.mktime(time.strptime(x[0], "%H:%M:%S")) + float("0." + x[1])

def loadService():
  TALON_HOME = os.path.expanduser("~/.talon/user")
  filename = os.path.join(TALON_HOME, "launcher.py")

  launcher_exists = os.path.exists(filename)
  launcher_isfile = os.path.isfile(filename)

  if not (launcher_exists and launcher_isfile):
    with open("./launcher.py", 'r') as src, open(filename, 'w') as dst: 
      dst.write(src.read())
      
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

        return key

def previewQueues(gazes, ctrl_timestamp):
  import pandas as pd
  df_series = {
    "gazes":  [str(x.split(",")[0]) for x in gazes],
    "capture time" : [str(ctrl_timestamp) for i in gazes]
  }
  df = pd.DataFrame(df_series)
  print(df.tail(30))

def findClosestGazeFrame(gazes, frame_id, tm):
  gaze = gazes[0]
  # previewQueues(gazes, tm)  
  
  diff = 0.0

  diff = math.fabs(tm - gaze.sys_clock)
  for i in range(1,len(gazes)):
    if gazes[i].sys_clock:
      pt_diff = math.fabs(tm - gazes[i].sys_clock)
      
      if pt_diff < diff:
        diff = pt_diff
        gaze = gazes[i]
        
  result = {
    "log" : "frame {}: \t ({:.4},{:.4}), \t acc: {:.4}\n\n".format(frame_id, gaze.gaze.x, gaze.gaze.y, diff),
    "gaze" : gaze.csvString(frame_id, tm, diff)
  }
  return result

def getCSVHeaders():
      return '"frame","timestamp","gaze_x","gaze_y","valid_gaze","origin_left_x","origin_left_y","origin_left_z","origin_right_x","origin_right_y","origin_right_z", "valid_origin","pos_left_x","pos_left_y","pos_left_z","pos_right_x","pos_right_y","pos_right_z","valid_pos","acc/s","video" \n'

def createlog(text, logtype = INFO):
  str_logtype = {
      INFO : "INFO",
      ERROR : "ERROR",
      WARNING: "WARNING"
  }
  # timestr = time.strftime("%Y/%m/%d %H:%M:%S")
  log = ""
  if text:
    log = "{}: {}".format(str_logtype.get(logtype, INFO), text)
  return log

def getSessionName():
  return "ets-{}".format(time.strftime("%m_%d_%H_%M_%S"))

def getVideoFPS(path):
  if not os.path.isfile(path):
    return 0

  video = cv2.VideoCapture(path)
  fps = video.get(cv2.CAP_PROP_FPS)
  video.release()
  return fps

def playVideo(path, cb, fps = 29.9):
  sec = 0.0
  cap = cv2.VideoCapture(path)
  delta_time_between_frames = 1/fps
  
  index = 0
  while(cap.isOpened()):
    cap.set(cv2.CAP_PROP_POS_MSEC, sec*1000)
    ret, frame = cap.read()
    if not ret:
      break
    cv2.namedWindow('stimuli video', cv2.WINDOW_FREERATIO)
    # cv2.setWindowProperty('stimuli video', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    cv2.imshow('stimuli video',frame)
    cb(sec)
    index += 1
    sec += delta_time_between_frames

  cap.release()
  cv2.destroyAllWindows()

# if __name__ == "__main__":
#     loadService()
