# eye-tracker
Eye Tracker

On Windows and Linux branch it is expected that the device is any Tobii tracker that support the TobiiPro SDK and it is expected that the device is connected and drivers installed. 

A callback function reads gaze records directly from the interface provided by the TobiiPro SDK

The `main.py` feeds from this callback throught the gaze_listener module and queues the top 10-100 gaze records.

on impulse signal, the app finds the camera feed frame as well as the gaze record whose record time is closest to the time of signal 

** Requirements ** 
kivy
numpy
opencv

** setup ** 
python -m pip install kivy_examples==1.11.1
python -m pip install docutils pygments pypiwin32 kivy_deps.sdl2==0.1.* kivy_deps.glew==0.1.*
python -m pip install kivy_deps.gstreamer==0.1.*
python -m pip install kivy_deps.angle==0.1.*
python -m pip install kivy==1.11.1


