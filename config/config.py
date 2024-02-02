#coding=utf-8

import json


class Config:
    def __init__(self, cfg_file = "cfg.json"):
        self.__cfg_file = cfg_file
        with open(cfg_file) as f:
            self.decoded_cfg = json.loads(f.read())
        
    def save(self):
        with open(self.__cfg_file, 'w', encoding='utf-8') as f:
            json.dump(self.decoded_cfg, f, indent=4)

    def get_version(self):
        return self.decoded_cfg['version']
        
    def get_service_name(self):
        return self.decoded_cfg['service_name']
        
    def get_serial_cfg(self):
        return self.decoded_cfg['serial_cfg']
        
    def get_task_queue_size(self):
        return self.decoded_cfg['task_manager']['queue_size']
        
    def get_file_store_eigenvalue_directory(self):
        return self.decoded_cfg['file_store']['eigenvalue']['file_store_directory']
        
    def get_file_store_rawwave_directory(self):
        return self.decoded_cfg['file_store']['rawwave']['file_store_directory']
        
    def get_file_store_rawwave_upload_rate(self):
        return self.decoded_cfg['file_store']['rawwave']['rawwave_upload_rate']
    
    def get_file_store_rawwave_upload_interval(self):
        return self.decoded_cfg['file_store']['rawwave']['rawwave_upload_interval']
    
    def get_devices(self):
        return self.decoded_cfg['devices']

if __name__ == '__main__':
    cfg = Config()
    print(cfg.get_serial_cfg())


