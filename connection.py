import serial


def com_init(port="COM1", speed=9600):
    timeout_default = 2
    com_port = serial.Serial()
    com_port.baudrate = speed
    com_port.port = port
    com_port.bytesize = 8
    com_port.parity = 'N'
    com_port.stopbits = 1
    com_port.timeout = None
    com_port.xonxoff = 0
    com_port.rtscts = 0
    com_port.timeout = timeout_default
    com_port.write_timeout = timeout_default

    return com_port


if __name__ == "__main__":
    pass
