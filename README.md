# eye-tracker
Eye Tracker

On mac branch it is expected that the device is a Tobii 4C and uses the talonvoice drivers and that talonvoice application is installed and up and running 

The application copies the `eye_mon_snap.py` to the ~/.talon/user directory 

This puts up the gaze tracker and log it on the localhost socket.

The `main.py` feeds from this socket throught the gaze_listener module and queues the top 100 gaze records as well as the top 100 camera records at any given instance.

on impulse signal, the app finds the camera feed frame as well as the gaze record whose record time is closest to the time of signal 