import multiprocessing as mproc
from camera import Camera

class Multiprocess:
    def __init__(self):
        self.camera = Camera()
        self.queue = mproc.Queue()
        self.camera_process = mproc.Process(target=self.get_frames_show)
        self.mediapipe_process = mproc.Process(target=self.get_frames_landmarks)
        self.recording = False
        self.running = True
        self.final = False
        self.depth_intrin = None

    def get_frames_show(self):
        while self.running:
            self.camera.get_frame()
            color_image = self.camera.color_image
            depth_image = self.camera.depth_image
            if self.depth_intrin is None:
                self.depth_intrin = self.camera.depth_intrin

            if self.recording:
                self.queue.put(color_image, depth_image)

            if self.final:
                self.queue.put(None)  # Señal para que el consumidor termine

    def get_frames_landmarks(self):
        while self.recording:
            color_image, depth_image = self.queue.get()
            self.camera.get_landmarks(color_image, self.depth_intrin, depth_image)

            if color_image is None:  # Si recibe la señal de término, rompe el bucle
                break

    def start(self):
        self.camera_process.start()
        self.mediapipe_process.start()

    def join(self):
        self.camera_process.join()
        self.mediapipe_process.join()
        print('Fin del procesamiento')
        self.camera.landmarks_to_csv()


if __name__ == '__main__':
    pc = Multiprocess()
    pc.start()
    pc.join()