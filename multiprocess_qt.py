import multiprocessing as mproc

import numpy as np
from PyQt5 import QtWidgets, QtCore, QtGui
from mp_frame_process import MpFrameProcess
from camera import Camera
import cv2
import config_functions as cf
import pandas as pd


class MultiprocessQt(QtCore.QObject):
    def __init__(self, file_number):
        super().__init__()

        self.cam = Camera()
        depth_intrin = self.cam.depth_intrin

        depth_intrinsic_dict = {
            'width': depth_intrin.width,
            'height': depth_intrin.height,
            'ppx': depth_intrin.ppx,
            'ppy': depth_intrin.ppy,
            'fx': depth_intrin.fx,
            'fy': depth_intrin.fy,
            'model': depth_intrin.model,
            'coeffs': depth_intrin.coeffs
        }

        self.start_recording = False
        self.end_recording = False
        self.closed = False

        self.timestamps_absolut = None
        self.timestamps_rest = None
        self.file_number = file_number

        # multiproc config
        self.color_queue = mproc.Queue()
        self.depth_queue = mproc.Queue()
        self.stop_queue = mproc.Queue()
        self.read_proc = MpFrameProcess(color_queue=self.color_queue, depth_queue=self.depth_queue,
                                        stop_queue=self.stop_queue, intrinsics=depth_intrinsic_dict,
                                        file_number=self.file_number)

        self.read_proc.start()  # Start the process here
        print('Queues started')

    def update_process(self):
        self.cam.get_frame()

        if not self.stop_queue.empty():
            self.stop_process()

        if self.end_recording:
            color_image = None
            depth_image = None
            self.color_queue.put(color_image)
            self.depth_queue.put(depth_image)

        if self.start_recording:
            if self.cam.color_image is not None:
                self.color_queue.put(self.cam.color_image)
                self.depth_queue.put(self.cam.depth_image)
                self.store_timestamps()

    def store_timestamps(self):
        if self.timestamps_absolut is None:
            self.timestamps_absolut = self.cam.abs_timestamp
            self.timestamps_rest = self.cam.rest_timestamp
        else:
            self.timestamps_absolut = np.vstack((self.timestamps_absolut, self.cam.abs_timestamp))
            self.timestamps_rest = np.vstack((self.timestamps_rest, self.cam.rest_timestamp))

    def timestamps_csv(self):
        if self.timestamps_absolut is not None:
            times = np.hstack((self.timestamps_absolut, self.timestamps_rest))
            filename = cf.get_number_filename('camera_timestamps/timestamps', '.csv',
                                              self.file_number)
            df_time = pd.DataFrame(times)  # Create DataFrame
            df_time.columns = ["Time", "Time - Initial"]  # Set column names
            df_time.to_csv(filename, index=False)  # Save to csv
            print('Timestamps saved to ', filename)
        else:
            print('No timestamps to save')

    def stop_process(self):
        self.read_proc.join()
        self.timestamps_csv()
        print("Processes finished")
        self.cam.stop()
        self.closed = True

    def terminate_process(self):
        self.read_proc.terminate()
        print("Process terminated")
        self.cam.stop()


if __name__ == '__main__':
    mprocess = MultiprocessQt()

    while not mprocess.closed:
        mprocess.update_process()

        if cv2.waitKey(1) == ord('r'):
            if not mprocess.start_recording:
                mprocess.start_recording = True
                print('Recording...')

            else:
                mprocess.start_recording = False
                print('Stopped Recording')
                mprocess.end_recording = True

