from time import sleep
from threading import Timer

SEND_DELAY = 0.0002
SET_DELAY = 2


class SerialResponseError(Exception):
    pass


class SerialTimeoutError(Exception):
    pass


class PowerSupplyUnit:
    def __init__(self, com):
        self.com = com
        self.rc_modes = {
            "RM": (b'cont_ps_ext', b'EC'),
            "HM": (b'cps_int_ext', b'EIC'),
            "OFF": (b'cont_ps_int', b'IC'),
        }
        self.rc_mode = "OFF"
        self.model = None
        self.serial = None
        self.soft_ver = None
        self.ui_now = [0, 0]
        self.ui_setted = [0, 0]
        self.load = False
        self.set_block = False

    @staticmethod
    def _frm_bytes(byte_string):
        """
        Convert values from PSU format
        (b'uuuuuu' or b'iiiii' in mV or mA)
        to V or A
        :param byte_string: Values from PSU
        :return: Value in V or A
        """
        return int(byte_string.decode()) / 1000

    @staticmethod
    def _to_bytes(value, size):
        """
        Convert values to PSU format
        (b'uuuuuu' or b'iiiii' in mV or mA)
        from V or A
        :param value: value in
        :param size: size in bytes
        :return:
        """
        return str(int(value * 1000)).zfill(size).encode()

    def reset_set_block(self):
        self.set_block = False

    def rc_mode_select(self, mode="RM"):
        """
        Enabling remote control mode
        Mode RM - Remote mode (only PC control via RS232)
        Mode HM - Hybrid Mode (PC control via RS232 + Buttons on front panel)
        Mode OFF - Disabling remote control mode (default state of the power supply unit (PSU) after reset)
        :param mode: Mode (RM or HM)
        """
        self.com.write(self.rc_modes.get(mode)[0])
        response = self.com.read_until(terminator=b'\r')[:-1]
        sleep(SEND_DELAY)

        if response == b'':
            raise SerialTimeoutError()
        elif response != self.rc_modes.get(mode)[1]:
            raise SerialResponseError(
                f"Invalid response from PSU - {response} (valid is {self.rc_modes.get(mode)[1]})"
            )

        self.rc_mode = mode

    def reset(self):
        """
        Reset PSU with 1 second delay after executing command
        :return: None
        """
        self.com.write(b'c_reset_ext')
        sleep(2)

    def read_ident(self):
        """
        Read identification information from PSU
        :return:
        """
        self.com.write(b'A')
        response = self.com.read_until(terminator=b'\r')[:-1]
        dec_response = response.decode()
        self.model = dec_response[1:3]
        self.serial = dec_response[4:14]
        self.soft_ver = dec_response[15:18]
        sleep(SEND_DELAY)

    def read_ui_setted(self):
        """
        Read voltage and current values that were set by user
        :return: Tuple 'ui_setted'. ui_setted[0] - voltage (V), ui_setted[1] - current (A)
        """
        self.com.write(b'R')
        response = self.com.read_until(terminator=b'\r')[:-1]
        sleep(SEND_DELAY)
        self.ui_setted = (self._frm_bytes(response[7:13]), self._frm_bytes(response[1:6]))

    def read_ui_now(self):
        """
        Measure voltage and current values
        :return: Tuple 'ui_now'. ui_now[0] - voltage (V), ui_now[1] - current (A)
        :return:
        """
        self.com.write(b'M')
        response = self.com.read_until(terminator=b'\r')[:-1]
        if response == b'':
            raise SerialTimeoutError()
        else:
            self.ui_now = (self._frm_bytes(response[7:13]), self._frm_bytes(response[1:6]))
        sleep(SEND_DELAY)

    def turn_on(self):
        """
        Turn On PSU (turn on load)
        :return:
        """
        self.com.write(b'Y')
        response = self.com.read_until(terminator=b'\r')[:-1]
        if response != b'Y':
            raise SerialResponseError(f"Response error from PSU - {response} (valid is b'Y')")
        else:
            self.load = True
        sleep(SEND_DELAY)

    def turn_off(self):
        """
        Turn Off PSU (turn off load)
        :return:
        """
        self.com.write(b'N')
        response = self.com.read_until(terminator=b'\r')[:-1]
        if response != b'N':
            raise SerialResponseError(f"Response error from PSU - {response} (valid is b'N')")
        else:
            self.load = False
        sleep(SEND_DELAY)

    def set_u(self, value):
        """
        :param value: Voltage (V)
        :return:
        """
        if self.set_block is False:
            set_u = b'U' + self._to_bytes(value, 6)
            self.com.write(set_u)
            response = self.com.read_until(terminator=b'\r')[:-1]
            sleep(SEND_DELAY)
            if response != b'U':
                raise SerialResponseError(f"Response error from PSU - {response} (valid is b'U')")

            if self.load is True:
                self.set_block = True
                timer_reset_setblock = Timer(SET_DELAY, self.reset_set_block)
                timer_reset_setblock.start()

    def set_i(self, value):
        """
        :param value: Current (I)
        :return:
        """

        if self.set_block is False:
            set_i = b'I' + self._to_bytes(value, 5)
            self.com.write(set_i)
            response = self.com.read_until(terminator=b'\r')[:-1]
            if response != b'I':
                raise SerialResponseError(f"Response error from PSU - {response} (valid is b'I')")
            sleep(SEND_DELAY)

            if self.load is True:
                timer_reset_setblock = Timer(SET_DELAY, self.reset_set_block)
                timer_reset_setblock.start()


if __name__ == "__main__":
    pass
