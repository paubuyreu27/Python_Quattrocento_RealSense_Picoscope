import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel
from PyQt5 import QtCore
from PyQt5.QtCore import QTimer
from multiprocess_qt import MultiprocessQt
from picoscopeClass import PicoscopeController


# Clase principal que hereda de QMainWindow
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Configuración de la ventana principal
        self.setWindowTitle("Ventana Principal")
        self.setGeometry(100, 100, 600, 400)  # x, y, ancho, alto

        # Crear una etiqueta (QLabel) para mostrar el número
        self.label = QLabel("0", self)
        self.label.setGeometry(250, 150, 100, 50)  # x, y, ancho, alto
        self.label.setStyleSheet("font-size: 24px;")

        # Inicializar el contador
        self.counter = 0

        # Multiprocessing
        self.cam = MultiprocessQt()

        # Picoscope
        self.picoscope = PicoscopeController()


        # Configurar un temporizador (QTimer) para actualizar el número
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_data)
        self.timer.start()

    def update_data(self):
        # Incrementar el contador
        self.counter += 1
        # Actualizar el texto de la etiqueta
        self.label.setText(str(self.counter))

        # Camera
        self.cam.update_process()

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Space:  # Aquí puedes cambiar la tecla según tus necesidades
            if not self.cam.start_recording:
                self.cam.start_recording = True
                self.picoscope.trigger_signal()
            else:
                self.cam.start_recording = False
                self.cam.end_recording = True
            print("Tecla presionada, Recording:", self.cam.start_recording)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Crear una instancia de la ventana principal
    main_window = MainWindow()
    main_window.show()

    # Ejecutar la aplicación
    sys.exit(app.exec_())
