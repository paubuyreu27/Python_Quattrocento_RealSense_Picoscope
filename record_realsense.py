#pruebas_cv2cam
import cv2
import mediapipe as mp
from realsense_utils import realsense_config, get_frame
import time
import pyrealsense2 as rs
import numpy as np

# ----------------
# Realsense CONFIG
# ----------------


# samp_freq = 30 #[Hz]


pipe = rs.pipeline()
cfg = rs.config()

cfg.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
cfg.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)

pipe.start(cfg)
previous_stamp = 0

init_time = time.perf_counter()
time_vect = np.array([])
frame_vect = np.array([])

output = cv2.VideoWriter( 
        "output.avi", cv2.VideoWriter_fourcc(*'mp4v'), 90, (640, 480)) 

while True:
    frame = pipe.wait_for_frames()
    if frame.get_timestamp() == previous_stamp:
         continue
    previous_stamp = frame.get_timestamp()
    init_time = time.perf_counter()
    depth_frame = frame.get_depth_frame()
    color_frame = frame.get_color_frame()
    time_vect = np.append(time_vect, np.array(time.perf_counter())) #-init_time
    frame_vect = np.append(frame_vect, np.array(frame.get_timestamp()))

    # depth_image = np.asanyarray(depth_frame.get_data())
    image = np.asanyarray(color_frame.get_data())

    
        # image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    # image = cv2.cvtColor(image,cv2.COLOR_RGB2GRAY)
    # image.flags.writeable = False # To improve performance, optionally mark the image as not writeable to pass by reference.


    # Flip the image horizontally for a selfie-view display.
    cv2.imshow('Realsense', cv2.flip(image, 1))

    #grabar imagen
    output.write(image)

    if cv2.waitKey(1) == ord('q'):
        break

csv_file_path = "times.csv"

with open(csv_file_path, 'w', newline='') as fout:
        i = 0
        fout.write('frame_n, py_time, rs_time')
        fout.write('\n')
        for kpt in time_vect:
            fout.write(str(i+1)+', '+str(kpt)+', '+str(frame_vect[i]))
            fout.write('\n')
            i += 1
        fout.close()

print("Vector saved to", csv_file_path)

pipe.stop()
