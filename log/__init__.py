#coding=utf-8
#Copyright (c) 2020, Blue Aspirations 

from log.logger import Logger

def get_logger(name, config_file = "logging.conf"):
    return Logger(name, config_file).logging_init()
    
    
LOGGER = get_logger('cms_data_logger') 
