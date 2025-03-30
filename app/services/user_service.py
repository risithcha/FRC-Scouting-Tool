import os
import json
import datetime
import hashlib
from werkzeug.security import generate_password_hash, check_password_hash
from flask import current_app
# Use the correct drive_integration import
from drive_integration import upload_to_drive, download_file_from_drive, find_file_by_name
from app.utils.logger import log_activity

class UserManager:
    # User management service
    
    def __init__(self, google_drive_folder_id=None):
        self.google_drive_folder_id = google_drive_folder_id
        self.users_file = os.path.join("data", "users.json")
        self.users = {}  # Initialize empty, will load in init_app
        self.app = None
    
    def init_app(self, app):
        self.app = app
        # Set folder ID from config if not provided
        if not self.google_drive_folder_id and app.config.get("GOOGLE_DRIVE_FOLDER_ID"):
            self.google_drive_folder_id = app.config.get("GOOGLE_DRIVE_FOLDER_ID")
        
        # Force download from Drive on startup
        print("Initializing user manager - forcing download from Google Drive")
        self._force_download_from_drive()
        
        # Now load users (includes the just-downloaded file)
        self.users = self._load_users()
    
    def _force_download_from_drive(self):
        # Force download the users.json file from Google Drive at startup
        if not self.google_drive_folder_id:
            print("No Google Drive folder ID configured. Skipping user download.")
            return False
        
        try:
            # Find users file in Drive
            file_info = find_file_by_name("users.json", self.google_drive_folder_id)
            if not file_info:
                print("No users.json found on Google Drive. Using local file only.")
                return False
            
            # Download users file
            content = download_file_from_drive(file_info['id'])
            if not content:
                print("Failed to download users.json from Google Drive.")
                return False
            
            # Parse and save locally
            try:
                drive_users = json.loads(content)
                self._save_local_users(drive_users)
                print(f"Successfully downloaded users.json from Google Drive with {len(drive_users)} users.")
                return True
            except json.JSONDecodeError:
                print("Failed to parse users.json from Google Drive - invalid JSON.")
                return False
                
        except Exception as e:
            print(f"Error downloading users from Drive: {str(e)}")
            return False
    
    def _load_users(self):
        # Load users from local file
        if os.path.exists(self.users_file):
            try:
                with open(self.users_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print("Error loading users.json - invalid JSON. Creating empty users file.")
                empty_users = {}
                self._save_local_users(empty_users)
                return empty_users
        else:
            print("No users.json file found. Creating empty users file.")
            empty_users = {}
            self._save_local_users(empty_users)
            return empty_users
    
    def _save_users(self):
        # Save users locally and to Google Drive
        # Save users locally
        self._save_local_users(self.users)
        
        # Backup to Google Drive if configured
        if self.google_drive_folder_id:
            print(f"Saving users to Google Drive folder: {self.google_drive_folder_id}")
            self._save_drive_users(self.users)
        else:
            print("No Google Drive folder ID configured. Users not saved to Drive.")
    
    def _save_local_users(self, users_data):
        # Save users to local file
        # Make sure data directory exists
        os.makedirs(os.path.dirname(self.users_file), exist_ok=True)
        with open(self.users_file, 'w') as f:
            json.dump(users_data, f, indent=2)
    
    def _save_drive_users(self, users_data):
        # Save users to Google Drive
        try:
            result = upload_to_drive(users_data, "users.json", self.google_drive_folder_id)
            if result:
                print(f"User data uploaded to Drive with ID: {result}")
                return True
            else:
                print("Failed to upload user data to Drive")
                return False
        except Exception as e:
            print(f"Error saving users to Drive: {str(e)}")
            return False
    
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

# Initialize the user manager singleton
user_manager = UserManager()
