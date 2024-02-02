import time, datetime, os, struct
import libscrc
from log import LOGGER
from config import cfg
from task_manager import TaskPriority, TaskType, get_datasend_task_manager, get_wavedata_trigger_task_manager, get_sensor_config_task_manager
from sensor import *
from pathlib import *

count = 0
wavedata_count = 0
wavedatas = ''
datas = ''

col_names = '时间,频率_X(Hz),频率_Y(Hz),频率_Z(Hz),加速度峰值_X(m/s2),加速度峰值_Y(m/s2),加速度峰值_Z(m/s2),速度有效值-烈度_X(mm/s),速度有效值-烈度_Y(mm/s),速度有效值-烈度_Z(mm/s),位移峰峰值_X(um),位移峰峰值_Y(um),位移峰峰值_Z(um),倾角_X(度),倾角_Y(度),倾角_Z(度),温度(℃),电压(V),休眠时间(秒)\n'

col_names_5a03_ = '时间,加速度峰值_X(m/s2),加速度峰值_Y(m/s2),加速度峰值_Z(m/s2),速度有效值-烈度_X(mm/s),速度有效值-烈度_Y(mm/s),速度有效值-烈度_Z(mm/s),位移峰峰值_X(um),位移峰峰值_Y(um),位移峰峰值_Z(um),温度(℃),电压(V),休眠时间(秒)\n'

col_names_0102 = '帧号,字节数,数据\n'

def bytes2int(bdata, byteorder='little'):
    return int.from_bytes(bdata, byteorder, signed=False)

def save_to_csv(data,col_names,fn):
    dir = cfg.get_file_store_eigenvalue_directory()
    f_name = fn+'.csv'
    f_path = os.path.join(dir, f_name)
    if not os.path.exists(f_path):
        data = col_names + data
    with open(f_path,'a') as f:
        f.write(data)

def get_s16(val):
    if val < 0x8000:
        return val
    else:
        return (val - 0x10000)
        
def save_to_onefile(fn_dir):
    s = ''
    vs = []
    with open(fn_dir, 'r') as f:
        cs = f.readlines()
    fn = os.path.basename(fn_dir)
    frame_size = int(fn.split('_')[3])
    for c in cs[1:]:
        LOGGER.debug(c)
        s = s + c.split(',')[2][:-1]
        LOGGER.debug(s)
    s_hex = bytes().fromhex(s)
    if len(s_hex) >= (frame_size - 1) * 62:
        for i in range(0,len(s_hex),2):
            v = get_s16(bytes2int(s_hex[i:i+2], byteorder='little'))/100
            vs.append(str(v))
        save_to_csv(','.join(vs), '', fn.replace('.csv', '.p'))
    else:
        LOGGER.info('Length too small')

def search_wavedata_file(dir,device_ID):
    pattern = 'wavedata_*_ID%s*.csv'%device_ID
    newest_fn_dt = [None, '0']
    for i in Path(dir).glob(pattern):
        ts = str(i).split('_')[1]
        if ts > newest_fn_dt[1]:
            newest_fn_dt = [i,ts]
    LOGGER.debug(newest_fn_dt[0])
    return str(newest_fn_dt[0])

def handle_5C03(frame_type, frame_body, tm):
    global count, datas
    LOGGER.info('Handling 5C03...')
    try:
        assert frame_type.find(b'\x5C\x03') == 0
        device_ID = bytes2int(frame_body[4:7], byteorder='big')
        X_freq = bytes2int(frame_body[9:11], byteorder='little')
        Y_freq = bytes2int(frame_body[11:13], byteorder='little')
        Z_freq = bytes2int(frame_body[13:15], byteorder='little')
        X_acc_max = bytes2int(frame_body[15:17], byteorder='little')/100.0
        Y_acc_max = bytes2int(frame_body[17:19], byteorder='little')/100.0
        Z_acc_max = bytes2int(frame_body[19:21], byteorder='little')/100.0
        X_vel_rms = bytes2int(frame_body[21:23], byteorder='little')/100.0
        Y_vel_rms = bytes2int(frame_body[23:25], byteorder='little')/100.0
        Z_vel_rms = bytes2int(frame_body[25:27], byteorder='little')/100.0
        X_disp_mm = bytes2int(frame_body[27:29], byteorder='little')
        Y_disp_mm = bytes2int(frame_body[29:31], byteorder='little')
        Z_disp_mm = bytes2int(frame_body[31:32], byteorder='little')
        X_tilt = bytes2int(frame_body[33:35], byteorder='little')
        Y_tilt = bytes2int(frame_body[35:37], byteorder='little')
        Z_tilt = bytes2int(frame_body[37:39], byteorder='little')
        tem = bytes2int(frame_body[39:41], byteorder='little')/10.0
        vol = bytes2int(frame_body[41:43], byteorder='little')/100.0
        sleepinterval = bytes2int(frame_body[43:47], byteorder='little')
        data_crc = bytes2int(frame_body[47:49], byteorder='little')
        expected_data_crc = libscrc.modbus(frame_body[3:47])
        if expected_data_crc == data_crc:
            LOGGER.info('CRC Check Passed！')
            ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            #ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            data = f'{ts},{X_freq},{Y_freq},{Z_freq},{X_acc_max:.2f},{Y_acc_max:.2f},{Z_acc_max:.2f},{X_vel_rms:.2f},{Y_vel_rms:.2f},{Z_vel_rms:.2f},{X_disp_mm},{Y_disp_mm},{Z_disp_mm},{X_tilt},{Y_tilt},{Z_tilt},{tem:.1f},{vol:.2f},{sleepinterval}\n'
            datas = datas + data
            count = count + 1
            if count > 5:
                save_to_csv(datas,col_names,'eigenvalue_' + str(datetime.date.today())+'_ID'+str(device_ID))
                count = 0
                datas = ''
                LOGGER.info('Saved to file successfully！')
        else:
            LOGGER.error('crc mismatch(%d, %d)!' % (expected_data_crc, data_crc))
    except Exception as e:   
        LOGGER.exception(e)
        
def handle_5A03(frame_type, frame_body, tm):
    global count, datas
    LOGGER.info('Handling 5A03...')
    try:
        assert frame_type.find(b'\x5A\x03') == 0
        device_Model = frame_body[3]
        device_ID = bytes2int(frame_body[4:7], byteorder='big')
        X_acc_max = bytes2int(frame_body[9:11], byteorder='little')/100.0
        Y_acc_max = bytes2int(frame_body[11:13], byteorder='little')/100.0
        Z_acc_max = bytes2int(frame_body[13:15], byteorder='little')/100.0
        X_vel_rms = bytes2int(frame_body[15:17], byteorder='little')/100.0
        Y_vel_rms = bytes2int(frame_body[17:19], byteorder='little')/100.0
        Z_vel_rms = bytes2int(frame_body[19:21], byteorder='little')/100.0
        X_disp_mm = bytes2int(frame_body[21:23], byteorder='little')
        Y_disp_mm = bytes2int(frame_body[23:25], byteorder='little')
        Z_disp_mm = bytes2int(frame_body[25:27], byteorder='little')
        tem = bytes2int(frame_body[27:29], byteorder='little')/10.0
        vol = bytes2int(frame_body[29:31], byteorder='little')/100.0
        sleepinterval = bytes2int(frame_body[31:35], byteorder='little')
        data_crc = bytes2int(frame_body[35:37], byteorder='little')
        expected_data_crc = libscrc.modbus(frame_body[3:35])
        if expected_data_crc == data_crc:
            LOGGER.info('CRC Check Passed！')
            ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            #ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            data = f'{ts},{X_acc_max:.2f},{Y_acc_max:.2f},{Z_acc_max:.2f},{X_vel_rms:.2f},{Y_vel_rms:.2f},{Z_vel_rms:.2f},{X_disp_mm},{Y_disp_mm},{Z_disp_mm},{tem:.1f},{vol:.2f},{sleepinterval}\n'
            datas = datas + data
            count = count + 1
            if count > 5:
                save_to_csv(datas,col_names_5a03_,'eigenvalue_' + str(datetime.date.today())+'_ID'+str(device_ID)+'_5A03')
                count = 0
                datas = ''
                LOGGER.info('Saved to file successfully！')
            
            tm_sender = get_datasend_task_manager()
            date_sender = get_data_sender()
            
            tm_sensor_config = get_sensor_config_task_manager()
            t0 = tm_sensor_config.get_next_task()
            while t0:
                tm_sender.add_task(TaskPriority.HIGH, TaskType.DATA_SEND, t0.task_data)
                t0 = tm_sensor_config.get_next_task()
                
            tm_wavedata_trigger = get_wavedata_trigger_task_manager()
            t = tm_wavedata_trigger.get_next_task()
            if t:
                #time.sleep(1)
                tm_sender.add_task(TaskPriority.HIGH, TaskType.DATA_SEND, t.task_data)
                return
            tm_sender.add_task(TaskPriority.NORMAL, TaskType.DATA_SEND, date_sender.ACK_5A03(device_Model, device_ID))
        else:
            LOGGER.error('crc mismatch(%d, %d)!' % (expected_data_crc, data_crc))
    except Exception as e:   
        LOGGER.exception(e)
        
def handle_0110(frame_type, frame_body, tm):
    try:
        assert frame_type.find(b'\x01\x10') == 0
        
        LOGGER.debug('Got ACK for the CMD')
        
        data_crc = bytes2int(frame_body[-5:-3], byteorder='little')
        expected_data_crc = libscrc.modbus(frame_body[3:-5])
        if data_crc == expected_data_crc:
            device_ID = bytes2int(frame_body[4:7], byteorder='big')
            part1 = frame_body[3:7]
            part2 = frame_body[9:-5]
            new_frame_part = part1 + b'\x01\x20' + part2
            data_crc = struct.pack('<H',libscrc.modbus(new_frame_part))
            new_frame = FRAME_DATA_HEAD + new_frame_part + data_crc + FRAME_DATA_END
            
            frame_size = bytes2int(frame_body[9:11], byteorder='big')
            freq = frame_body[11]
            wave_lenth = frame_body[12]
            
            wavedatas_f_name = 'wavedata_' + str(round(time.time()))+'_ID'+str(device_ID)+'_'+str(frame_size)+'_'+str(freq)+'_'+str(wave_lenth)
            save_to_csv('',col_names_0102, wavedatas_f_name) # multiple receiving
            tm_sender = get_datasend_task_manager()
            LOGGER.debug(new_frame)
            tm_sender.add_task(TaskPriority.HIGH, TaskType.DATA_SEND, new_frame)
    except Exception as e:   
        LOGGER.exception(e)

def handle_0102(frame_type, frame_body, tm):# 多个传感器同时接收，考虑启多个线程
    try:
        assert frame_type.find(b'\x01\x02') == 0
        data_crc = bytes2int(frame_body[-5:-3], byteorder='little')
        expected_data_crc = libscrc.modbus(frame_body[3:-5])
        if data_crc == expected_data_crc:
            device_ID = bytes2int(frame_body[4:7], byteorder='big')
            part1 = frame_body[3:7]
            part2 = frame_body[9:13]
            data_part = frame_body[13:-5]
            
            new_frame_part = part1 + b'\x01\x20' + part2
            data_crc = struct.pack('<H',libscrc.modbus(new_frame_part))
            new_frame = FRAME_DATA_HEAD + new_frame_part + data_crc + FRAME_DATA_END
            
            frame_no = bytes2int(frame_body[9:11], byteorder='big')
            single_frame_size = bytes2int(frame_body[11:13], byteorder='big')
            wavedata = '%d,%d,%s\n'%(frame_no, single_frame_size, data_part.hex())
            dir = cfg.get_file_store_rawwave_directory()
            fn = search_wavedata_file(dir, device_ID)
            fn_dir = os.path.join(dir, fn)
            save_to_csv(wavedata,col_names_0102, fn.split('.')[0])
            
            tm_sender = get_datasend_task_manager()
            tm_sender.add_task(TaskPriority.HIGH, TaskType.DATA_SEND, new_frame)
            
            if frame_no >= (int(fn.split('_')[3])):
                save_to_onefile(fn_dir)
    except Exception as e:   
        LOGGER.exception(e)

def handle_sleepintervalconfig_fb(frame_type, frame_body, tm):
    assert frame_type.find(b'\x81\x10') == 0
    device_ID = bytes2int(frame_body[4:7], byteorder='big')
    LOGGER.info('Device:%d sleepinterval setup successfully!'%device_ID)

def handle_sensorconfig_fb(frame_type, frame_body, tm):
    assert frame_type.find(b'\x81\x10') == 0
    device_ID = bytes2int(frame_body[4:7], byteorder='big')
    LOGGER.info('Device:%d sensor setup successfully!'%device_ID)

def handle_unknown_frame(frame_type, frame_body): 
    LOGGER.info('Unhandled frame, frame_type(%s), frame_body(%s)' % (frame_type.hex(), frame_body.hex()))


frame_handler_table = {
                        b'\x5C\x03': handle_5C03,
                        b'\x5A\x03': handle_5A03,
                        b'\x01\x10': handle_0110,
                        b'\x01\x02': handle_0102,
                        b'\x81\x10': handle_sleepintervalconfig_fb,
                        b'\x82\x10': handle_sensorconfig_fb,
                       }


def handle_frame(frame, tm):
    frame_type = frame[0]
    frame_body = frame[1]
    try:
        LOGGER.info('Handling frame_type(%s), frame_body(%s)' % (frame_type, frame_body))
    except:
        LOGGER.info('Handling frame_type(%s), frame_body(%s)' % (frame_type, frame_body.hex().encode().upper()))
    if frame_type in frame_handler_table:
        frame_handler_table[frame_type](frame_type, frame_body, tm)  
    else:
        handle_unknown_frame(frame_type, frame_body)  
        
        
def frame_handler_runner(tm):
    while True:
        t = tm.get_next_task()
        if t is None:
            time.sleep(0.5)
            continue
        else:
            if t.task_type == TaskType.FRAME_HANDLING:
                handle_frame(t.task_data, tm)
            