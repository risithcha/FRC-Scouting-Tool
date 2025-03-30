import threading
import time
import datetime
from flask import current_app, copy_current_request_context

class BackgroundTaskManager:
    def __init__(self):
        self.tasks = {}
        self._lock = threading.Lock()
        self.app = None
        
    def init_app(self, app):
        self.app = app
        
    def start_task(self, task_name, function, *args, **kwargs):
        # Start a background task with correct context
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
            
            # Get current application for context
            app = self.app or current_app._get_current_object()
            
            # Start the task in a background thread with app context
            thread = threading.Thread(
                target=self._run_task_with_context,
                args=(app, task_name, function, args, kwargs)
            )
            thread.daemon = True
            thread.start()
            
            return {'status': 'started', 'task_id': task_name}
    
    def _run_task_with_context(self, app, task_name, function, args, kwargs):
        # Execute the task with proper Flask application context
        with app.app_context():
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