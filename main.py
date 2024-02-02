
import threading
import time
import struct
from log import LOGGER
from config import cfg
from serial_wrapper.serial_wrapper import SerialWrapper
from frame.frame_sniffer import FrameSniffer
from frame.frame_handler import frame_handler_runner
from task_manager.task_manager import  TaskManager
from task_manager import TaskPriority, TaskType, set_datarecv_task_manager, set_datasend_task_manager, get_datasend_task_manager, set_wavedata_trigger_task_manager, set_sensor_config_task_manager
from sensor.sensor_sender import SensorSender
from sensor import set_data_sender, get_data_sender

s = None

def connect():
    serial_cfg = cfg.get_serial_cfg()
    s = SerialWrapper(serial_cfg)
    s.connect()
    s.flush()
    return s


def connection_checker(s):
    while True:
        try:
            if s.is_serial_connected():
                pass
            else:
                LOGGER.error('Serial is not connected, reconnecting...')
                s.reconnect()
                send_notice('Serial Reconnect')                
        except Exception as e:
            LOGGER.error('Serial exception(%s), retry...' % str(e))
        time.sleep(600)

def data_send_runner(sensor_sender, tm):
    LOGGER.info('Start data_send_runner')
    while True:
        t = tm.get_next_task()
        if t:
            try:
                LOGGER.info('New task type(%s)' % str(t.task_type)) 
                if t.task_type == TaskType.DATA_SEND:
                    sensor_sender.send(t.task_data)
            except Exception as e:
                LOGGER.error('data_send_runner exception(%s)' % str(e))
        time.sleep(0.5)
        
def data_receive_runner(s, tm):
    MIN_DATA_LEN = 14
    MAX_BUF =300
    sniffer = FrameSniffer()
    left_data = bytes()

    while True:
        try:
            recv = s.read()
            data = left_data + recv
            LOGGER.debug(data)
            if len(data) >= MIN_DATA_LEN:
                LOGGER.debug('Checking frames...')
                frame_type, frame_body, left_data = sniffer.sniff_frame(data)
                if frame_type:
                    try:
                        tm.add_task(TaskPriority.HIGH, TaskType.FRAME_HANDLING, [frame_type, frame_body])
                    except Exception as e:
                        LOGGER.error('Exception(%s, %s) during handling frame' % (frame, str(e)))                  
            if len(left_data)>=MAX_BUF: #clearup buffer if something unexpected
                left_data = b''
        except Exception as e:
            LOGGER.exception('Serial exception(%s)' % str(e))
            s.disconnect()
            time.sleep(5)
        #time.sleep(5)

def wavedata_timing_runner(tm):# 多台设备需要考虑
    while True:
        time.sleep(cfg.get_file_store_rawwave_upload_rate())
        date_sender = get_data_sender()
        date_sender.TRIG_Wavedata(tm)

def init_sensor_sender(s):
    #dest_device = cfg.get_dest_device()
    sssender = SensorSender(s)    
    return sssender

APP_VERSION = '1.0.0'
def run():
    global s
    LOGGER.info('CMS DataLogger app(%s) starting...' % APP_VERSION)
    
    sensor_sender = get_data_sender()
     
    datasend_task_manager = TaskManager(cfg.get_task_queue_size())
    set_datasend_task_manager(datasend_task_manager)
    t_data_sender = threading.Thread(target=data_send_runner, args=(sensor_sender, datasend_task_manager))
    t_data_sender.start()
    
    sensor_config_task_manager = TaskManager(cfg.get_task_queue_size())
    set_sensor_config_task_manager(sensor_config_task_manager)
    sensor_sender.set_sensor_config(sensor_config_task_manager)
    
    wavedata_trigger_task_manager = TaskManager(cfg.get_task_queue_size())
    set_wavedata_trigger_task_manager(wavedata_trigger_task_manager)
    t_wavedata_timing = threading.Thread(target=wavedata_timing_runner, args=(wavedata_trigger_task_manager,))
    t_wavedata_timing.start()

    datarecv_task_manager = TaskManager(cfg.get_task_queue_size())
    set_datarecv_task_manager(datarecv_task_manager)
    t_data_receiver = threading.Thread(target=data_receive_runner, args=(s, datarecv_task_manager))
    t_data_receiver.start()
    
    t_frame_handler = threading.Thread(target=frame_handler_runner, args=(datarecv_task_manager,))
    t_frame_handler.start()
    
    one_day_sec = 86400
    while True:
        LOGGER.info('Main Heartbeat:%d!'%one_day_sec)
        time.sleep(one_day_sec)

def init():
    global s
    LOGGER.info('CMS DataLogger app(%s) initializing...' % APP_VERSION)
    s = connect()
    LOGGER.info('Device is connected!')
    t_connection_checker = threading.Thread(target=connection_checker, args=(s,))
    t_connection_checker.start()
    LOGGER.info('Connection checker started!')
    
    sensor_sender = init_sensor_sender(s)
    set_data_sender(sensor_sender)

if __name__ == '__main__':
    init()
    run()

