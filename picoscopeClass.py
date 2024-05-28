import numpy as np
from PyQt5 import QtWidgets, QtCore, QtGui
import ctypes
from picosdk.ps2000a import ps2000a as ps
from picosdk.functions import assert_pico_ok
import keyboard
import time


class PicoscopeController(QtCore.QObject):
    def __init__(self):
        super().__init__()
        self.status = {}
        self.chandle = ctypes.c_int16()
        self.pkToPk = 2000000
        self.frequency = 1  # Hz
        self.running = True

        # Open the device
        self.status["openunit"] = ps.ps2000aOpenUnit(ctypes.byref(self.chandle), None)
        # try:
        #     assert_pico_ok(self.status["openunit"])
        #
        # except:
        #     powerstate = self.status["openunit"]
        #     if powerstate == 282:
        #         self.status["ChangePowerSource"] = ps.ps2000aChangePowerSource(self.chandle, 282)
        #     elif powerstate == 286:
        #         self.status["ChangePowerSource"] = ps.ps2000aChangePowerSource(self.chandle, 286)
        #     else:
        #         raise
        #     assert_pico_ok(self.status["ChangePowerSource"])

        self.set_signal(self.pkToPk, self.frequency)

    def set_signal(self, pkToPk, frequency):
        wave_type = ctypes.c_int16(1)
        sweep_type = ctypes.c_int32(0)
        trigger_type = ctypes.c_int32(0)
        trigger_source = ctypes.c_int32(4)        #trigger_source = ps.PS2000A_SIGGEN_SOFT_TRIG
        shots = 2
        self.status = ps.ps2000aSetSigGenBuiltIn(
            self.chandle, 0, pkToPk, wave_type, frequency, frequency, 0, 1, sweep_type, 0, shots, 0, trigger_type, trigger_source, 1
        )
        #assert_pico_ok(self.status["SetSigGenBuiltIn"])

    def trigger_signal(self):
        self.status = ps.ps2000aSigGenSoftwareControl(self.chandle, 1)
        print('signal triggered')

    def close(self):
        self.running = False
        self.status["close"] = ps.ps2000aCloseUnit(self.chandle)
        assert_pico_ok(self.status["close"])

if __name__ == "__main__":
    pico = PicoscopeController()

    while True:
        if keyboard.is_pressed('R'):
            # Toggle between initial and alternate pkToPk
            pico.trigger_signal()
            # Wait for key release to prevent rapid toggling
            while keyboard.is_pressed('R'):
                time.sleep(0.1)

        if keyboard.is_pressed('Q'):
            break

        time.sleep(0.1)  # Sleep for a short time to reduce CPU usage


