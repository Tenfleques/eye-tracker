import time 
import locale 
import json

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

def parseGazeLog(record):
  """decodes the record in the socket to dict"""
  keys = [
      {"time": "time"},
      {"gaze" : [
          {"left" : ["x", "y"]},
          {"right" : ["x", "y"]},
        ],
      },
      {"pos" : [
          {"left" : ["x", "y", "z"]},
          {"right" : ["x", "y", "z"]},
        ],
      },
      {"flag" : "is_main_gaze"}
  ]
  return
  
def findClosestGazeFrame(gazes, frames, time):
  pass

def createlog(text, logtype = INFO):
  str_logtype = {
      INFO : "INFO",
      ERROR : "ERROR",
      WARNING: "WARNING"
  }
  timestr = time.strftime("%Y/%m/%d %H:%M:%S")
  
  log = "{}: {}".format(str_logtype.get(logtype, INFO), text)
  return log