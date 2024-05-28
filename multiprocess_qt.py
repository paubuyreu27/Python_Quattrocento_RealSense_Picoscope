import multiprocessing as mproc
from PyQt5 import QtWidgets, QtCore, QtGui
from mp_frame_process import MpFrameProcess
from camera import Camera
import cv2


class MultiprocessQt(QtCore.QObject):
    def __init__(self):
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
        self.stop_loop = False

        # multiproc config
        self.color_queue = mproc.Queue()
        self.depth_queue = mproc.Queue()
        self.stop_queue = mproc.Queue()
        self.read_proc = MpFrameProcess(color_queue=self.color_queue, depth_queue=self.depth_queue,
                                        stop_queue=self.stop_queue, intrinsics=depth_intrinsic_dict)

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

    def stop_process(self):
        self.read_proc.join()
        print("Process finished")
        self.cam.stop()
        self.stop_loop = True

if __name__ == '__main__':
    mprocess = MultiprocessQt()

    while not mprocess.stop_loop:
        mprocess.update_process()

        if cv2.waitKey(1) == ord('r'):
            if not mprocess.start_recording:
                mprocess.start_recording = True
                print('Recording...')

            else:
                mprocess.start_recording = False
                print('Stopped Recording')
                mprocess.end_recording = True

