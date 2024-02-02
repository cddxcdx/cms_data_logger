# coding = utf-8


FRAME_DATA_HEAD = b'\xAA\x55\x7F'
FRAME_DATA_END = b'\x7F\xAA\xED'
SLEEPINTERVAL_CMD = b'\x81\x01'
SAMPLEFREQ_WAVELENGTH_CMD = b'\x82\x01'
ACK_5A03_CMD = b'\x5A\x30'
TRIG_0101_CMD = b'\x01\x01'

g_data_sender = None
def set_data_sender(sender):
    global g_data_sender
    g_data_sender = sender
    

def get_data_sender():
    global g_data_sender
    return g_data_sender
    