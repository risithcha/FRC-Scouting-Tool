import os
import json
import time
import math
import datetime
from flask import current_app
from app.models.report import Report
from drive_integration import upload_to_drive, download_file_from_drive, find_file_by_name, get_all_files_from_drive

class ReportService:
    # Service for managing scouting reports
    
    @staticmethod
    def save_report(report_data):
        # Save a scouting report locally and back up to Google Drive
        report = Report.from_dict(report_data)
        report.calculate_scores()
        
        # Generate filename
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{report.team_number}_{timestamp}.json"
        report.filename = filename
        
        # Get report data as dictionary
        report_dict = report.to_dict()
        
        # Save to local storage first
        reports_dir = current_app.config["REPORTS_DIR"]
        local_path = os.path.join(reports_dir, filename)
        
        with open(local_path, 'w') as f:
            json.dump(report_dict, f, indent=2)
        
        # Backup to Google Drive
        drive_folder_id = current_app.config["GOOGLE_DRIVE_FOLDER_ID"]
        file_id = upload_to_drive(report_dict, filename, drive_folder_id)
        
        if not file_id:
            print("Failed to upload report to Google Drive, but saved locally")
        
        return filename
        
    @staticmethod
    def get_all_reports():
        # Gets all scouting reports from local storage
        reports = []
        reports_dir = current_app.config["REPORTS_DIR"]
        
        # Get all JSON files from the reports directory
        for filename in os.listdir(reports_dir):
            if filename.endswith('.json'):
                file_path = os.path.join(reports_dir, filename)
                try:
                    with open(file_path, 'r') as f:
                        report_data = json.load(f)
                        report_data["filename"] = filename  # Add filename to the report
                        
                        # Make sure required fields exist
                        if "team_number" not in report_data:
                            print(f"Warning: File {filename} missing required field 'team_number'")
                            report_data["team_number"] = filename.split('_')[0] if '_' in filename else "unknown"
                        
                        reports.append(report_data)
                except json.JSONDecodeError as e:
                    print(f"Error parsing JSON from file {filename}: {e}")
        
        # Sort reports by timestamp (newest first)
        reports.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        return reports
    
    @staticmethod
    def get_report(filename):
        # Get a specific report by filename
        reports_dir = current_app.config["REPORTS_DIR"]
        file_path = os.path.join(reports_dir, filename)
        
        if not os.path.exists(file_path):
            return None
        
        try:
            with open(file_path, 'r') as f:
                report_data = json.load(f)
                report_data["filename"] = filename
                return report_data
        except:
            return None
    
    @staticmethod
    def get_team_reports(team_number):
        # Get all reports for a specific team
        all_reports = ReportService.get_all_reports()
        team_reports = [r for r in all_reports if r.get("team_number") == str(team_number)]
        return team_reports
    
    @staticmethod
    def sync_reports_from_drive():
        # Sync reports from Google Drive in small batches to prevent timeouts
        reports_dir = current_app.config["REPORTS_DIR"]
        drive_folder_id = current_app.config["GOOGLE_DRIVE_FOLDER_ID"]
        
        # Get list of local files
        local_files = set(os.listdir(reports_dir))
        
        synced_count = 0
        failed_count = 0
        batch_count = 0
        total_drive_files = 0
        
        # Use pagination to get files in smaller batches from Drive
        next_page_token = None
        
        while True:
            batch_count += 1
            print(f"Fetching file list batch #{batch_count} from Google Drive")
            
            # Get a batch of files from Drive
            result = get_all_files_from_drive(drive_folder_id, page_size=100, page_token=next_page_token)
            drive_files_batch = result["files"]
            next_page_token = result["nextPageToken"]
            
            total_drive_files += len(drive_files_batch)
            
            # Filter files that need to be downloaded
            files_to_download = [
                file for file in drive_files_batch 
                if file['name'] not in local_files and file['name'].endswith('.json')
            ]
            
            # Process in smaller download batches of 10
            download_batch_size = 10
            download_batches = math.ceil(len(files_to_download) / download_batch_size)
            
            for i in range(0, len(files_to_download), download_batch_size):
                download_batch = files_to_download[i:i+download_batch_size]
                current_batch = i // download_batch_size + 1
                print(f"Processing download batch {current_batch}/{download_batches} ({len(download_batch)} files)")
                
                for file in download_batch:
                    file_content = download_file_from_drive(file['id'])
                    if file_content:
                        local_path = os.path.join(reports_dir, file['name'])
                        try:
                            with open(local_path, 'w') as f:
                                f.write(file_content)
                            synced_count += 1
                        except Exception as e:
                            failed_count += 1
                            print(f"Error saving {file['name']} locally: {str(e)}")
                
                # Add a pause between download batches
                if i + download_batch_size < len(files_to_download):
                    time.sleep(1.5)  # 1.5 second pause between download batches
            
            # If no more pages, break the loop
            if not next_page_token:
                break
                
            # Pause between fetching file list batches
            time.sleep(2)  # 2 second pause between file listing batches
        
        # Save last sync time
        with open(os.path.join("data", "last_sync.txt"), 'w') as f:
            f.write(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        return {
            "synced": synced_count,
            "failed": failed_count,
            "total_drive": total_drive_files,
            "total_local": len(local_files) + synced_count,
            "batches": batch_count
        }
    
    @staticmethod
    def sync_users_from_drive():
        # Sync users from Google Drive
        drive_folder_id = current_app.config["GOOGLE_DRIVE_FOLDER_ID"]
        
        # Find users file in Drive
        file_info = find_file_by_name("users.json", drive_folder_id)
        
        if not file_info:
            return {"status": "No users file found on Drive"}
        
        # Download users file
        content = download_file_from_drive(file_info['id'])
        if not content:
            return {"status": "Failed to download users file"}
        
        try:
            drive_users = json.loads(content)
            
            # Load current local users
            local_path = os.path.join("data", "users.json")
            local_users = {}
            if os.path.exists(local_path):
                with open(local_path, 'r') as f:
                    local_users = json.load(f)
            
            local_usernames = {user["username"].lower() for user in local_users.get("users", [])}
            new_users_count = 0
            
            for drive_user in drive_users.get("users", []):
                if drive_user["username"].lower() not in local_usernames:
                    local_users.setdefault("users", []).append(drive_user)
                    new_users_count += 1
            
            # Save updated users file
            if new_users_count > 0:
                with open(local_path, 'w') as f:
                    json.dump(local_users, f, indent=2)
            
            return {
                "status": "success",
                "new_users": new_users_count
            }
        
        except Exception as e:
            return {"status": f"Error: {str(e)}"}

report_service = ReportService()