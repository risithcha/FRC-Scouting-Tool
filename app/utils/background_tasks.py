import threading
import time
import os
import json
import datetime
from flask import current_app

class BackgroundTaskManager:
    def __init__(self):
        self.tasks = {}
        self._lock = threading.Lock()
        
    def start_task(self, task_name, function, *args, **kwargs):
        # Start a background task
        with self._lock:
            if task_name in self.tasks and self.tasks[task_name]['status'] == 'running':
                return {'status': 'already_running', 'task_id': task_name}
            
            task_info = {
                'status': 'running',
                'start_time': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'result': None,
                'error': None
            }
            
            self.tasks[task_name] = task_info
            
            thread = threading.Thread(
                target=self._run_task,
                args=(task_name, function, args, kwargs)
            )
            thread.daemon = True
            thread.start()
            
            return {'status': 'started', 'task_id': task_name}
    
    def _run_task(self, task_name, function, args, kwargs):
        # Execute the task and store its result
        try:
            result = function(*args, **kwargs)
            with self._lock:
                self.tasks[task_name]['status'] = 'completed'
                self.tasks[task_name]['result'] = result
                self.tasks[task_name]['end_time'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        except Exception as e:
            with self._lock:
                self.tasks[task_name]['status'] = 'failed'
                self.tasks[task_name]['error'] = str(e)
                self.tasks[task_name]['end_time'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def get_task_status(self, task_name):
        # Get the status of a task
        with self._lock:
            if task_name not in self.tasks:
                return {'status': 'not_found'}
            return self.tasks[task_name]
    
    def get_all_tasks(self):
        # Get all tasks and their statuses
        with self._lock:
            return self.tasks.copy()

task_manager = BackgroundTaskManager()