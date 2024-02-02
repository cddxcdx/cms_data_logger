from enum import IntEnum

class TaskPriority(IntEnum):
    NORMAL = 1
    HIGH = 2

class TaskType(IntEnum):
    FRAME_HANDLING = 0
    DATA_SEND = 1

g_sensor_config_task_manager = None
def set_sensor_config_task_manager(task_manager):
    global g_sensor_config_task_manager
    g_sensor_config_task_manager = task_manager

def get_sensor_config_task_manager():
    global g_sensor_config_task_manager
    return g_sensor_config_task_manager

g_wavedata_trigger_task_manager = None
def set_wavedata_trigger_task_manager(task_manager):
    global g_wavedata_trigger_task_manager
    g_wavedata_trigger_task_manager = task_manager

def get_wavedata_trigger_task_manager():
    global g_wavedata_trigger_task_manager
    return g_wavedata_trigger_task_manager

g_datasend_task_manager = None
def set_datasend_task_manager(task_manager):
    global g_datasend_task_manager
    g_datasend_task_manager = task_manager
    

def get_datasend_task_manager():
    global g_datasend_task_manager
    return g_datasend_task_manager
    
    
g_datarecv_task_manager = None
def set_datarecv_task_manager(task_manager):
    global g_datarecv_task_manager
    g_datarecv_task_manager = task_manager
    

def get_datarecv_task_manager():
    global g_datarecv_task_manager
    return g_datarecv_task_manager