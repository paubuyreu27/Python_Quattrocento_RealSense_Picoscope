import multiprocessing as mproc
import pandas as pd
import sys
import numpy as np
import pyqtgraph as pg
from PyQt5 import QtWidgets, QtCore
from mp_frame_process import MpFrameProcess
from camera import Camera

import config
import config_functions as cf
import stream_data
from picoscopeClass import PicoscopeController


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        self.graphWidget = pg.PlotWidget()
        self.setCentralWidget(self.graphWidget)



        # Conexión Quattrocento
        if config.used_amp == 'QUATTROCENTO':
            self.ip_address = config.ip_address
            self.port = config.port
            (self.start_command,
             self.number_of_channels,
             self.sample_frequency,
             self.bytes_in_sample) = stream_data.create_bin_command(start=1)
            self.connection = stream_data.connect_to_qc(self.ip_address, self.port, self.start_command)

        self.list_used_channels = cf.select_channels(config.list_used_inputs)

        self.current_channel_index = 0  # Canal inicial
        if len(self.list_used_channels) < 8:
            self.num_plot_channels = len(self.list_used_channels)
        else:
            self.num_plot_channels = 8

        self.plot_channels = self.list_used_channels[self.current_channel_index:
                                                     self.current_channel_index + self.num_plot_channels]
        self.channel_names = [cf.get_channel_name(channel) for channel in self.plot_channels]
        self.all_channel_names = [cf.get_channel_name(channel) for channel in self.list_used_channels]

        self.data_matrix = []
        self.data_interval = 68

        self.recording = False
        self.record_file_path = "recordings/recording.csv"
        self.rec_matrix = np.zeros((1, len(self.list_used_channels)))
        self.time_stamps_amp = []

        # Datos iniciales vacíos
        self.x = np.array(range(-config.samples_in_plot, 0))
        self.y = np.zeros((config.samples_in_plot, self.num_plot_channels), dtype=int)

        self.graphWidget.setBackground('k')

        self.recording_label = QtWidgets.QLabel(self)
        self.recording_label.setGeometry(60, 10, 200, 20)
        self.update_recording_label()

        self.graphWidget.setTitle(f"Channels {', '.join(self.channel_names)}")
        self.update_y_axis_labels()

        self.pen_colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255),
                           (128, 0, 0), (0, 128, 0)]
        while len(self.pen_colors) < self.num_plot_channels:
            self.pen_colors += self.pen_colors
        self.pen_colors = self.pen_colors[:self.num_plot_channels]

        self.data_lines = []

        for i in range(self.num_plot_channels):
            pen = pg.mkPen(color=self.pen_colors[i])  # Asigna el color correspondiente
            line = self.graphWidget.plot(self.x, self.y[:, i], pen=pen)  # Crea la línea de datos para cada canal
            self.data_lines.append(line)

        # Camera initialization
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

        # Picoscope
        self.picoscope = PicoscopeController()

        # Timer + Intervalo para actualizar
        self.timer = QtCore.QTimer()
        # self.timer.setInterval(1) # Mirar que interval no sigui massa curt/llarg
        self.timer.timeout.connect(self.update_data)
        self.timer.start()
        print('App started')

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Down:  # Flecha hacia abajo
            if self.current_channel_index < len(self.list_used_channels) - self.num_plot_channels:
                self.current_channel_index += 1
                self.update_plot_channels()
        elif event.key() == QtCore.Qt.Key_Up:  # Flecha hacia arriba
            if self.current_channel_index > 0:
                self.current_channel_index -= 1
                self.update_plot_channels()
        elif event.key() == QtCore.Qt.Key_R:  # Tecla "r"
            if not self.recording:
                self.picoscope.trigger_signal()
                self.recording = True
                self.start_recording = True
                print('Started Recording')
            else:
                self.end_recording = True
                self.recording = False
                self.start_recording = False
                print('Stopped Recording')
            self.update_recording_label()
            self.update_data()

    def update_plot_channels(self):  # Only used for title
        self.plot_channels = self.list_used_channels[self.current_channel_index:
                                                     self.current_channel_index + self.num_plot_channels]
        self.channel_names = [cf.get_channel_name(channel) for channel in self.plot_channels]
        self.graphWidget.setTitle(f"Channels {', '.join(self.channel_names)}")
        self.update_y_axis_labels()

    def update_y_axis_labels(self):
        ticks = [(i * -20, name) for i, name in enumerate(self.channel_names)]
        ax = self.graphWidget.getAxis('left')
        ax.setTicks([ticks])

    def record_csv(self):
        self.recording = False
        self.record_file_path = cf.get_available_filename("recordings/recording", "csv")
        df_rec = pd.DataFrame(self.rec_matrix[1:])
        df_rec.columns = self.all_channel_names
        df_rec.to_csv(self.record_file_path, index=False)

        self.rec_matrix = np.zeros((1, len(self.list_used_channels)))
        print('File Saved to, ', self.record_file_path)

    def update_recording_label(self):
        if self.recording:
            self.recording_label.setText("Recording")
            self.recording_label.setStyleSheet("color: green")
        else:
            self.recording_label.setText("Not Recording")
            self.recording_label.setStyleSheet("color: blue")

    def update_data(self):
        # Camera update process
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

        # Plot data
        self.x = self.x[self.data_interval:]
        self.x = np.hstack((self.x, np.array(range(self.x[-1] + 1, self.x[-1] + self.data_interval + 1))))
        self.y = self.y[self.data_interval:]
        self.data_matrix = []

        for i in range(self.data_interval):
            emg_data_frame = np.array(stream_data.read_emg_signal(self.connection,
                                                                  self.number_of_channels,
                                                                  self.bytes_in_sample,
                                                                  output_milli_volts=True))
            self.data_matrix.append(emg_data_frame)

        final_matrix = np.vstack(self.data_matrix)

        if self.recording:
            self.rec_matrix = np.vstack((self.rec_matrix, final_matrix[:, self.list_used_channels]))

        self.y = np.vstack((self.y, final_matrix[:, self.list_used_channels[
                                                    self.current_channel_index:self.current_channel_index + self.num_plot_channels]]))
        for i in range(self.num_plot_channels):
            self.data_lines[i].setData(self.x, self.y[:, i] - 20 * i)

    def stop_process(self):
        self.read_proc.join()
        print("Process finished")
        self.cam.stop()
        self.stop_loop = True
        self.record_csv()

    def closeEvent(self, event):
        self.read_proc.terminate()
        print("Camera process terminated")
        # self.picoscope.close()  # Ensure the Picoscope is properly closed
        event.accept()


app = QtWidgets.QApplication(sys.argv)
w = MainWindow()
w.show()
sys.exit(app.exec_())
