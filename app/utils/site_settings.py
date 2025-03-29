import json
import datetime
from flask import current_app
from app.services.drive_service import find_file_by_name, download_file_from_drive, upload_to_drive

def get_site_settings():
    # Retrieves site-wide settings from Google Drive or uses default if none exist
    drive_folder_id = current_app.config["GOOGLE_DRIVE_FOLDER_ID"]
    file_info = find_file_by_name("site_settings.json", drive_folder_id)
    
    if file_info:
        # Download existing settings
        content = download_file_from_drive(file_info['id'])
        if content:
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                # Create new if its corrupt or something
                pass
    
    # Default settings
    default_settings = {
        "active_events": ["2025wabon", "2025wasno"],  # Default events
        "default_event": "2025wabon",                 # Global default event
        "events_last_updated": datetime.datetime.now().isoformat(),
        "system_notice": ""
    }
    
    # Save default settings to drive
    upload_to_drive(default_settings, "site_settings.json", drive_folder_id)
    return default_settings

def save_site_settings(settings):
    # Saves site-wide settings to Google Drive
    drive_folder_id = current_app.config["GOOGLE_DRIVE_FOLDER_ID"]
    settings["events_last_updated"] = datetime.datetime.now().isoformat()
    result = upload_to_drive(settings, "site_settings.json", drive_folder_id)
    return result