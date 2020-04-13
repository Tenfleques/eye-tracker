from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.clock import Clock
from kivy.graphics.texture import Texture

import cv2

class CVideo(Image):
    def build(self):
        self.img_src=self.ids["img_src"]
        self.capture = cv2.VideoCapture(self.img_src.src)
        Clock.schedule_interval(self.update, self.img_src.fps)

    def update(self, dt):
        ret, frame = self.capture.read()
        # convert it to texture
        buf1 = cv2.flip(frame, 0)
        buf = buf1.tostring()
        texture1 = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='bgr') 
        #if working on RASPBERRY PI, use colorfmt='rgba' here instead, but stick with "bgr" in blit_buffer. 
        texture1.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
        # display image from the texture
        self.img_src.texture = texture1

class VideoApp(App):
    def build(self):
        video = CVideo()
        return video

if __name__ == '__main__':
    VideoApp().run()