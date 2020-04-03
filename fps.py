#!/usr/bin/env python
import cv2
import time

def recordFPS(video, num_frames = 120):
    
    # Start time
    start = time.time()    
    # Grab a few frames
    for i in range(0, num_frames) :
        ret, frame = video.read()    
    # End time
    end = time.time()
    # Time elapsed
    seconds = end - start
    # Calculate frames per second
    fps  = num_frames / seconds;
    
    return fps

if __name__ == '__main__' :
    # Start default camera
    video = cv2.VideoCapture(0);
    
    fps = video.get(cv2.CAP_PROP_FPS)
    print ("Frames per second using video.get(cv2.CAP_PROP_FPS) : {0}".format(fps))

    ffps = recordFPS(video)
    print ("Factual Frames per second: {0}".format(fps))

    fix = 20
    video.set(cv2.CAP_PROP_FPS, fix)
    fps = video.get(cv2.CAP_PROP_FPS)

    print ("Frames per second after fixing at {1}: {0}".format(fps, fix))
    ffps = recordFPS(video)    
    print ("Factual Frames per second after fixing at {1}: {0}".format(ffps, fix))
    # Release video
    video.release()