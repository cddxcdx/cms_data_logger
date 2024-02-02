# coding = utf-8

import random
import copy
import time
import struct
import libscrc
from config import cfg
from log import LOGGER
from sensor import *
from task_manager import TaskPriority, TaskType

class SensorSender(object):
    def __init__(self, serial, dest = 205):
        self.__s = serial
        self.__dest = int(dest)
        
    def send(self, data):
        try:
            LOGGER.info('Writing data(hex: %s) to serial' % data.hex())
        except:
            LOGGER.info('Writing data(ascii: %s) to serial' % data)
        self.__s.write(data)

    def set_sensor_config(self, tm):
        devices = cfg.get_devices()
        cmds = []
        t = b''
        t1 = b''
        for device_name, device_properity in devices.items():
            model = struct.pack('B',device_properity['Model'])
            addr = struct.pack('>i',device_properity['Address'])[1:]
            iv = device_properity['eigenvalue_upload_rate']
            if not (iv >= 10 and iv <= 86400):
                iv = 10
            interval = struct.pack('<i',iv)
            sample_freq = struct.pack('B',int(device_properity['sample_freq'],16))
            wave_length = struct.pack('B',int(device_properity['wave_length'],2))
            
            t = model + addr + SLEEPINTERVAL_CMD + interval
            data_crc = struct.pack('<H',libscrc.modbus(t))
            tr = FRAME_DATA_HEAD + t + data_crc + FRAME_DATA_END
            cmds.append(tr)
            
            t1 = model + addr + SAMPLEFREQ_WAVELENGTH_CMD + sample_freq + wave_length
            data_crc1 = struct.pack('<H',libscrc.modbus(t1))
            tr1 = FRAME_DATA_HEAD + t1 + data_crc1 + FRAME_DATA_END
            cmds.append(tr1)
            
        if cmds is not []:
            for cmd in cmds:
                tm.add_task(TaskPriority.HIGH, TaskType.DATA_SEND, cmd)
                #time.sleep(1)
    
    def ACK_5A03(self, model, id):
        md = struct.pack('B',model)
        addr = struct.pack('>i',id)[1:]
        t = md + addr + ACK_5A03_CMD
        LOGGER.debug(t)
        data_crc = struct.pack('<H',libscrc.modbus(t))
        tr = FRAME_DATA_HEAD + md + addr + ACK_5A03_CMD + data_crc + FRAME_DATA_END
        return tr
        
    def TRIG_Wavedata(self, tm):
        devices = cfg.get_devices()
        trs = []
        for device_name, device_properity in devices.items():
            model = struct.pack('B',device_properity['Model'])
            addr = struct.pack('>i',device_properity['Address'])[1:]
            t = model + addr + TRIG_0101_CMD + b'\x00\x00\x00\x00'
            LOGGER.debug(t.hex())
            data_crc = struct.pack('<H',libscrc.modbus(t))
            tr = FRAME_DATA_HEAD + t + data_crc + FRAME_DATA_END
            trs.append(tr)
            if trs is not []:
                for tr in trs:
                    tm.add_task(TaskPriority.HIGH, TaskType.DATA_SEND, tr)
                    time.sleep(cfg.get_file_store_rawwave_upload_interval())
        