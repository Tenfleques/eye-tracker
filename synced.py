import cv2
import time
import matplotlib
import matplotlib.pyplot as plt
import os
import sys
from ctypes import cdll, c_int, POINTER
from tracker_record import Record
import json
from PIL import ImageGrab
from collections import deque
import numpy as np
import io
import threading


class DummyTobii:
    take_shots = False
    cam_shot = None
    cap = None
    records = deque()
    frame = None

    def start(self, cam_index= 0):
        self.records.append(Record())
        self.cap = cv2.VideoCapture(cam_index)
        cam_thread = threading.Thread(target=self.cam_shots)
        try:
            cam_thread.start()

        except KeyboardInterrupt:
            cam_thread.join()
            self.cap.release()

    def cam_shots(self):
        while self.take_shots and self.cap.isOpened():
            ret, self.frame = self.cap.read()
            r = np
            self.records.append(Record())

    def stop(self):
        if self.cap.isOpened():
            self.cap.release()

    def get_latest(self, index=0):
        return [self.records[index]]


def get_img_from_fig(fig, dpi=100):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi)
    buf.seek(0)
    img_arr = np.frombuffer(buf.getvalue(), dtype=np.uint8)
    buf.close()
    img = cv2.imdecode(img_arr, 1)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    return img


class Synced:
    stop_feed = False

    # fast appends, 0(1)
    FRAMES = deque()

    def __init__(self, video_path, save_dir="sample",
                 dll_path="TobiiEyeLib/x64/Debug/TobiiEyeLib.dll",
                 cam_index=0, poll_wait=10, bg_color=(255, 255, 255), fore_color=(200, 200, 0)):

        screen_grab = ImageGrab.grab()
        self.SCREEN_SIZE = screen_grab.size
        self.bg_frame = np.zeros(shape=(self.SCREEN_SIZE[1], self.SCREEN_SIZE[0], 3), dtype=np.uint8)
        self.bg_color = bg_color
        self.fore_color = fore_color
        self.calc_fps = 0.0
        self.record_fps = 0.0

        self.poll_wait = poll_wait
        self.details_log = deque(maxlen=(self.SCREEN_SIZE[1] - 460) // 70)
        self.metrics = {
            "mean": .0,
            "min": .0,
            "max": .0
        }

        try:
            self.tobii_lib = cdll.LoadLibrary(dll_path)
            self.tobii_lib.start.argtypes = [c_int]
            self.tobii_lib.stop.restype = c_int
            self.tobii_lib.start.restype = c_int
            self.tobii_lib.get_latest.restype = POINTER(Record)
        except OSError:
            print("os error")
            self.tobii_lib = DummyTobii()

        self.save_dir = save_dir
        self.img_dir = save_dir
        self.cam_index = cam_index
        self.video_path = video_path
        self.video_name = None

        self.cam_feed = None  # cam feed thread
        self.cam_cap = None  # cam feed capture object
        self.cam_fps = None  # frame rate/second in use for the camera

        self.vid_cap = None  # video feed capture object
        self.vid_fps = None  # video traverse capture rate

    def log_frames(self):
        # index
        last_cam_frame = self.FRAMES
        if len(last_cam_frame):
            last_cam_frame = last_cam_frame[-1]
            tracker = last_cam_frame["tracker"]
            tm = last_cam_frame["time"]
            gaze_time = tracker["timestamp"]

            print("gaze_time: {}, time: {}, acc: {} \n gaze: {}\n\n".format(gaze_time,
                                                                            tm, abs(gaze_time - tm), tracker["gaze"]))

    def set_metrics(self):
        ll = max(1000, len(self.FRAMES))
        times = np.zeros(ll)

        for (i, x) in enumerate(self.FRAMES):
            if x["tracker"]["gaze"]["valid"]:
                times[i] = abs(x["time"] - x["tracker"]["timestamp"])

        mn = times.min()
        mx = times.max()

        fig = plt.figure(figsize=(3, 5), dpi=200)
        ax = fig.subplots()
        ax.plot(times)
        ax.set(xlabel='frame (id)', ylabel='error (s)',
               title='time difference')
        ax.grid()
        chart = get_img_from_fig(fig, 200)

        chart = cv2.resize(chart, dsize=(500, 300), interpolation=cv2.INTER_CUBIC)
        x = self.SCREEN_SIZE[0] - 500
        y = 50

        self.bg_frame[:, :, :] = 255
        self.bg_frame[y:y+300, x:x+500, :] = chart

        self.metrics = {
            "mean": times.mean(),
            "min": mn,
            "max": mx
        }

    def start(self, video_fps=None, replay=False):
        if not os.path.isfile(self.video_path):
            print("the video file not found")
            return
        self.vid_cap = None
        self.vid_cap = cv2.VideoCapture(self.video_path)
        self.video_name = "replay: {}".format(self.video_path.split(os.sep)[-1])

        if video_fps:
            self.vid_fps = video_fps
        else:
            # set the video determined fps
            self.vid_fps = self.vid_cap.get(cv2.CAP_PROP_FPS)

        try:
            self.stop_feed = False
            if not replay:
                self.record_fps = self.vid_fps
                self.video_name = self.video_path.split(os.sep)[-1]
                self.img_dir = os.path.join(self.save_dir, "images")
                os.makedirs(self.img_dir, exist_ok=True)
                # start the devices
                self.tobii_lib.start(0)
                self.frame_capture(self.vid_cap, self.record_processor, lambda: self.stop_feed, replay)
            else:
                self.frame_capture(self.vid_cap, self.replay_processor, lambda: self.stop_feed, replay)

            self.stop_feed = True
            self.stop(replay)

            # When ctrl+c is received
        except KeyboardInterrupt:
            self.stop(replay)

        except Exception as e:
            print(e)
            self.stop(replay)

    def replay(self, video_fps=None):
        self.set_metrics()
        self.start(video_fps, True)

    def stop(self, replay=False):
        if not replay:
            self.tobii_lib.stop()
            filename = os.path.join(self.save_dir, "results.json")
            with open(filename, "w") as f:
                f.write(json.dumps(list(self.FRAMES)))
                f.close()
        cv2.destroyAllWindows()

    def record_processor(self, frame_id):
        gaze = self.tobii_lib.get_latest()[0]
        if gaze.sys_clock:
            self.FRAMES.append({
                "frame": frame_id,
                "time": time.time(),
                "tracker": gaze.to_dict()
            })
        return

    def replay_processor(self, frame_id, frame):
        font = cv2.FONT_HERSHEY_PLAIN
        color = [(100, 20, 20), (20, 100, 20), (20, 20, 100)]
        font_size = 1.1

        x = self.SCREEN_SIZE[0] - 550

        self.bg_frame[:, :x, :] = self.bg_color
        self.bg_frame[360:, x:, :] = 200

        x += 10
        cv2.putText(self.bg_frame,
                    "FPS: {:.4}, factual FPS: approx. {:.4}".format(float(self.record_fps), float(self.calc_fps)),
                    (x, 400), font, font_size, color[2], 1, cv2.LINE_4)

        cv2.putText(self.bg_frame,
                    "time min: {:.4}, max: {:.4}, mean: {:.4}"
                    .format(self.metrics["min"], self.metrics["max"], self.metrics["mean"]),
                    (x, 430), font, font_size, color[2], 1, cv2.LINE_4)

        x += 20
        y = 480

        if frame_id < len(self.FRAMES):
            cap_frame = self.FRAMES[frame_id]
            tracker = cap_frame["tracker"]
            tm = cap_frame["time"]
            gaze_time = tracker["timestamp"]
            xyv = tracker["gaze"]

            details_1 = "frame: {}, time diff {:.4}".format(frame_id, abs(gaze_time - tm))
            details_2 = "gaze: ({:.4},{:.4}), valid: {}".format(xyv["x"], xyv["y"], xyv["valid"])
            self.details_log.append([details_1, details_2])

            if xyv["valid"]:
                if True:  # 0.0 < xyv["x"] < 1.0 and 0.0 < xyv["y"] < 1.0:
                    x1 = int(self.SCREEN_SIZE[0] * xyv["x"]) - 10
                    y1 = int(self.SCREEN_SIZE[1] * xyv["y"]) - 10
                    box_w = 20
                    box_h = 20
                    cv2.rectangle(self.bg_frame, (x1, y1), (x1 + box_w, y1 + box_h), color[2], -1)

        else:
            details = "no gaze data for the frame: {}".format(frame_id)
            self.details_log.append([details, details])

        c = False
        for i in self.details_log:
            col = color[int(c)]
            cv2.putText(self.bg_frame, i[0], (x, y), font, font_size, col, 1, cv2.LINE_AA)
            cv2.putText(self.bg_frame, i[1], (x, y + 30), font, font_size, col, 1, cv2.LINE_AA)
            y += 70
            c = not c

        # add the time chart

        cv2.imshow(self.video_name, self.bg_frame)

    def all_ready(self):
        gaze = self.tobii_lib.get_latest()[0]

        if not gaze.sys_clock:
            print("tobii device not ready")
            return

        if not self.vid_cap.isOpened():
            print("video not ready")
            return False

        return True

    def frame_capture(self, cap, cb, should_stop, replay=False):
        frame_id = 0

        if not replay:
            ready = False
            # wait for all to be ready for 10 seconds, longer than that give up
            for i in range(self.poll_wait):
                print("polling for the devices ... {}".format(i))
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
        waits = 30
        if self.vid_fps:
            waits = int(1000.0 / self.vid_fps)

        cv2.namedWindow(self.video_name, cv2.WND_PROP_FULLSCREEN)
        cv2.setWindowProperty(self.video_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

        st = time.time()
        while cap.isOpened():
            if should_stop():
                break
            ret, frame = cap.read()
            if frame_id == 0:
                st = time.time()
            if not ret:
                break
            # get tobii position only if in recording mode
            if not replay:
                cb(frame_id)
                cv2.imshow(self.video_name, frame)
            else:
                cb(frame_id, frame)

            key = cv2.waitKey(waits)
            if key == ord('Q') or key == ord('q'):
                break
            frame_id += 1

        cap.release()

        if time.time() - st:
            factual_rate = frame_id / (time.time() - st)
            if not replay:
                self.calc_fps = factual_rate
            print("factual rate used: {}".format(factual_rate))
            sys.stdout.flush()


if __name__ == "__main__":
    synced = Synced("./data/stimulus_sample.mp4")
    synced.start(video_fps=1000)
    print("start replay")
    synced.replay()
