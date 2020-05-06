import cv2
import time
import matplotlib.pyplot as plt
import os
import sys
from ctypes import cdll, c_int, POINTER, c_char_p, c_char
from tracker_record import Record
import json
from PIL import ImageGrab
from collections import deque
import numpy as np
import io
import threading

CString = POINTER(c_char)


class DummyTobii:
    """Dummy Tobii class to imitate the TobiiLib in the event of an error from the DLL, for testing only"""
    take_shots = False
    cam_shot = None
    cap = None
    records = deque()
    frame = None
    img_dir = None
    frame_id = 0

    def start(self, cam_index=0, img_dir=""):
        self.records.append(Record())
        self.cap = cv2.VideoCapture(cam_index)
        cam_thread = threading.Thread(target=self.cam_shots)
        try:
            cam_thread.start()

        except KeyboardInterrupt:
            cam_thread.join()
            self.cap.release()

    def cam_shots(self):
        while self.take_shots and self.cap and self.cap.isOpened():
            ret, self.frame = self.cap.read()
            r = np
            if self.img_dir:
                cv2.imwrite("{}/frame-{}.png".format(self.img_dir, self.frame_id), self.frame)
                self.frame_id += 1

            self.records.appendleft(Record())

    def stop(self):
        if self.cap.isOpened():
            self.cap.release()

    def get_latest(self, index=0):
        return self.records


def get_img_from_fig(fig, dpi=100):
    """converts a matplotlib figure image to cv2 image
        fig: [Matplotlib Figure]
        dpi: [int] the desired dpi of the image
    """
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi)
    buf.seek(0)
    img_arr = np.frombuffer(buf.getvalue(), dtype=np.uint8)
    buf.close()
    img = cv2.imdecode(img_arr, 1)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    return img


class Synced:
    """
        Module that synchronizes video frames , Tobii tracker data and Camera frames.
        Interfaces the DLL written in c++ in the TobiiLib project
        Arguments:
            video_path[String] path to the stimuli video source
            save_dir[String] path to the output directory ["./sample"],
            dll_path [String] path to the DLL ["./TobiiEyeLib/x64/Debug/TobiiEyeLib.dll"]
            cam_index=0, poll_wait=10, bg_color=(255, 255, 255)
    """
    stop_feed = False

    # fast appends, 0(1) contains session data at the end of recording
    FRAMES = deque()
    render_rect = None
    stop_tobii_thread = None
    real_time_gaze = False

    def __init__(self, video_path, save_dir="sample",
                 dll_path="TobiiEyeLib/x64/Debug/TobiiEyeLib.dll",
                 cam_index=0, poll_wait=10, bg_color=(255, 255, 255)):

        screen_grab = ImageGrab.grab()
        self.SCREEN_SIZE = screen_grab.size
        self.bg_frame = np.zeros(shape=(self.SCREEN_SIZE[1], self.SCREEN_SIZE[0], 3), dtype=np.uint8)
        self.bg_color = bg_color
        self.fore_color = (200, 200, 0)
        self.calc_fps = 0.0
        self.record_fps = 0.0

        self.poll_wait = poll_wait
        self.details_log = deque(maxlen=(self.SCREEN_SIZE[1] - 460) // 70)

        # metric object for indicating the degree of sync between device data and stimuli frames
        self.metrics = {
            "mean": .0,
            "min": .0,
            "max": .0
        }

        try:
            self.tobii_lib = cdll.LoadLibrary(dll_path)
            self.tobii_lib.start.argtypes = [c_int, c_char_p]
            self.tobii_lib.stop.restype = c_int
            self.tobii_lib.start.restype = c_int
            self.tobii_lib.get_latest.argtypes = [c_int]
            self.tobii_lib.get_latest.restype = POINTER(Record)
        except OSError as err:
            print("os error", err)
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

    def __del__(self):
        """
        :return:
        """
        if self.stop_tobii_thread is not None:
            if self.stop_tobii_thread.is_alive():
                self.stop_tobii_thread.join()

    def set_metrics(self):
        """
            creates chart indicative of the latency
        :return:
        """
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

        self.metrics = {
            "mean": times.mean(),
            "min": mn,
            "max": mx,
            "chart": chart
        }

    def log_frames(self):
        """
            helper function to visualize the frame progress, slows down the frame cycle
        :return:
        """
        last_cam_frame = self.FRAMES
        if len(last_cam_frame):
            last_cam_frame = last_cam_frame[-1]
            tracker = last_cam_frame["tracker"]
            tm = last_cam_frame["time"]
            gaze_time = tracker["timestamp"]

            print("gaze_time: {}, time: {}, acc: {} \n gaze: {}\n\n".format(gaze_time,
                                                                            tm, abs(gaze_time - tm), tracker["gaze"]))

    def start(self, video_fps=None, replay=False, real_time_gaze = False):
        """

        :param video_fps:
        :param replay:
        :return:
        """
        if not os.path.isfile(self.video_path):
            print("the video file not found")
            return
        self.vid_cap = None
        self.vid_cap = cv2.VideoCapture(self.video_path)
        self.video_name = "replay: {}".format(self.video_path.split(os.sep)[-1])
        self.real_time_gaze = real_time_gaze

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
                self.tobii_lib.start(0, bytes(self.img_dir, encoding='utf-8'))
                factual_fps = self.frame_capture(self.vid_cap, self.record_processor, lambda: self.stop_feed, replay)
            else:
                factual_fps = self.frame_capture(self.vid_cap, self.replay_processor, lambda: self.stop_feed, replay)

            if not replay:
                self.calc_fps = factual_fps
            if factual_fps:
                print("factual rate used: {}".format(factual_fps))

            self.stop_feed = True
            self.stop(replay)

            # When ctrl+c is received
        except KeyboardInterrupt:
            self.stop(replay)

        except Exception as e:
            print(e)
            self.stop(replay)

    def replay(self, video_fps=None):
        """

        :param video_fps:
        :return:
        """
        self.set_metrics()
        self.start(video_fps, True)

    def stop(self, replay=False):
        """

        :param replay:
        :return:
        """
        if not replay:
            if self.stop_tobii_thread is not None:
                if self.stop_tobii_thread.is_alive():
                    self.stop_tobii_thread.join()

            self.stop_tobii_thread = threading.Thread(target=self.tobii_lib.stop)
            self.stop_tobii_thread.start()

            filename = os.path.join(self.save_dir, "results.json")
            with open(filename, "w") as f:
                f.write(json.dumps(list(self.FRAMES)))
                f.close()
        cv2.destroyAllWindows()

    def record_processor(self, frame_id, frame):
        """
        :param frame_id:
        :param frame:
        :return:
        """
        tm = time.time()
        tracker = self.tobii_lib.get_latest(frame_id)[0]
        # check the query latency here, [recent test on VM gets x/1000 for [x < 9.0]
        # latency = time.time() - tm
        # print("latency {}".format(latency))
        # sys.stdout.flush()


        self.bg_frame[:, :, :] = self.bg_color
        # self.bg_frame[self.render_rect[1]:self.render_rect[3], self.render_rect[0]:self.render_rect[2], :] = frame
        self.bg_frame[0:frame.shape[0], 0:frame.shape[1], :] = frame
        if tracker.sys_clock:
            self.FRAMES.append({
                "frame": frame_id,
                "time": tm,
                "camera": {
                    "timestamp": tracker.sys_clock,
                    "frame": frame_id
                },
                "tracker": tracker.to_dict()
            })
            if self.real_time_gaze:
                color = [(100, 20, 20), (20, 100, 20), (20, 20, 100)]
                xyv = tracker.gaze
                x1 = int(xyv.x * self.SCREEN_SIZE[0])
                y1 = int(xyv.y * self.SCREEN_SIZE[1])
                # box_w = 20
                # box_h = 20
                # create target circle
                # radius = min(10, self.SCREEN_SIZE[0] - x1, self.SCREEN_SIZE[1] - y1)
                radius = 10
                cv2.circle(self.bg_frame, (x1, y1), radius,
                           color[2], thickness=2, lineType=8, shift=0)
                # # cv2.rectangle(self.bg_frame, (x1, y1), (x1 + box_w, y1 + box_h), color[2], -1)
                radius = max(min(radius - 5, radius - 10),  0)
                # horizontal line
                a, b = (x1 - radius, y1), (x1 + radius, y1)
                cv2.line(self.bg_frame, a, b,
                         color[1], thickness=1, lineType=8, shift=0)
                # vertical line
                a, b = (x1, y1 - radius), (x1, y1 + radius)
                cv2.line(self.bg_frame, a, b,
                         color[1], thickness=1, lineType=8, shift=0)
            cv2.imshow(self.video_name, self.bg_frame)
        return

    def replay_processor(self, frame_id, frame):
        """
        :param frame_id: int
        :param frame: cv2::Mat
        :return: None
        """
        font = cv2.FONT_HERSHEY_PLAIN
        color = [(100, 20, 20), (20, 100, 20), (20, 20, 100)]
        font_size = 1.1

        frame_id

        x = self.SCREEN_SIZE[0] - 550
        self.bg_frame[:, :, :] = 255
        ww = self.render_rect[2] - self.render_rect[0]
        hh = self.render_rect[3] - self.render_rect[1]
        # frame = cv2.resize(frame, (ww, hh))
        self.bg_frame[:, :x, :] = self.bg_color
        # self.bg_frame[self.render_rect[1]:self.render_rect[3], self.render_rect[0]:self.render_rect[2], :] = frame
        self.bg_frame[0:frame.shape[0], 0:frame.shape[1], :] = frame
        self.bg_frame[360:, x:, :] = 200
        y = 50
        self.bg_frame[y:y+300, x:x+500, :] = self.metrics["chart"]


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
                    x1 = int(xyv["x"] * self.SCREEN_SIZE[0])
                    y1 = int(xyv["y"] * self.SCREEN_SIZE[1])
                    # box_w = 20
                    # box_h = 20
                    # create target circle
                    # radius = min(10, self.SCREEN_SIZE[0] - x1, self.SCREEN_SIZE[1] - y1)
                    radius = 10
                    cv2.circle(self.bg_frame, (x1, y1), radius,
                               color[2], thickness=2, lineType=8, shift=0)
                    # # cv2.rectangle(self.bg_frame, (x1, y1), (x1 + box_w, y1 + box_h), color[2], -1)
                    radius = max(min(radius - 5, radius - 10),  0)
                    # horizontal line
                    a, b = (x1 - radius, y1), (x1 + radius, y1)
                    cv2.line(self.bg_frame, a, b,
                             color[1], thickness=1, lineType=8, shift=0)
                    # vertical line
                    a, b = (x1, y1 - radius), (x1, y1 + radius)
                    cv2.line(self.bg_frame, a, b,
                             color[1], thickness=1, lineType=8, shift=0)

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
        """
        :return: Boolean
        """
        gaze = self.tobii_lib.get_latest(0)[0]

        if not gaze.sys_clock:
            print("tobii device not ready")
            return False

        if not self.vid_cap.isOpened():
            print("video not ready")
            return False

        return True

    def frame_capture(self, cap, cb, should_stop, replay=False):
        """
        The process for showing frames on the screen during recording or replay
        :param cap: [CV2::VideoCapture] from which frames are read
        :param cb: [Function] The callback function to process the captured frame
        :param should_stop: [Function] the function to signal the process to stop if it is in thread
        :param replay: [Boolean]
        :return:
        """
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
            return -1

        waits = 30
        # in the event that vid_fps is undefined or 0 or None, escape division by zero
        if self.vid_fps:
            waits = int(1000.0 / self.vid_fps)

        # set the video to full screen
        # cv2.namedWindow(self.video_name, cv2.WND_PROP_FULLSCREEN)
        # cv2.setWindowProperty(self.video_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

        st = time.time()
        while cap.isOpened():

            if should_stop():
                break
            # read the next frame
            ret, frame = cap.read()

            if not ret:
                break

            # first few frames takes longer,
            # for a truthful Factual FPS reset time for every frame less than the first stable frame
            if frame_id < 5:
                if not replay:
                    self.render_rect = cv2.getWindowImageRect(self.video_name)
                st = time.time()

            cb(frame_id, frame)

            key = cv2.waitKey(waits)

            # signal stop if user press Q, or q
            if key == ord('Q') or key == ord('q'):
                break
            # increment the frame index
            frame_id += 1

        # release the video capture
        cap.release()

        # calculate the Factual Rate used
        if time.time() - st:
            factual_rate = frame_id / (time.time() - st)
            return factual_rate

        return 0


if __name__ == "__main__":
    synced = Synced("./data/stimulus_sample.mp4",
                    dll_path="TobiiEyeLib/x64/Release/TobiiEyeLib.dll",)
    synced.start(video_fps=1000)
    # print("start replay")
    synced.replay(video_fps=30)
