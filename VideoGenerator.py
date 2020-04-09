import numpy as np
import cv2 as cv
import copy
import math

def plot(img):
    fig, ax = plt.subplots(figsize = (10,10))
    ax.imshow(img)
    
def get_speed(size, delta, framerate):
    speed = size*delta/framerate
    return speed


def GenerateVideo(name, duration, width, height, fps, startRad, dR, dphi):
    print("Video generation start")
    background = np.full((height,width,3),255).astype(dtype = 'uint8')
    fourcc = cv.VideoWriter_fourcc('m', 'p', '4', 'v')
    out = cv.VideoWriter()
    
    success = out.open(name+'.mp4',fourcc,fps,(width, height),True) 
    traj_out = open(name+'.txt','w')
    
    Y, X, _ = background.shape
    X_center = X/2
    Y_center = Y/2
    
    rad = startRad
    phi = 0
    
    framecounts = int(duration*fps)
    dt = 1.0/fps
    
    radius = 5
    color = (255, 0, 0)
    thickness = 5
    
    dphi_frame = dphi*1.0/fps
    dR_frame = dR*1.0/fps
    for i in range(framecounts):
        
        phi = phi+dphi_frame
        phi_radians = math.radians(phi)
        rad = rad+dR_frame
        
        X = X_center+ math.sin(phi_radians)*rad
        Y = Y_center+ math.cos(phi_radians)*rad
        center_coordinates = (int(X),int(Y))
        
        back = copy.deepcopy(background)
        frame = cv.circle(back, center_coordinates, radius, color, thickness)
        out.write(frame)
        
        traj_out.write(str(dt*i)+'\t'+str(X)+'\t'+str(Y)+'\n')
        
    out.release()
    traj_out.close()
    print("Video generation end")
    
    
def GenerateVideoText(name, duration, width, height, fps, image):
    print("Text generation start")
    fourcc = cv.VideoWriter_fourcc('m', 'p', '4', 'v')
    out = cv.VideoWriter()
    success = out.open(name+'.mp4',fourcc,fps,(width, height),True) 
    framecounts = int(duration*fps)
    for i in range(framecounts):
         out.write(image)
    out.release()
    print("Text generation end")

