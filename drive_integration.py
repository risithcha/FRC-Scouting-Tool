import os
import json
import io
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
        
        # Create a temporary file to upload, /tmp is being used cause... Render
        try:
            os.makedirs('/tmp', exist_ok=True)
        except:
            # If /tmp doesn't work, just use a local path
            pass
            
        temp_path = os.path.join("/tmp", file_name)
        try:
            with open(temp_path, 'w') as f:
                if isinstance(file_content, dict):
                    json.dump(file_content, f, indent=2)
                else:
                    f.write(file_content)
        except Exception as e:
            print(f"Error writing temp file: {str(e)}")
            # Try other path if /tmp fails
            temp_path = file_name
            with open(temp_path, 'w') as f:
                if isinstance(file_content, dict):
                    json.dump(file_content, f, indent=2)
                else:
                    f.write(file_content)
            
        # Upload to Drive
        media = MediaFileUpload(temp_path, mimetype='application/json')
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()
        
        try:
            os.remove(temp_path)
        except:
            pass
        
        print(f"File uploaded to Drive with ID: {file.get('id')}")
        return file.get('id')
    
    except Exception as e:
        print(f"Error uploading to Drive: {str(e)}")
        return None

def get_all_files_from_drive(folder_id=None):
    # Get all files from a Google Drive folder
    try:
        service = get_drive_service()
        if not service:
            return []
        
        query = f"'{folder_id}' in parents and mimeType='application/json'" if folder_id else "mimeType='application/json'"
        
        results = service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name)'
        ).execute()
        
        return results.get('files', [])
    
    except Exception as e:
        print(f"Error retrieving files from Drive: {str(e)}")
        return []

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