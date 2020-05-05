import cv2
import time
import matplotlib.pyplot as plt
import os
import sys
from ctypes import cdll, c_int, POINTER, c_char_p, c_char, c_long
from tracker_record import Record
import json
from PIL import ImageGrab
from collections import deque
import numpy as np
import io
import threading

CString = POINTER(c_char)

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


class ASynced:
    """
        Module that synchronizes video frames , Tobii tracker data and Camera frames.
        Interfaces the DLL written in c++ in the TobiiLib project
        Arguments:
            video_path[String] path to the stimuli video source
            save_dir[String] path to the output directory ["./sample"],
            dll_path [String] path to the DLL ["./TobiiEyeLib/x64/Debug/TobiiEyeLib.dll"]
            cam_index=0, bg_color=(255, 255, 255)
    """
    stop_tobii_thread = None

    def __init__(self, video_path, save_dir="sample",
                 dll_path="TobiiEyeLib/x64/Debug/TobiiEyeLib.dll",
                 cam_index=0, bg_color=(255, 255, 255)):

        screen_grab = ImageGrab.grab()
        self.SCREEN_SIZE = screen_grab.size
        self.bg_frame = np.zeros(shape=(self.SCREEN_SIZE[1], self.SCREEN_SIZE[0], 3), dtype=np.uint8)
        self.bg_color = bg_color
        self.fore_color = (200, 200, 0)
        self.calc_fps = 0.0
        self.record_fps = 0.0

        self.details_log = deque(maxlen=(self.SCREEN_SIZE[1] - 460) // 70)

        # metric object for indicating the degree of sync between device data and stimuli frames
        self.metrics = {
            "mean": .0,
            "min": .0,
            "max": .0
        }

        try:
            self.tobii_lib = cdll.LoadLibrary(dll_path)
            self.tobii_lib.run.argtypes = [CString, CString, c_int]
            self.tobii_lib.run.restype = c_int

            self.tobii_lib.save_images.restype = c_long
            self.tobii_lib.save_images.argtypes = [CString]

            self.tobii_lib.get_json.restype = CString

        except OSError as err:
            print("os error", err)
            return;

        self.save_dir = save_dir
        self.img_dir = save_dir
        self.cam_index = cam_index
        self.video_path = video_path
        self.video_name = None

    def __del__(self):
        """
        :return:
        """
        pass

    def start(self, video_fps=None):
        """
        :param video_fps:
        :param replay:
        :return:
        """
        if not os.path.isfile(self.video_path):
            print("the video file not found")
            return

        if video_fps:
            self.vid_fps = int(1000.0/video_fps)
        else:
            # set the video determined fps
            self.vid_fps = -1

        try:
            self.tobii_lib.run(self.video_path, self.video_path, self.vid_fps)
            # When ctrl+c is received
        except KeyboardInterrupt:
            self.tobii_lib.stop()

        except Exception as e:
            print(e)
            self.tobii_lib.stop()

    def replay(self, video_fps=None):
        """
        :param video_fps:
        :return:
        """
        pass

    def get_json(self):
        return self.tobii_lib.get_json()

    def get_json(self):
        return self.tobii_lib.get_json()

    def stop(self, replay=False):
        """

        :param replay:
        :return:
        """
        self.tobii_lib.stop()

    # def replay_processor(self, frame_id, frame):
    #     """
    #     :param frame_id: int
    #     :param frame: cv2::Mat
    #     :return: None
    #     """
    #     font = cv2.FONT_HERSHEY_PLAIN
    #     color = [(100, 20, 20), (20, 100, 20), (20, 20, 100)]
    #     font_size = 1.1
    #
    #     x = self.SCREEN_SIZE[0] - 550
    #
    #     self.bg_frame[:, :x, :] = self.bg_color
    #     self.bg_frame[360:, x:, :] = 200
    #
    #     x += 10
    #     cv2.putText(self.bg_frame,
    #                 "FPS: {:.4}, factual FPS: approx. {:.4}".format(float(self.record_fps), float(self.calc_fps)),
    #                 (x, 400), font, font_size, color[2], 1, cv2.LINE_4)
    #
    #     cv2.putText(self.bg_frame,
    #                 "time min: {:.4}, max: {:.4}, mean: {:.4}"
    #                 .format(self.metrics["min"], self.metrics["max"], self.metrics["mean"]),
    #                 (x, 430), font, font_size, color[2], 1, cv2.LINE_4)
    #
    #     x += 20
    #     y = 480
    #
    #     if frame_id < len(self.FRAMES):
    #         cap_frame = self.FRAMES[frame_id]
    #         tracker = cap_frame["tracker"]
    #         tm = cap_frame["time"]
    #         gaze_time = tracker["timestamp"]
    #         xyv = tracker["gaze"]
    #
    #         details_1 = "frame: {}, time diff {:.4}".format(frame_id, abs(gaze_time - tm))
    #         details_2 = "gaze: ({:.4},{:.4}), valid: {}".format(xyv["x"], xyv["y"], xyv["valid"])
    #         self.details_log.append([details_1, details_2])
    #
    #         if xyv["valid"]:
    #             if True:  # 0.0 < xyv["x"] < 1.0 and 0.0 < xyv["y"] < 1.0:
    #                 x1 = int(self.SCREEN_SIZE[0] * xyv["x"])
    #                 y1 = int(self.SCREEN_SIZE[1] * xyv["y"])
    #                 # box_w = 20
    #                 # box_h = 20
    #                 # create target circle
    #                 radius = min(20, self.SCREEN_SIZE[0] - x1, self.SCREEN_SIZE[1] - y1)
    #                 cv2.circle(self.bg_frame, (x1, y1), radius,
    #                            color[2], thickness=2, lineType=8, shift=0)
    #                 # # cv2.rectangle(self.bg_frame, (x1, y1), (x1 + box_w, y1 + box_h), color[2], -1)
    #                 radius = max(min(radius - 5, radius - 10, radius - 15),  0)
    #                 # horizontal line
    #                 a, b = (x1 - radius, y1), (x1 + radius, y1)
    #                 cv2.line(self.bg_frame, a, b,
    #                          color[1], thickness=1, lineType=8, shift=0)
    #                 # vertical line
    #                 a, b = (x1, y1 - radius), (x1, y1 + radius)
    #                 cv2.line(self.bg_frame, a, b,
    #                          color[1], thickness=1, lineType=8, shift=0)
    #
    #     else:
    #         details = "no gaze data for the frame: {}".format(frame_id)
    #         self.details_log.append([details, details])
    #
    #     c = False
    #     for i in self.details_log:
    #         col = color[int(c)]
    #         cv2.putText(self.bg_frame, i[0], (x, y), font, font_size, col, 1, cv2.LINE_AA)
    #         cv2.putText(self.bg_frame, i[1], (x, y + 30), font, font_size, col, 1, cv2.LINE_AA)
    #         y += 70
    #         c = not c
    #
    #     # add the time chart
    #
    #     cv2.imshow(self.video_name, self.bg_frame)

    # def frame_capture(self, cap, cb, should_stop, replay=False):
    #     """
    #     The process for showing frames on the screen during recording or replay
    #     :param cap: [CV2::VideoCapture] from which frames are read
    #     :param cb: [Function] The callback function to process the captured frame
    #     :param should_stop: [Function] the function to signal the process to stop if it is in thread
    #     :param replay: [Boolean]
    #     :return:
    #     """
    #     frame_id = 0
    #
    #     if not replay:
    #         ready = False
    #         # wait for all to be ready for 10 seconds, longer than that give up
    #         for i in range(self.poll_wait):
    #             print("polling for the devices ... {}".format(i))
    #             sys.stdout.flush()
    #             if self.all_ready():
    #                 ready = True
    #                 break
    #             time.sleep(1)
    #     else:
    #         # replay mode, we are showing the user their recorded screen gaze
    #         ready = True
    #
    #     if not ready:
    #         print("got tired of waiting...")
    #         sys.stdout.flush()
    #         return -1
    #
    #     waits = 30
    #     # in the event that vid_fps is undefined or 0 or None, escape division by zero
    #     if self.vid_fps:
    #         waits = int(1000.0 / self.vid_fps)
    #
    #     # set the video to full screen
    #     cv2.namedWindow(self.video_name, cv2.WND_PROP_FULLSCREEN)
    #     cv2.setWindowProperty(self.video_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    #
    #     st = time.time()
    #     while cap.isOpened():
    #
    #         if should_stop():
    #             break
    #         # read the next frame
    #         ret, frame = cap.read()
    #
    #         if not ret:
    #             break
    #
    #         # first few frames takes longer,
    #         # for a truthful Factual FPS reset time for every frame less than the first stable frame
    #         if frame_id < 5:
    #             st = time.time()
    #
    #         cb(frame_id, frame)
    #
    #         key = cv2.waitKey(waits)
    #
    #         # signal stop if user press Q, or q
    #         if key == ord('Q') or key == ord('q'):
    #             break
    #         # increment the frame index
    #         frame_id += 1
    #
    #     # release the video capture
    #     cap.release()
    #
    #     # calculate the Factual Rate used
    #     if time.time() - st:
    #         factual_rate = frame_id / (time.time() - st)
    #         return factual_rate
    #
    #     return 0


if __name__ == "__main__":
    synced = ASynced("./data/stimulus_sample.mp4",
                    dll_path="TobiiEyeLib/x64/Release/TobiiEyeLib.dll",)
    synced.start(video_fps=1000)
    # print("start replay")
