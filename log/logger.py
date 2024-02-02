#coding=utf-8
#Copyright (c) 2020, Blue Aspirations 

from logging import config, getLogger

class Logger:
    def __init__(self, logger, logging_conf="logging.conf"):
        self.logging_conf = logging_conf
        self.logger = logger

    def logging_init(self):
        print("Logger config file is :", self.logging_conf)
        config.fileConfig(self.logging_conf)
        return getLogger(self.logger)