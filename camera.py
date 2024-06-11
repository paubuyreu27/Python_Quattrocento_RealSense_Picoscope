import pyrealsense2 as rs
import numpy as np
import cv2


# class Camera(QtCore.QObject):
class Camera:
    def __init__(self):
        self.pipe = rs.pipeline()
        self.cfg = rs.config()
        self.cfg.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
        self.cfg.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
        profile = self.pipe.start(self.cfg)

        depth_sensor = profile.get_device().first_depth_sensor()
        depth_scale = depth_sensor.get_depth_scale()
        # print("Depth Scale is: ", depth_scale)

        align_to = rs.stream.color
        self.align = rs.align(align_to)

        self.previous_stamp = 0
        self.initial_timestamp = None
        self.abs_timestamp = None
        self.rest_timestamp = None

        self.depth_image = None
        self.depth_intrin = None
        self.color_image = None
        self.get_frame()
        self.depth_image = None
        self.color_image = None
        print('Camera running')

    def get_frame(self):
        frame = self.pipe.wait_for_frames()
        if frame.get_timestamp() != self.previous_stamp:
            self.previous_stamp = frame.get_timestamp()
            if self.initial_timestamp is None:
                self.initial_timestamp = frame.get_timestamp()

            self.abs_timestamp = frame.get_timestamp()
            self.rest_timestamp = frame.get_timestamp() - self.initial_timestamp

            aligned_frames = self.align.process(frame)
            aligned_depth_frame = aligned_frames.get_depth_frame()  # aligned_depth_frame is a 640x480 depth image
            color_frame = aligned_frames.get_color_frame()
            self.depth_image = np.asanyarray(aligned_depth_frame.get_data())
            self.color_image = np.asanyarray(color_frame.get_data())

            if self.depth_intrin is None:
                self.depth_intrin = aligned_depth_frame.profile.as_video_stream_profile().intrinsics
            # self.frame_vect = np.append(self.frame_vect, np.array(frame.get_timestamp()))

            cv2.imshow('Realsense', cv2.flip(self.color_image, 1))

        else:
            self.color_image = None
            self.depth_image = None

    def stop(self):
        self.pipe.stop()
        cv2.destroyAllWindows()




