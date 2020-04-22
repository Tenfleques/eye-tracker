import cv2
import time
import threading
import os
import sys
from ctypes import cdll, c_int, POINTER
from tracker_record import Record
import json
from PIL import ImageGrab
from collections import deque
import numpy as np



class Synced:    
    cam_feed = None # cam feed thread
    cam_cap = None # cam feed capture object 
    cam_fps = None # frame rate/second in use for the camera 
    
    video_feed = None # video feed thread
    vid_cap = None  # video feed capture object 
    vid_fps = None # video traverse capture rate
    
    stop_feed = False

    # fast appends, 0(1)
    FRAMES = {
        "video": deque(),
        "cam" : deque()
    }

    def __init__(self, 
                video_path,
                save_dir = "sample", 
                dll_path = "TobiiEyeLib\\x64\\Debug\\TobiiEyeLib.dll", 
                cam_index = 0, 
                poll_wait = 10):
        
        screen_grab = ImageGrab.grab()
        self.SCREEN_SIZE = screen_grab.size

        self.poll_wait = poll_wait
        self.tobii_lib = cdll.LoadLibrary(dll_path)
        self.save_dir = save_dir
        self.img_dir = save_dir
        self.cam_index = cam_index
        self.video_path = video_path

        self.tobii_lib.stop.restype = c_int
        self.tobii_lib.start.restype = c_int
        self.tobii_lib.getLatest.restype = POINTER(Record)

        self.video_name = "video"

        if video_path:
            self.video_name = video_path.split(os.sep)[-1]

    def log_frames(self):
        # index
        last_cam_frame = self.FRAMES["cam"]
        if len(last_cam_frame):
            last_cam_frame = last_cam_frame[-1]
            tracker = last_cam_frame["tracker"]
            tm = last_cam_frame["time"]
            gaze_time = tracker["timestamp"]

            print("gaze_time: {}, time: {}, acc: {} \n gaze: {}\n\n".format(gaze_time, tm, abs(gaze_time - tm), tracker["gaze"]))

    def start(self, video_fps=None, cam_fps=None, cb=None):
        if not os.path.isfile(self.video_path):
            print("video file not found")
            return 

        self.cam_cap = cv2.VideoCapture(self.cam_index)
        self.vid_cap = cv2.VideoCapture(self.video_path)

        if video_fps:
            self.vid_fps = video_fps
        else:
            # set the video determined fps
            self.vid_fps = self.vid_cap.get(cv2.CAP_PROP_FPS)
        
        print("supplied fps: {}, used fps: {}".format(video_fps, self.vid_fps))

        if cam_fps:
            self.cam_fps = cam_fps
        else:
            # set the cam determined fps
            self.cam_fps = self.cam_cap.get(cv2.CAP_PROP_FPS)

        self.vid_feed = threading.Thread(target=self.frame_capture, 
                        args=(self.vid_cap, 
                                self.vid_processor, 
                                lambda : self.stop_feed,
                                "video"))

        self.cam_feed = threading.Thread(target=self.frame_capture, 
                        args=(self.cam_cap, 
                                self.cam_processor, 
                                lambda : self.stop_feed,
                                "cam"))
        
        try:
            self.img_dir = os.path.join(self.save_dir, "images")
            os.makedirs(self.img_dir, exist_ok=True)
            self.stop_feed = False
            # start the devices
            self.tobii_lib.start()
            self.cam_feed.start()
            self.vid_feed.start()
            
            while self.all_ready():
                if cb == None:
                    self.log_frames()
                else:
                    cb(self.FRAMES)
            
            self.stop_feed = True
            self.stop()
            # When ctrl+c is received
        except KeyboardInterrupt:
            self.stop()

    def replay(self, video_fps=None):
        if not os.path.isfile(self.video_path):
            print("video file not found")
            return 

        self.vid_cap = None
        self.vid_cap = cv2.VideoCapture(self.video_path)
        self.video_name = "replay: " + self.video_name

        if video_fps:
            self.vid_fps = video_fps
        else:
            # set the video determined fps
            self.vid_fps = self.vid_cap.get(cv2.CAP_PROP_FPS)

        self.vid_feed = threading.Thread(target=self.frame_capture, 
                        args=(self.vid_cap, 
                                self.vid_processor, 
                                lambda : self.stop_feed,
                                "replay",
                                True
                                ))
        
        try:
            self.stop_feed = False
            self.vid_feed.start()
            
            while self.vid_cap.isOpened():
                continue
            
            self.stop_feed = True

            if self.vid_feed.is_alive:
                self.vid_feed.join()
            # When ctrl+c is received
        except KeyboardInterrupt:
            if self.vid_feed.is_alive:
                self.vid_feed.join()

    def stop(self):
        self.stop_feed = True
        if self.cam_feed.is_alive:
            self.tobii_lib.stop()
            self.cam_feed.join()
        if self.vid_feed.is_alive:
            self.vid_feed.join()

        filename = os.path.join(self.save_dir, "results.json")
        with open(filename, "w") as f:
            res = {
                "video" : list(self.FRAMES["video"]),
                "cam" : list(self.FRAMES["cam"])
            }
            f.write(json.dumps(res))
            f.close()
        
        cv2.destroyAllWindows()

    def vid_processor(self, 
                        frame_id, frame, gaze, replay=False):
        
        cv2.namedWindow(self.video_name, cv2.WND_PROP_FULLSCREEN)
        cv2.setWindowProperty(self.video_name,cv2.WND_PROP_FULLSCREEN,cv2.WINDOW_FULLSCREEN)
        font = cv2.FONT_HERSHEY_PLAIN

        if not replay:
            self.FRAMES["video"].append({
                "frame" : frame_id,
                "time" : time.time(),
                "tracker" : gaze.toDict()
            })
        else:
            # it's replay time 
            x = self.SCREEN_SIZE[0] - 500
            frame = np.zeros(shape=(self.SCREEN_SIZE[1],self.SCREEN_SIZE[0], 3), dtype=np.uint8)
            frame[:,:,:] = 150

            if frame_id < len(self.FRAMES["video"]):
                cap_frame = self.FRAMES["video"][frame_id]
                tracker = cap_frame["tracker"]
                tm = cap_frame["time"]
                gaze_time = tracker["timestamp"]
                xyv = tracker["gaze"]

                details = "frame: {}, time diff {:.4}".format(frame_id, abs(gaze_time - tm))
                cv2.putText(frame, details, (x,40), font, 1.0, (200,20,20), 1, cv2.LINE_AA)

                details = "gaze: ({:.4},{:.4}), valid: {}".format(xyv["x"], xyv["y"], xyv["valid"])
                cv2.putText(frame, details, (x,90), font, 1.0, (200,20,20), 1, cv2.LINE_AA)
                
                if xyv["valid"]:
                    if 0.0 < xyv["x"] < 1.0 and 0.0 < xyv["y"] < 1.0:
                        x1 = int(self.SCREEN_SIZE[0] * xyv["x"]) - 5
                        y1 = int(self.SCREEN_SIZE[1] * xyv["y"]) - 5
                        box_w = 10
                        box_h = 10
                        cv2.rectangle(frame, (x1, y1), (x1+box_w, y1+box_h), (255,20,0), -1)

            else:
                details = "no gaze data for frame: {}".format(frame_id)
                cv2.putText(frame, details, (x,40), font, 1.0, (200,20,20), 1, cv2.LINE_AA)

        
        cv2.imshow(self.video_name, frame)
        waitms = 30
        if self.vid_fps:
            waitms = int(1000.0/self.vid_fps)
        return cv2.waitKey(waitms)

        
    def cam_processor(self, frame_id, frame, gaze, replay=False):
        if replay:
            return

        self.FRAMES["cam"].append({
                        "time" : time.time(),
                        "tracker" : gaze.toDict()
                    })
        image_path = os.path.join(self.img_dir, "frame-{}.png".format(frame_id))

        cv2.imwrite(image_path, frame)
        waitms = 30
        if self.cam_fps:
            waitms = int(1000.0/self.cam_fps)
        return cv2.waitKey(waitms)

    def all_ready(self):
        gaze = self.tobii_lib.getLatest()[0]
        if not self.cam_cap.isOpened():
            return False

        ret, _ = self.cam_cap.read()

        return self.vid_cap.isOpened() and ret and gaze.sys_clock

    def frame_capture(self, cap, cb, should_stop, name = "", replay=
     False):
        frame_id = 0
        st = time.time()
        
        if not replay:
            ready = False
            # wait for all to be ready for 10 seconds, longer than that give up
            for i in range(self.poll_wait):
                print("{} polling for other devices ... {}".format(name, i))
                sys.stdout.flush()
                if self.all_ready():
                    ready = True
                    break
                time.sleep(1)
        else:
            # replay mode, we are showing the user their recorded screen gaze
            ready = True 

        if not ready:
            print("got tired of waiting...")
            sys.stdout.flush()
            return

        while cap.isOpened():
            if should_stop():
                break
            # checks all ready only in recording mode
            if not replay:
                if not self.all_ready():
                    break

            ret, frame = cap.read()
            if not ret:
                break
            # get tobii position only if in recording mode
            key = None
            if not replay:
                gaze = self.tobii_lib.getLatest()[0]
                if gaze.sys_clock:
                    key = cb(frame_id, frame, gaze, replay)
            else:
                key = cb(frame_id, frame, None, replay)
            
            if key == ord('Q') or key == ord('q'):
                break
            frame_id += 1

        # if any video thread is finished close
        cap.release()
        if time.time() - st:
            factual_rate = frame_id/(time.time() - st)
            print("{}: factual rate used: {}".format(name, factual_rate))
            sys.stdout.flush()
        
def silent_cb(x):
    pass

if __name__ == "__main__":
    synced = Synced("data\\stimulus_sample.mp4")
    synced.start(video_fps=1000, cb= silent_cb)
    print("start replay")
    synced.replay(video_fps=1000)