import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # The secret sauce
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY', 'dev_key')
    
    # TBA API settings
    TBA_API_KEY = os.environ.get('TBA_API_KEY')
    
    # Admin credentials - explicit loading
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')
    
    # File paths
    REPORTS_DIR = os.path.join("data", "reports")
    LOGS_DIR = os.path.join("data", "logs")
    
    # Google Drive integration
    GOOGLE_CREDENTIALS_JSON = os.environ.get('GOOGLE_CREDENTIALS_JSON')
    GOOGLE_DRIVE_FOLDER_ID = os.environ.get('GOOGLE_DRIVE_FOLDER_ID')