import time 

ERROR = 1
WARNING = 2
INFO = 3

def props(cls):   
  return [i for i in cls.__dict__.keys() if i[:1] != '_']

def createlog(text, logtype = INFO):
  str_logtype = {
      INFO : "INFO",
      ERROR : "ERROR",
      WARNING: "WARNING"
  }
  timestr = time.strftime("%Y/%m/%d %H:%M:%S")
  
  log = "{}\t {} \n {} \n".format(str_logtype.get(logtype, INFO), timestr, text)
  return log