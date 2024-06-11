import sys
import pandas as pd
import numpy as np

from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QWidget
from PyQt5.QtCore import QTimer
from PyQt5 import QtCore
import pyqtgraph as pg

from multiprocess_qt import MultiprocessQt
from picoscopeClass import PicoscopeController
import config
import config_functions as cf
import stream_data


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        ###############################################################################################################
        # Config. Window
        ###############################################################################################################

        self.setWindowTitle("Main Window")
        self.setGeometry(0, 0, 1200, 800)  # x, y, ancho, alto
        self.setStyleSheet("background-color: black;")

        ###############################################################################################################
        # Plot Widget
        ###############################################################################################################

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        self.plot_widget = pg.PlotWidget(title="Plot Title", color="w")
        self.plot_widget.setBackground('k')  # Establecer fondo negro
        self.plot_widget.getPlotItem().getAxis('left').setPen('w')  # Eje y blanco
        self.plot_widget.getPlotItem().getAxis('bottom').setPen('w')  # Eje x blanco

        layout.addWidget(self.plot_widget)

        ###############################################################################################################
        # Recording Button
        ###############################################################################################################

        self.button = QPushButton("Start Recording", self)
        self.button.setGeometry(10, 10, 110, 35)  # x, y, ancho, alto
        self.button.setStyleSheet("background-color: white; color: black; font-size: 12px;")
        self.button.clicked.connect(self.toggle_recording)
        self.recording_state = 0  # 0: Not recording, 1: Recording, 2: Saving Files
        self.signal_recording = False  # Variable to save amplifier signal

        ###############################################################################################################
        # Frame counter (test)
        ###############################################################################################################

        self.label = QLabel("0", self)
        self.label.setGeometry(130, 10, 30, 35)  # x, y, ancho, alto
        self.label.setStyleSheet("font-size: 12px; color: white;")

        self.frame_counter = 0
        self.threshold = 0

        ###############################################################################################################
        # Set up files, camera and Picoscope
        ###############################################################################################################

        # File name and number
        self.record_file_path, self.file_number = cf.get_available_filename("signal_recordings/signal_recording",
                                                                            "csv")

        # Multiprocessing
        self.cam = MultiprocessQt(self.file_number)

        # Picoscope
        self.picoscope = PicoscopeController()

        ###############################################################################################################
        # Connect to Amplifier
        ###############################################################################################################

        # Socket Connection
        if config.used_amp == 'QUATTROCENTO':
            self.ip_address = config.ip_address
            self.port = config.port

            (self.start_command,
             self.number_of_channels,
             self.sample_frequency,
             self.bytes_in_sample) = stream_data.create_bin_command(start=1)
            self.connection = stream_data.connect_to_qc(self.ip_address, self.port, self.start_command)

        # Channels selected in config file
        self.list_used_channels = cf.select_channels(config.list_used_inputs)
        self.all_channel_names = [cf.get_channel_name(channel) for channel in self.list_used_channels]

        # Sample to graph in each iteration
        self.data_interval = config.data_interval

        ###############################################################################################################
        # Select channels to plot (Initialization)
        ###############################################################################################################

        # Select number of channels to plot
        max_num_channels_plot = config.max_channels_to_plot
        self.current_channel_index = 0
        if len(self.list_used_channels) < max_num_channels_plot:
            self.num_plot_channels = len(self.list_used_channels)
        else:
            self.num_plot_channels = max_num_channels_plot

        # Index in selected channels
        self.plot_channels = self.list_used_channels[self.current_channel_index:
                                                     self.current_channel_index + self.num_plot_channels]
        self.channel_names = [cf.get_channel_name(channel) for channel in self.plot_channels]

        # Set title axis and colors
        self.plot_widget.setTitle(f"Channels {', '.join(self.channel_names)}")
        self.update_y_axis_labels()
        self.pen_colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255),
                           (128, 0, 0), (0, 128, 0)]
        while len(self.pen_colors) < self.num_plot_channels:
            self.pen_colors += self.pen_colors
        self.pen_colors = self.pen_colors[:self.num_plot_channels]

        ###############################################################################################################
        # Set plot data (empty)
        ###############################################################################################################

        self.rec_signal_matrix = None  # Matrix to save signals
        self.x = np.array(range(-config.samples_in_plot, 0))
        self.y = np.zeros((config.samples_in_plot, self.num_plot_channels), dtype=int)
        self.data_lines = []

        for i in range(self.num_plot_channels):
            pen = pg.mkPen(color=self.pen_colors[i])  # Asigna el color correspondiente
            line = self.plot_widget.plot(self.x, self.y[:, i], pen=pen)  # Crea la línea de datos para cada canal
            self.data_lines.append(line)

        ###############################################################################################################
        # Start App
        ###############################################################################################################

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_data)
        self.timer.start()

    ###################################################################################################################
    # Application Loop
    ###################################################################################################################

    def update_data(self):
        # Update frame counter
        self.frame_counter += 1
        self.label.setText(str(self.frame_counter))

        # Camera
        self.cam.update_process()

        # Close when processes are finished
        if self.cam.closed:
            QApplication.quit()

        # Plot data
        data_matrix = []
        interval_matrix = []
        self.x = self.x[self.data_interval:]
        self.x = np.hstack((self.x, np.array(range(self.x[-1] + 1, self.x[-1] + self.data_interval + 1))))
        self.y = self.y[self.data_interval:]

        for i in range(self.data_interval):
            emg_data_frame = np.array(stream_data.read_signal(self.connection,
                                                              self.number_of_channels,
                                                              self.bytes_in_sample,
                                                              output_milli_volts=True))
            data_matrix.append(emg_data_frame)
        interval_matrix = np.vstack(data_matrix)

        self.y = np.vstack((self.y, interval_matrix[:, self.list_used_channels[self.current_channel_index:
                                                                               self.current_channel_index +
                                                                               self.num_plot_channels]]))
        for i in range(self.num_plot_channels):
            self.data_lines[i].setData(self.x, self.y[:, i] - config.arbitrary_distance_plot_channels * i)

        # Save interval if recording
        if self.signal_recording:
            if self.rec_signal_matrix is None:
                self.rec_signal_matrix = interval_matrix[:, self.list_used_channels]
            else:
                self.rec_signal_matrix = np.vstack((self.rec_signal_matrix,
                                                    interval_matrix[:, self.list_used_channels]))

    ###################################################################################################################
    # Button Activated
    ###################################################################################################################

    def toggle_recording(self):
        if self.recording_state == 0:
            self.button.setText("Stop Recording")
            self.signal_recording = True
            self.cam.start_recording = True  # Start sending frames
            self.picoscope.trigger_signal()  # Trigger Picoscope
            self.recording_state = 1
            self.frame_counter = 0

        elif self.recording_state == 1:
            self.cam.start_recording = False  # Stop sending frames
            self.signal_recording = False
            self.record_signal_csv()  # Save signals to csv
            self.cam.end_recording = True  # Send signal to frames processing to finish
            self.button.setText("Saving Files")
            self.recording_state = 2

        else:
            self.button.setText("Start Recording")
            self.recording_state = 0

    ###################################################################################################################
    # Change channels to view
    ###################################################################################################################

    # If down/up arrow is pressed, change the index for plot_channels
    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Down:  # Down Arrow
            if self.current_channel_index < len(self.list_used_channels) - self.num_plot_channels:
                self.current_channel_index += 1
                self.update_plot_channels()
        elif event.key() == QtCore.Qt.Key_Up:  # Up Arrow
            if self.current_channel_index > 0:
                self.current_channel_index -= 1
                self.update_plot_channels()

    # Change plot_channels and title
    def update_plot_channels(self):
        self.plot_channels = self.list_used_channels[self.current_channel_index:
                                                     self.current_channel_index + self.num_plot_channels]
        self.channel_names = [cf.get_channel_name(channel) for channel in self.plot_channels]
        self.plot_widget.setTitle(f"Channels {', '.join(self.channel_names)}")
        self.update_y_axis_labels()

    # Change y-axis ticks
    def update_y_axis_labels(self):
        ticks = [(i * -config.arbitrary_distance_plot_channels, name) for i, name in enumerate(self.channel_names)]
        ax = self.plot_widget.getAxis('left')
        ax.setTicks([ticks])

    ###################################################################################################################
    # Save signals to csv
    ###################################################################################################################

    def record_signal_csv(self):
        if self.rec_signal_matrix is not None:
            print('Before trim', self.rec_signal_matrix.shape)
            rec_signal_matrix_trim, self.threshold = cf.trim_matrix(self.rec_signal_matrix, self.data_interval)
            print('After trim', rec_signal_matrix_trim.shape, 'Threshold', self.threshold)

            df_rec = pd.DataFrame(rec_signal_matrix_trim)  # Create DataFrame
            df_rec.columns = self.all_channel_names  # Set column names
            df_rec.to_csv(self.record_file_path, index=False)  # Save to csv
            print('Signals saved to ', self.record_file_path)
        else:
            print('No signals recorded')

    ###################################################################################################################
    # Forced Close
    ###################################################################################################################

    def closeEvent(self, event):
        self.timer.stop()
        self.cam.terminate_process()
        event.accept()

    ###################################################################################################################


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Crear una instancia de la ventana principal
    main_window = MainWindow()
    main_window.show()

    # Ejecutar la aplicación
    sys.exit(app.exec_())
