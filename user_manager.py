import os
import json
import hashlib
import uuid
import datetime
from drive_integration import upload_to_drive, download_file_from_drive, find_file_by_name

class UserManager:
    USERS_FILE = "users.json"
    
    def __init__(self, drive_folder_id):
        self.drive_folder_id = drive_folder_id
        self.users_cache = None
        self.last_fetch_time = None
        
    def _hash_password(self, password, salt=None):
        # Hash a password
        if salt is None:
            salt = uuid.uuid4().hex
        hashed = hashlib.sha256((password + salt).encode()).hexdigest()
        return hashed, salt
    
    def _fetch_users(self, force_refresh=False):
        # Get users from Google Drive with caching
        # Check if we should use cache
        if not force_refresh and self.users_cache is not None:
            # Use cache if last fetch was less than 5 minutes ago
            if self.last_fetch_time and (datetime.datetime.now() - self.last_fetch_time).seconds < 300:
                return self.users_cache
        
        # Find users file in Drive
        file_info = find_file_by_name(self.USERS_FILE, self.drive_folder_id)
        
        if not file_info:
            # Create new users file with default admin
            self.users_cache = {
                "users": [
                    {
                        "username": os.getenv("ADMIN_USERNAME", "admin"),
                        "password_hash": hashlib.sha256(os.getenv("ADMIN_PASSWORD", "password").encode()).hexdigest(),
                        "salt": "", 
                        "is_admin": True,
                        "created_at": datetime.datetime.now().isoformat()
                    }
                ]
            }
            # Upload the new users file
            upload_to_drive(self.users_cache, self.USERS_FILE, self.drive_folder_id)
        else:
            # Download and parse the users file
            content = download_file_from_drive(file_info['id'])
            if content:
                try:
                    self.users_cache = json.loads(content)
                except json.JSONDecodeError:
                    # Create new users file if corrupt
                    self.users_cache = {"users": []}
            else:
                self.users_cache = {"users": []}
        
        self.last_fetch_time = datetime.datetime.now()
        return self.users_cache
    
    def _save_users(self):
        # Save users to Google Drive
        if self.users_cache:
            upload_to_drive(self.users_cache, self.USERS_FILE, self.drive_folder_id)
    
    def get_user(self, username):
        # Get user by username
        users_data = self._fetch_users()
        
        for user in users_data.get("users", []):
            if user["username"].lower() == username.lower():
                return user
        
        return None
    
    def authenticate(self, username, password):
        # Authenticate a user
        user = self.get_user(username)
        
        if not user:
            return None
            
        # Check if this is the admin with non-salted password
        if user.get("is_admin") and not user.get("salt"):
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            if password_hash == user["password_hash"]:
                return user
        # Normal salted password check
        elif user.get("salt"):
            hashed, _ = self._hash_password(password, user["salt"])
            if hashed == user["password_hash"]:
                return user
                
        return None
    
    def create_user(self, username, password, is_admin=False):
        # Create a new user
        # Check if user already exists
        if self.get_user(username):
            return False, "Username already exists"
            
        # Hash the password
        password_hash, salt = self._hash_password(password)
        
        # Get users data
        users_data = self._fetch_users()
        
        # Add new user
        new_user = {
            "username": username,
            "password_hash": password_hash,
            "salt": salt,
            "is_admin": is_admin,
            "created_at": datetime.datetime.now().isoformat()
        }
        
        users_data["users"].append(new_user)
        
        # Save to Drive
        self._save_users()
        
        return True, "User created successfully"

    def get_user_settings(self, username):
        # Get settings for a specific user
        user = self.get_user(username)
        if not user:
            return {}
            
        # Return settings or empty dict if none exists
        return user.get("settings", {})
        
    def update_user_settings(self, username, settings):
        # Update settings for a user
        users_data = self._fetch_users()
        
        for user in users_data.get("users", []):
            if user["username"].lower() == username.lower():
                # Create settings dict if it doesn't exist
                if "settings" not in user:
                    user["settings"] = {}
                    
                # Update with new settings
                user["settings"].update(settings)
                
                # Save to Google Drive
                self._save_users()
                return True
                
        return False