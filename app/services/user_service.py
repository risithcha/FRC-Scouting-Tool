import os
import json
import datetime
import hashlib
from werkzeug.security import generate_password_hash, check_password_hash
from flask import current_app
from app.services.drive_service import upload_to_drive, download_file_from_drive, find_file_by_name
from app.utils.logger import log_activity

class UserManager:
    # User management service
    
    def __init__(self, google_drive_folder_id=None):
        self.google_drive_folder_id = google_drive_folder_id
        self.users_file = os.path.join("data", "users.json")
        self.users = self._load_users()
    
    def init_app(self, app):
        self.app = app
        # Set folder ID from config if not provided
        if not self.google_drive_folder_id and app.config.get("GOOGLE_DRIVE_FOLDER_ID"):
            self.google_drive_folder_id = app.config.get("GOOGLE_DRIVE_FOLDER_ID")
    
    def _load_users(self):
        # First try to load from local file
        local_users = self._load_local_users()
        
        # Then check Google Drive if configured
        if self.google_drive_folder_id:
            drive_users = self._load_drive_users()
            
            # If we have both, merge them (local takes precedence for now)
            if local_users and drive_users:
                # TODO: Implement proper merging with timestamps
                return local_users
            elif drive_users:
                # If we only have drive users, save them locally
                self._save_local_users(drive_users)
                return drive_users
        
        return local_users
    
    def _load_local_users(self):
        # Load users from local file
        if os.path.exists(self.users_file):
            try:
                with open(self.users_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return {}
        return {}
    
    def _load_drive_users(self):
        # Load users from Google Drive
        try:
            file_info = find_file_by_name("users.json", self.google_drive_folder_id)
            if file_info:
                content = download_file_from_drive(file_info['id'])
                if content:
                    return json.loads(content)
            return None
        except Exception as e:
            print(f"Error loading users from Drive: {str(e)}")
            return None
    
    def _save_users(self):
        # Save users locally
        self._save_local_users(self.users)
        
        # Backup to Google Drive if configured
        if self.google_drive_folder_id:
            self._save_drive_users(self.users)
    
    def _save_local_users(self, users_data):
        # Save users to local file
        with open(self.users_file, 'w') as f:
            json.dump(users_data, f, indent=2)
    
    def _save_drive_users(self, users_data):
        # Save users to Google Drive
        try:
            upload_to_drive(users_data, "users.json", self.google_drive_folder_id)
        except Exception as e:
            print(f"Error saving users to Drive: {str(e)}")
    
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