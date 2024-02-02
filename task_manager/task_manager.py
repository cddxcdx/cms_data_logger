# coding = utf-8
import time
import queue
from log import LOGGER
from task_manager import TaskPriority, TaskType


class Task(object):
    def __init__(self, task_type, task_data):
        self.task_type = task_type
        self.task_data = task_data

 
class TaskManager(object):
    def __init__(self, queue_size=50000):
        self.queue_size = queue_size
        self.q_normal = queue.Queue(queue_size)
        self.q_high = queue.Queue(queue_size)

    def add_task(self, priority, task_type, task_data):
        try:
            LOGGER.info('Adding task(%s)' % bytes.fromhex(task_data).decode())
        except:
            LOGGER.info('Adding task(%s)' % task_data)
        if priority >= TaskPriority.HIGH:
            self.q_high.put(Task(task_type, task_data))
        else:
            self.q_normal.put(Task(task_type, task_data))
            
    def get_next_task(self):
        if not self.q_high.empty():
            return self.q_high.get()
        elif not self.q_normal.empty():
            return self.q_normal.get()
            
        return None
            
    def __clear_queue(self, q):
        if q.empty():
            return
        i=0            
        while q.get():
            if q.empty():
                return
            i+=1
            if(i>=self.queue_size):
                break
            time.sleep(0.05)

    def clear_normal_priority_tasks(self):
        self.__clear_queue(self.q_normal)
    
    def clear_high_priority_tasks(self):
        self.__clear_queue(self.q_high)

    def clear_tasks(self):
        self.clear_normal_priority_tasks()
        self.clear_high_priority_tasks()
