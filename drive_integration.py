import os
import json
import io
import uuid
import time
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from dotenv import load_dotenv

load_dotenv()

def get_drive_service():
    try:
        creds_json = os.getenv("GOOGLE_CREDENTIALS_JSON")
        if not creds_json:
            print("Google Drive credentials not found in environment.")
            return None
            
        credentials_dict = json.loads(creds_json)
        credentials = service_account.Credentials.from_service_account_info(credentials_dict, scopes=['https://www.googleapis.com/auth/drive.file'])
        
        drive_service = build('drive', 'v3', credentials=credentials)
        return drive_service
    
    except Exception as e:
        print(f"Error creating Drive service: {str(e)}")
        return None

def upload_to_drive(file_content, file_name, folder_id=None):
    try:
        service = get_drive_service()
        if not service:
            print("Failed to get Drive service")
            return None
            
        file_metadata = {'name': file_name}
        if folder_id:
            file_metadata['parents'] = [folder_id]
        
        # Create a unique temporary filename to avoid conflicts
        unique_id = str(uuid.uuid4())[:8]
        temp_path = f"temp_{unique_id}_{file_name}"
        
        # Create a temporary file to upload
        try:
            with open(temp_path, 'w') as f:
                if isinstance(file_content, dict) or isinstance(file_content, list):
                    json.dump(file_content, f, indent=2)
                else:
                    f.write(str(file_content))
        except Exception as e:
            print(f"Error writing temp file: {str(e)}")
            return None
            
        try:
            # Upload to Drive
            media = MediaFileUpload(temp_path, mimetype='application/json')
            
            # Check if file already exists
            existing_file = find_file_by_name(file_name, folder_id)
            
            if existing_file:
                # Update existing file
                file = service.files().update(
                    fileId=existing_file['id'],
                    media_body=media).execute()
                file_id = existing_file['id']
            else:
                # Create new file
                file = service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id').execute()
                file_id = file.get('id')
            
            print(f"File uploaded to Drive with ID: {file_id}")
            return file_id
            
        finally:
            # Always try to clean up the temp file with retry mechanism
            for attempt in range(5):  # Try up to 5 times
                try:
                    if os.path.exists(temp_path):
                        # Close any potential file handles
                        media._fd.close()
                        os.close(os.open(temp_path, os.O_RDONLY))
                        # Remove the file
                        os.remove(temp_path)
                    break  # If successful, exit the retry loop
                except Exception as e:
                    print(f"Error removing temp file (attempt {attempt+1}): {str(e)}")
                    time.sleep(0.5)  # Wait half a second before trying again
            
            # If we still couldn't delete it after all attempts, just log it
            if os.path.exists(temp_path):
                print(f"Warning: Could not remove temporary file {temp_path}")
    
    except Exception as e:
        print(f"Error uploading to Drive: {str(e)}")
        return None

def get_all_files_from_drive(folder_id=None, page_size=100, page_token=None):
    # Get files from a Google Drive folder with pagination
    try:
        service = get_drive_service()
        if not service:
            return {"files": [], "nextPageToken": None}
        
        query = f"'{folder_id}' in parents and mimeType='application/json'" if folder_id else "mimeType='application/json'"
        
        # Use pagination to get files in smaller batches
        results = service.files().list(
            q=query,
            spaces='drive',
            fields='nextPageToken, files(id, name)',
            pageSize=page_size,
            pageToken=page_token
        ).execute()
        
        return {
            "files": results.get('files', []),
            "nextPageToken": results.get('nextPageToken')
        }
    
    except Exception as e:
        print(f"Error retrieving files from Drive: {str(e)}")
        return {"files": [], "nextPageToken": None}

def download_file_from_drive(file_id):
    # Download a file from Google Drive by ID
    try:
        service = get_drive_service()
        if not service:
            return None
            
        request = service.files().get_media(fileId=file_id)
        file_content = io.BytesIO()
        downloader = MediaIoBaseDownload(file_content, request)
        
        done = False
        while not done:
            _, done = downloader.next_chunk()
            
        return file_content.getvalue().decode('utf-8')
    
    except Exception as e:
        print(f"Error downloading file from Drive: {str(e)}")
        return None

def find_file_by_name(file_name, folder_id=None):
    # Find a file by name in Google Drive
    try:
        service = get_drive_service()
        if not service:
            return None
            
        query = f"name='{file_name}'"
        if folder_id:
            query += f" and '{folder_id}' in parents"
            
        results = service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name)'
        ).execute()
        
        files = results.get('files', [])
        if files:
            return files[0]
        return None
    
    except Exception as e:
        print(f"Error finding file in Drive: {str(e)}")
        return None