# eye-tracker
Eye Tracker

On Windows branch, the device is any Tobii tracker that support the Core SDK.
The device is connected and drivers installed. 


** Requirements ** 
numpy
Pillow
opencv-python
matplot



** setup ** 
install OpenCV c++ binaries
set the $OPENCV_DIR environment variable 

Add the Tobii Stream libs and dll to the debug and release folders 
Build the dll in TobiiLib


Install the rest of the requirements

python -m pip install kivy_examples==1.11.1
python -m pip install docutils pygments pypiwin32 kivy_deps.sdl2==0.1.* kivy_deps.glew==0.1.*
python -m pip install kivy_deps.gstreamer==0.1.*
python -m pip install kivy_deps.angle==0.1.*
python -m pip install kivy==1.11.1


