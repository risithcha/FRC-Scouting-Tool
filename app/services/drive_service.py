import os
import json
import io
import uuid
import time
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from flask import current_app

def get_drive_service():
    # Get the Google Drive service
    try:
        creds_json = os.getenv("GOOGLE_CREDENTIALS_JSON")
        if not creds_json:
            print("Google Drive credentials not found in environment.")
            return None
            
        credentials_dict = json.loads(creds_json)
        credentials = service_account.Credentials.from_service_account_info(
            credentials_dict, 
            scopes=['https://www.googleapis.com/auth/drive.file']
        )
        
        drive_service = build('drive', 'v3', credentials=credentials)
        return drive_service
    
    except Exception as e:
        print(f"Error creating Drive service: {str(e)}")
        return None

def upload_to_drive(file_content, file_name, folder_id=None):
    # Upload a file to Google Drive
    try:
        drive_service = get_drive_service()
        if not drive_service:
            print("Failed to get Drive service")
            return None
            
        file_metadata = {'name': file_name}
        if folder_id:
            file_metadata['parents'] = [folder_id]
        
        # Create a unique temporary filename to fix that stupid annoying bug
        unique_id = str(uuid.uuid4())[:8]
        temp_path = f"temp_{unique_id}_{file_name}"
        
        # Create a temporary file to upload
        with open(temp_path, 'w') as f:
            if isinstance(file_content, dict) or isinstance(file_content, list):
                json.dump(file_content, f, indent=2)
            else:
                f.write(str(file_content))
        
        # Upload to Drive
        try:
            media = MediaFileUpload(temp_path, 
                                mimetype='application/json',
                                resumable=True)
            
            # Check if file already exists
            existing_file = find_file_by_name(file_name, folder_id)
            
            if existing_file:
                # Update existing file
                file = drive_service.files().update(
                    fileId=existing_file['id'],
                    media_body=media).execute()
                file_id = existing_file['id']
            else:
                # Create new file
                file = drive_service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id').execute()
                file_id = file.get('id')
            
            print(f"File uploaded to Drive with ID: {file_id}")
            return file_id
        finally:
            # Always try to clean up the temp file with retries
            # Close the stupid media file handle if it exists
            if 'media' in locals() and hasattr(media, '_fd') and media._fd:
                try:
                    media._fd.close()
                except:
                    pass
                    
            # Try multiple times to delete the file
            for attempt in range(5):
                try:
                    if os.path.exists(temp_path):
                        os.close(os.open(temp_path, os.O_RDONLY))  # This helps on Windows
                        os.remove(temp_path)
                    break  # Success - exit the retry loop
                except Exception as e:
                    print(f"Attempt {attempt+1} - Error removing temp file: {str(e)}")
                    time.sleep(0.5)  # Wait half a second before trying again
            
            # If we still can't delete it, just log and continue
            if os.path.exists(temp_path):
                print(f"Warning: Could not remove temporary file {temp_path}")
    
    except Exception as e:
        print(f"Error uploading to Drive: {str(e)}")
        return None

def get_all_files_from_drive(folder_id=None):
    # Get all files from a Google Drive folder
    drive_service = get_drive_service()
    if not drive_service:
        return []
    
    try:
        query = ""
        if folder_id:
            query = f"'{folder_id}' in parents"
        
        results = drive_service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name, mimeType, createdTime)').execute()
        
        return results.get('files', [])
    except Exception as e:
        print(f"Error getting files from Drive: {str(e)}")
        return []

def download_file_from_drive(file_id):
    # Download a file from Google Drive
    drive_service = get_drive_service()
    if not drive_service:
        return None
    
    try:
        request = drive_service.files().get_media(fileId=file_id)
        file = io.BytesIO()
        downloader = MediaIoBaseDownload(file, request)
        done = False
        
        while not done:
            status, done = downloader.next_chunk()
            
        return file.getvalue().decode('utf-8')
    except Exception as e:
        print(f"Error downloading file from Drive: {str(e)}")
        return None

def find_file_by_name(file_name, folder_id=None):
    # Find a file by name in Google Drive
    drive_service = get_drive_service()
    if not drive_service:
        return None
    
    try:
        query = f"name = '{file_name}'"
        if folder_id:
            query += f" and '{folder_id}' in parents"
        
        results = drive_service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name)').execute()
        
        files = results.get('files', [])
        
        if not files:
            return None
            
        return files[0]
    except Exception as e:
        print(f"Error finding file in Drive: {str(e)}")
        return None