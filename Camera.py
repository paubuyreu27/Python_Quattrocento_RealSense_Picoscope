import pyrealsense2 as rs
import numpy as np
import cv2
import os
from PyQt5 import QtWidgets, QtCore, QtGui
# import config_functions as cf
import mediapipe as mp
import pandas as pd
import realsense_utils


class Camera(QtCore.QObject):
    def __init__(self):
        super().__init__()
        self.recording = False
        self.pipe = rs.pipeline()
        self.cfg = rs.config()
        self.cfg.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
        self.cfg.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
        profile = self.pipe.start(self.cfg)

        depth_sensor = profile.get_device().first_depth_sensor()
        depth_scale = depth_sensor.get_depth_scale()
        print("Depth Scale is: ", depth_scale)

        align_to = rs.stream.color
        self.align = rs.align(align_to)

        self.previous_stamp = 0
        self.frame_vect = np.array([])
        self.output = None

        print('Camera running')

        mp_pose = mp.solutions.pose
        self.pose = mp_pose.Pose(static_image_mode=True, min_detection_confidence=0.5)
        self.pose_landmarks = []
        self.final_landmarks = None

    def create_video(self):
        # Check if output.avi already exists
        file_exists = os.path.isfile("videos/video.avi")
        if not file_exists:
            self.output = cv2.VideoWriter(
                "videos/video.avi", cv2.VideoWriter_fourcc(*'mp4v'), 30, (640, 480))
        else:
            # Find an available filename
            index = 1
            while True:
                filename = f"videos/video{index}.avi"
                file_exists = os.path.isfile(filename)
                if not file_exists:
                    self.output = cv2.VideoWriter(
                        filename, cv2.VideoWriter_fourcc(*'mp4v'), 30, (640, 480))
                    break
                index += 1

    def get_frame(self):
        frame = self.pipe.wait_for_frames()
        if frame.get_timestamp() != self.previous_stamp:
            self.previous_stamp = frame.get_timestamp()
            aligned_frames = self.align.process(frame)
            aligned_depth_frame = aligned_frames.get_depth_frame()  # aligned_depth_frame is a 640x480 depth image
            color_frame = aligned_frames.get_color_frame()
            depth_image = np.asanyarray(aligned_depth_frame.get_data())
            color_image = np.asanyarray(color_frame.get_data())
            depth_intrin = aligned_depth_frame.profile.as_video_stream_profile().intrinsics
            self.frame_vect = np.append(self.frame_vect, np.array(frame.get_timestamp()))
            cv2.imshow('Realsense', cv2.flip(color_image, 1))
            if self.recording:
                self.output.write(color_image)
                self.get_landmarks(color_image, depth_intrin, depth_image)


    def get_landmarks(self, color_image, depth_intrin, depth_image):
        results = self.pose.process(cv2.cvtColor(color_image, cv2.COLOR_BGR2RGB))
        if not results.pose_landmarks:
            print('no landmarks')
            return None

        landmarks = results.pose_landmarks.landmark
        self.pose_landmarks = []
        for lm in range(0, 25):
            lmark = landmarks[lm]

            if 0 <= lmark.x < 1 and 0 <= lmark.y < 1:
                pos_x = round(lmark.x * color_image.shape[1])
                pos_y = round(lmark.y * color_image.shape[0])
            else:
                pos_x = 0
                pos_y = 0

            x, y, z = rs.rs2_deproject_pixel_to_point(depth_intrin, [pos_x, pos_y], depth_image[pos_y, pos_x])
            self.pose_landmarks.append(np.array([x, y, z]))

        self.pose_landmarks = np.array(self.pose_landmarks).flatten()
        print(self.pose_landmarks)

        if self.final_landmarks is None:
            self.final_landmarks = self.pose_landmarks
        else:
            self.final_landmarks = np.vstack((self.final_landmarks, self.pose_landmarks))

    def landmarks_to_csv(self, file_path):
        if self.final_landmarks is None:
            print('No landmarks to save')
            return

        # Convierte la lista de arrays en un DataFrame
        df = pd.DataFrame(self.final_landmarks)

        # Crear nombres de columna dinámicamente
        num_landmarks = len(self.final_landmarks[0]) // 3
        column_names = []
        for i in range(num_landmarks):
            column_names.extend([f'x_{i}', f'y_{i}', f'z_{i}'])

        df.columns = column_names

        # Guarda el DataFrame como un archivo CSV
        df.to_csv(file_path, index=False)
        print(f'Landmarks saved to {file_path}')

    def stop(self):
        self.pipe.stop()
        if self.output:
            self.output.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    cam = Camera()

    while True:
        cam.get_frame()

        if cv2.waitKey(1) == ord('r'):
            if not cam.recording:
                cam.recording = True
                cam.create_video()
                print('Recording...')


            else:
                cam.recording = False
                print('Not recording...')

        if cv2.waitKey(1) == ord('q'):
            break

    cam.stop()
    print(cam.final_landmarks)
    cam.landmarks_to_csv("landmarks.csv")


