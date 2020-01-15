import sys
from power_supply import *
from connection import *
from time import sleep
from threading import Thread, Lock
from PyQt5 import uic, QtWidgets, QtCore

# Setting display U and I update period in msec
DISPLAY_UPDATE_PERIOD = 200
# Setting data from PSU update period in msec
DATA_UPDATE_PERIOD = 100


def launch_in_thread(func):
    def wrapper(*args, **kwargs):
        Thread(target=func, args=args, kwargs=kwargs).start()
    return wrapper


class ReadUINow(Thread):
    def __init__(self, main_window, power_supply_unit):
        self.main_window = main_window
        self.psu = power_supply_unit
        super().__init__()

    def run(self):
        while self.main_window.allow_readuinow:
            sleep(DATA_UPDATE_PERIOD / 1000)
            if self.main_window.allow_readuinow is False:
                break
            with self.psu.com.mutex:
                self.psu.read_ui_now()


class MyWindow(QtWidgets.QMainWindow):
    def __init__(self, power_supply_unit):
        super().__init__()
        uic.loadUi("./qt/main.ui", self)
        self.psu = power_supply_unit
        self.setWindowTitle("Б5-71/х-ПРО Remote Control Programm")
        self.setFixedSize(700, 150)

        self.allow_readuinow = True
        self.display_timer = QtCore.QTimer()
        self.display_timer.timeout.connect(self.update_ui_now)
        self.display_timer.start(DISPLAY_UPDATE_PERIOD)
        sleep(0.5)
        self.read_ui_setted()

        self.pushButton_init.clicked.connect(self.initialize)
        self.radioButton_mode_hm.clicked.connect(self.set_mode)
        self.radioButton_mode_rm.clicked.connect(self.set_mode)
        self.radioButton_mode_off.clicked.connect(self.set_off)
        self.on_off_button.clicked.connect(self.turn)
        self.pushButton_set_values.clicked.connect(self.set_values)

    def closeEvent(self, *args, **kwargs):
        # Set HM mode before exit
        self.set_mode()

    @launch_in_thread
    def initialize(self, *args, **kwargs):
        with self.psu.com.mutex:
            self.psu.read_ident()

        self.label_model.setText(f"Model: {self.psu.model}")
        self.label_serial.setText(f"Serial: {self.psu.serial}")
        self.label_soft_ver.setText(f"Soft ver.: {self.psu.soft_ver}")
        sleep(DATA_UPDATE_PERIOD / 1000)

    def update_ui_now(self):
        self.lcd_u.display(self.psu.ui_now[0])
        self.lcd_i.display(self.psu.ui_now[1])

    @launch_in_thread
    def set_mode(self, *args, **kwargs):
        rc_modes = {
            "HM": self.radioButton_mode_hm.isChecked(),
            "RM": self.radioButton_mode_rm.isChecked(),
        }
        for key in rc_modes:
            if rc_modes[key] is True:
                selected_rc_mode = key
                break
            else:
                selected_rc_mode = "HM"

        with self.psu.com.mutex:
            self.psu.rc_mode_select(mode=selected_rc_mode)

        self.allow_readuinow = True

        read_thread = ReadUINow(self, self.psu)
        read_thread.setDaemon(daemonic=True)
        read_thread.start()

    @launch_in_thread
    def set_off(self, *args, **kwargs):
        self.allow_readuinow = False
        with self.psu.com.mutex:
            self.psu.rc_mode_select(mode="OFF")

        self.psu.ui_now = [0, 0]

    @launch_in_thread
    def set_values(self, *args, **kwargs):
        if self.psu.rc_mode != "OFF":
            with self.psu.com.mutex:
                u_for_set = round(self.doubleSpinBox_u.value(), 2)
                self.psu.set_u(u_for_set)
                i_for_set = round(self.doubleSpinBox_i.value(), 3)
                self.psu.set_i(i_for_set)

    @launch_in_thread
    def turn(self, *args, **kwargs):
        with self.psu.com.mutex:
            if self.psu.load is False:
                self.psu.turn_on()
            else:
                self.psu.turn_off()

    @launch_in_thread
    def read_ui_setted(self):
        with psu.com.mutex:
            self.psu.read_ui_setted()

        self.doubleSpinBox_u.setValue(window.psu.ui_setted[0])
        self.doubleSpinBox_i.setValue(window.psu.ui_setted[1])


if __name__ == "__main__":
    # Com port init
    com_port = com_init(port="COM1", speed=9600)
    com_port.open()
    com_port.mutex = Lock()
    # Making instance of PSU
    psu = PowerSupplyUnit(com_port)
    # Creating main window
    app = QtWidgets.QApplication(sys.argv)
    window = MyWindow(psu)
    window.show()

    sys.exit(app.exec_())
