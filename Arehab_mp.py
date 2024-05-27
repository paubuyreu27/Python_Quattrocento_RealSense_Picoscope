import mp_script as mproc
import pyrealsense2 as rs

from realsense_utils import realsense_config, get_frame
import time
import numpy as np
import cv2

class mp_show(mproc.Process):

    def __init__(self, red_queue, green_queue):
        super().__init__()
        
        # 2. create interprocess communication primitives and shared resources used by the current multiprocess:
        self.red_queue = red_queue
        self.green_queue = green_queue


    def run(self):
        # 4. import libraries that use multithreading:
        # from SomeLibrary import Analyzer
        # from concurrent.futures import ThreadPoolExecutor
        import mediapipe as mp
        # 5. if you use asyncio, remember to create a new event loop
        n = 0
        # other libraries
        mp_drawing = mp.solutions.drawing_utils
        mp_drawing_styles = mp.solutions.drawing_styles
        mp_pose = mp.solutions.pose

        # Create a pose estimator here
        self.pose = mp_pose.Pose(
            min_tracking_confidence=0.5,
            min_detection_confidence=0.5,
            smooth_landmarks=False,
        )

        while True:
            try:
                if not self.red_queue.empty():
            
                    n += 1
                    img = self.red_queue.get()
                    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                    img.flags.writeable = False
                    pose = self.pose
                    results = pose.process(img)
                                #pose 
                    img.flags.writeable = True

                    mp_drawing.draw_landmarks(
                    img,
                    results.pose_landmarks,
                    mp_pose.POSE_CONNECTIONS,
                    landmark_drawing_spec=mp_drawing_styles
                    .get_default_pose_landmarks_style())

                    img = cv2.flip(img, 1)



                    # Display the image
                    cv2.imshow('ARehab', img)
                    if cv2.waitKey(1) == ord('q'):
                        self.green_queue.put(True)
                        break
            except BrokenPipeError: # Handle broken pipe error (e.g., log, exit gracefully)
                break


def main():
    # inicilizar los queue y la pipeline de realsense

    # realsense config

    fs = 30  # sampling frequency
    pipeline, align = realsense_config(fs)
    previous_stamp = 0

    time_vect = np.array([])
    frame_vect = np.array([])

    # multiproc config
    red_queue = mproc.Queue()
    green_queue = mproc.Queue()
    read_proc = mp_show(red_queue=red_queue, green_queue=green_queue)
    read_proc.start()  # Start the process here
    n = 1

    output = cv2.VideoWriter(
        "output.avi", cv2.VideoWriter_fourcc(*'mp4v'), fs, (640, 480))

    while True:
        frame, color_image, depth_image, depth_intrin = get_frame(pipeline, align)
        # frame for the timestamp, color_image is a time array of color frame, depth image nparray of the depth, depth_intrin to obtain the same coordinates.
        if frame.get_timestamp() == previous_stamp:
            continue
        previous_stamp = frame.get_timestamp()
        time_vect = np.append(time_vect, np.array(time.perf_counter()))  # -init_time
        frame_vect = np.append(frame_vect, np.array(frame.get_timestamp()))

        # image_mediapipe = cv2.cvtColor(color_image, cv2.COLOR_BGR2RGB)

        red_queue.put(color_image)

        # grabar imagen
        img = cv2.flip(color_image, 1)
        output.write(img)

        if not green_queue.empty():
            break
    read_proc.join()
    print("finished the process")
    cv2.destroyAllWindows()
    pipeline.stop()

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

    

if __name__=='__main__':
    main()