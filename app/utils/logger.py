import os
import json
import datetime
from flask import current_app

def log_activity(action, details):
    # Log an activity to the log file
    log_entry = {
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "action": action,
        "details": details
    }
    
    logs_dir = current_app.config["LOGS_DIR"]
    logs_file = os.path.join(logs_dir, "activity_log.json")
    
    # Read existing logs
    existing_logs = []
    if os.path.exists(logs_file):
        try:
            with open(logs_file, 'r') as f:
                existing_logs = json.load(f)
        except json.JSONDecodeError:
            existing_logs = []
    
    # Add new log and save
    existing_logs.insert(0, log_entry)
    
    # Keep only the last 100 entries
    if len(existing_logs) > 100:
        existing_logs = existing_logs[:100]
    
    with open(logs_file, 'w') as f:
        json.dump(existing_logs, f, indent=2)
    
    return log_entry

def get_recent_logs(limit=20):
    # Get the most recent log entries
    logs_dir = current_app.config["LOGS_DIR"]
    logs_file = os.path.join(logs_dir, "activity_log.json")
    
    if not os.path.exists(logs_file):
        return []
    
    try:
        with open(logs_file, 'r') as f:
            logs = json.load(f)
            return logs[:limit]
    except:
        return []