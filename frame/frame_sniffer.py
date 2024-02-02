# coding=utf-8

import time
from log import LOGGER

FRAME_DATA_END = b'\x7F\xAA\xED'
FRAME_MIN_LEN = 14
FRAME_HEAD_LEN = 9


def get_frame_type(frame_body):
    return frame_body[FRAME_HEAD_LEN-2:min(FRAME_HEAD_LEN, len(frame_body))]


def find_frame_head(data):
    valid_heads = [b'\xAA\x55\x7F']
    pos_heads = []
    first_head_text = None
    for head in valid_heads:
        pos_head = data.find(head)
        if pos_head>=0:
            LOGGER.debug("Found new head(%s) at pos(%d)" %(head, pos_head))
            pos_heads.append(pos_head)
            if first_head_text is None:
                first_head_text = head

    if len(pos_heads):
        return first_head_text, min(pos_heads)
    else:
        return None, -1

 
class FrameSniffer:
    def __init__(self, tail=FRAME_DATA_END):
        self.__tail = tail
        self.kept_data = None

    def sniff_frame(self, data):
        is_tail_at_next_head = False
        FRAME_TAIL_LEN = len(self.__tail)
        if len(data) < FRAME_MIN_LEN:
            LOGGER.debug("Data is too short, keep data")
            return None, None, data

        first_head_text, pos_head = find_frame_head(data)
        if pos_head < 0:
            LOGGER.debug("No frame head found, drop data(%s)" % data)
            return None, None, bytes()

        first_head_text, next_head = find_frame_head(data[(pos_head+1):])
        if next_head < 0:
            pos_tail = data.find(self.__tail)
            if pos_tail < 0:
                LOGGER.debug("Keeping data as no head nor tail is found")
                LOGGER.debug(data.hex())
                data = self.record_kept_data(data)
                return None, None, data                
        else:
            next_head = next_head + 1
            if (next_head - pos_head) >= FRAME_MIN_LEN:
                pos_tail = next_head    
                is_tail_at_next_head = True
            else:
                pos_tail = data.find(self.__tail)
                if pos_tail < 0:
                    LOGGER.debug("Keeping data as no tail is found")
                    return None, None, data                        


        if pos_tail < pos_head:
            LOGGER.debug("Tail head mismatch, drop to head, pos_head(%d), pos_tail(%d)" % (pos_head, pos_tail))
            return None, None, data[pos_head:]

        if (pos_tail - pos_head) < (FRAME_MIN_LEN - FRAME_TAIL_LEN):
            LOGGER.debug("Heand and Tail are too near, dropping, pos_head(%d), pos_tail(%d)" % (pos_head, pos_tail))
            return None, None, bytes()
        if not is_tail_at_next_head:
            pos_tail = pos_tail+FRAME_TAIL_LEN
        frame_body = data[pos_head:pos_tail]
        LOGGER.debug("Frame body: %s"%frame_body.hex())

        if pos_tail < len(data):
            left_data = data[pos_tail:]
        else:
            left_data = bytes()
        LOGGER.debug("Left Data: %s"%left_data.hex())
        return get_frame_type(frame_body), frame_body, left_data

    def record_kept_data(self, data):
        if self.kept_data == None:
            self.kept_data = data
            return data
        elif self.kept_data == data:
            self.kept_data = None
            LOGGER.debug('record_kept_data same data')
            return data + self.__tail
        else:
            self.kept_data = None
            return data
            
        
            