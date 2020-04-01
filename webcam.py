import cv2
import time
import os
import argparse
import json

face_cascade = None
eye_cascade = None

def parse_args():
    """ Parse command line arguments.
    """
    parser = argparse.ArgumentParser(description="eye tracker frame synchronized capture")
    parser.add_argument(
        "--fps", help="Frames per second",
         required=True, type=float)
    
    parser.add_argument(
        "-c", "--cam", help="The camera index, usually 0 for web camera", default=0, type=int)
    
    parser.add_argument(
        "-n", "--numframes", help="number of desired frames", default=20, type=int)
    
    parser.add_argument(
        "-w", "--weights", help="the weights directory containing haarcascade_frontalface_default.xml and haarcascade_eye.xml files", default="./weights/")

    parser.add_argument( 
        "--visualise", help="visualize the process", default=0, type=int)

    parser.add_argument(
        "-o", "--output", help="the output directory or output .mp4 file to save frames to", default="./")

    return parser.parse_args()

def framesToVideo(frames, outfile, fps):
    if not len(frames):
        return 

    shape = frames[0].shape
    out = cv2.VideoWriter( outfile,cv2.VideoWriter_fourcc(*'mp4v'), fps, (shape[1], shape[0]))

    for i in range(len(frames)):
        out.write(frames[i])
    out.release()


def trackeyes(frame):  
    """
        returns arrays of eye boxes in frame [[x,y,w,h],...]
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) 
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)

    res = []
    for (x,y,w,h) in faces:
        roi_gray = gray[y:y+h, x:x+w] 
        eyes = eye_cascade.detectMultiScale(roi_gray,
                minNeighbors=8, 
                scaleFactor=1.1
                ) 

        for (ex,ey,ew,eh) in eyes:
            res.append([
                int(ex + x),
                int(ey + y),
                int(ew),
                int(eh)
            ])
    
    return res 

def trackcam(frame_rate, output = "", cam_index = 0, max_frames = 20, visualize = False):
    if frame_rate == 0.0:
        return 

    img_counter = 0
    cap = cv2.VideoCapture(cam_index)

    res = {
        "fps" : frame_rate,
        "eyes" : {

        }
    }
    frames = []
    marked_frames = []

    while True:
        ret, frame = cap.read()        
        if img_counter > max_frames:
            break

        if not ret:
            break

        eyes= trackeyes(frame)
        frames.append(frame)

        res["eyes"][img_counter] = eyes

        if not output.endswith(".mp4"):
            img_name = "{}/frame_{}.png".format(output,img_counter)
            cv2.imwrite(img_name, frame)

        for (ex,ey,ew,eh) in eyes: 
            cv2.rectangle(frame,(ex,ey),(ex+ew,ey+eh),(0,127,255),2) 

        marked_frames.append(frame)

        if not output.endswith(".mp4"):
            img_name = "{}/marked-frame_{}.png".format(output,img_counter)
            cv2.imwrite(img_name, frame)
            
        
        img_counter += 1

        if visualize:
            cv2.imshow('eye tracker', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            
        time.sleep(1/frame_rate) # pause and sync with fps

    cap.release()
    cv2.destroyAllWindows()

    if output.endswith(".mp4"):
        sp = output.split(os.sep)
        sp[-1] = "marked-" + sp[-1];

        print(os.sep.join(sp))

        framesToVideo(frames, output, frame_rate)
        framesToVideo(marked_frames, os.sep.join(sp), frame_rate)

    return res


if __name__ == '__main__':
    args = parse_args()

    output = args.output.strip()
    json_file = output + "/results.json"

    if output.endswith(".mp4"):
        path = output.split(os.sep)[:-1]    
        path = os.sep.join(path)

        os.makedirs(path, exist_ok=True)
        json_file =  "{}/results.json".format(path)
    else:
        if output.endswith("/"):
            output = output[:-1]
        json_file = output + "/results.json"
        os.makedirs(output, exist_ok=True)
    
    weights_dir = args.weights.strip()

    if weights_dir.endswith("/"):
        weights_dir = weights_dir[:-1]

    hcff = '{}/haarcascade_frontalface_default.xml'.format(weights_dir)
    hce = '{}/haarcascade_eye.xml'.format(weights_dir)

    if not (os.path.isfile(hcff) and os.path.isfile(hce)):
        print("provide valid path to weights")
        exit(-1)

    face_cascade = cv2.CascadeClassifier(hcff)
    eye_cascade = cv2.CascadeClassifier(hce)

    

    # visual()

    results = trackcam(args.fps, output, args.cam, args.numframes, args.visualise)
    
    with open(json_file, "w") as f:
        json.dump(results, f)
        print("done: results in json file {}".format(json_file))
        f.close()
    