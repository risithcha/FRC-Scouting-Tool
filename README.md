# FRC Scouting Tool - Developers

A comprehensive scouting application for FIRST Robotics Competition teams to collect, analyze, and share robot performance data during competitions.

## Features

- **Team Scouting**: Record detailed observations about robot performance
- **Performance Analytics**: Generate statistics about team capabilities
- **Match Planning**: Organize which teams need scouting and when
- **Admin Controls**: Manage users, events, and settings
- **Google Drive Integration**: Automatically sync data to drive

## Installation

### Prerequisites

- Python
- Git
- A Google account with Google Drive access
- The Blue Alliance API key

### Setup Instructions

1. Clone the repository:
   ```
   git clone https://github.com/risithcha/FRC-Scouting-Tool.git
   cd FRC-Scouting-Tool
   ```

2. Create and configure your environment file:
   ```
   cp .env.youchange .env
   ```
   Edit .env and add your:
   - TBA API key (get from [The Blue Alliance](https://www.thebluealliance.com/account))
   - Flask secret key (any secure random string)
   - Google Drive credentials (JSON format)
   - Google Drive folder ID

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Run the application:
   ```
   python run.py
   ```

5. Access the application in your browser at `http://localhost:5000`

## Configuration

### Google Drive Setup

1. Create a Google Cloud project
2. Enable the Google Drive API
3. Create a service account with Drive API access
4. Download the service account credentials JSON
5. Create a folder in Google Drive and share it with the service account email
6. Add the service account credentials and folder ID to your .env file

### Admin Account

The default admin account is created automatically with the credentials in your .env file:
```
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your_secure_password
```

## Usage

### User Management

- **Register**: Create an account to start scouting
- **Login**: Access your saved scouting data
- **Admin Login**: Manage all system settings via `/admin/login`

### Scouting Flow

1. Select a team to scout from the team list
2. Fill out the scouting form during a match
3. Submit the report to store data
4. View compiled stats for analysis

## Acknowledgements

- [The Blue Alliance](https://www.thebluealliance.com/) for match and team data
- [Font Awesome](https://fontawesome.com/) for the icons used throughout the app