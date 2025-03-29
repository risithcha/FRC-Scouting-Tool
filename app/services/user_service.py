from flask import Flask
from werkzeug.security import generate_password_hash, check_password_hash
import json
import os
from app.utils.logger import log_activity

class UserManager:
    # User management service
    
    def __init__(self, google_drive_folder_id=None):
        self.google_drive_folder_id = google_drive_folder_id
        self.users_file = os.path.join("data", "users.json")
        self.users = self._load_users()
    
    def init_app(self, app):
        self.app = app
    
    def _load_users(self):
        # Load users from file
        if os.path.exists(self.users_file):
            try:
                with open(self.users_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return {}
        return {}
    
    def _save_users(self):
        # Save users to file
        with open(self.users_file, 'w') as f:
            json.dump(self.users, f, indent=2)
    
    def create_user(self, username, password):
        # Create a new user
        if username in self.users:
            return False
        
        self.users[username] = {
            "password_hash": generate_password_hash(password),
            "is_admin": False,
            "created_at": self._get_timestamp(),
            "settings": {
                "default_event": None
            }
        }
        self._save_users()
        return True
    
    def authenticate_user(self, username, password):
        # Authenticate a user
        if username not in self.users:
            return False
        
        return check_password_hash(self.users[username]["password_hash"], password)
    
    def is_admin(self, username):
        # Check if user is an admin
        if username not in self.users:
            return False
        
        return self.users[username].get("is_admin", False)
    
    def get_user_settings(self, username):
        # Get user settings
        if not username or username not in self.users:
            return {}
        
        return self.users[username].get("settings", {})
    
    def update_user_settings(self, username, settings):
        # Update user settings
        if not username or username not in self.users:
            return False
        
        self.users[username]["settings"] = settings
        self._save_users()
        return True
    
    def get_all_users(self):
        # Get all users
        users_list = []
        for username, data in self.users.items():
            user_data = data.copy()
            user_data["username"] = username
            users_list.append(user_data)
        return users_list
    
    def _get_timestamp(self):
        # Get current timestamp
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def set_admin_status(self, username, is_admin):
        # Set admin status for a user
        if username not in self.users:
            return False
        
        self.users[username]["is_admin"] = is_admin
        self._save_users()
        return True

user_manager = UserManager()