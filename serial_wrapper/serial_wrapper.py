#coding=utf-8

import time
import serial
from log import LOGGER

class SerialWrapper():
    def __init__(self, cfg):
        self.port = cfg['port']
        self.__baud_rate = cfg['baud_rate']
        self.timeout = cfg['timeout']
        self.read_size = cfg['read_size']
        self.serial = None

    def is_serial_connected(self):
        return self.serial and self.serial.isOpen()
        
    def connect(self):
        if self.is_serial_connected():
            return True
        while True:
            try:
                self.serial = serial.Serial(self.port, self.__baud_rate, timeout=self.timeout)
                break
            except Exception as e:
                LOGGER.error('Serial connect exception(%s), retry...' % str(e))
                time.sleep(120)
        return True

    def disconnect(self):
        if self.serial:
            self.serial.close()
            self.serial = None

    def reconnect(self):
        LOGGER.warn('Serial reconnecting')
        self.disconnect()
        self.connect()

    
    def flush(self):
        try:
            self.serial.flush()
        except Exception as e:
            LOGGER.error('Serial flush exception(%s), retry...' % str(e))
            self.reconnect()
            self.serial.flush()

    def write(self, data):
        try:
            return self.serial.write(data)
        except Exception as e:
            LOGGER.error('Serial write exception(%s), retry...' % str(e))
            self.reconnect()
            return self.serial.write(data)

    def read_line(self):
        try:
            return self.serial.readline()
        except Exception as e:
            LOGGER.error('Serial readline exception(%s), retry...' % str(e))
            self.reconnect()
            return self.serial.readline()

    def read(self, size=None):
        try:
            if size:
                return self.serial.read(size)
            else:
                return self.serial.read(self.read_size)
        except Exception as e:
            LOGGER.error('Serial read exception(%s), retry...' % str(e))
            self.reconnect()
            if size:
                return self.serial.read(size)
            else:
                return self.serial.read(self.read_size)


