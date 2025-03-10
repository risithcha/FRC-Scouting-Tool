import os
import requests
import json
import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
TBA_API_KEY = os.getenv("TBA_API_KEY")
DATA_DIR = "data"
REPORTS_DIR = os.path.join(DATA_DIR, "reports")

# Makes sure that the directory exist
os.makedirs(REPORTS_DIR, exist_ok=True)

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "setup-a-key")

# TBA API Functions
def get_tba_data(endpoint):
    # Gets data from The Blue Alliance API.
    url = f"https://www.thebluealliance.com/api/v3/{endpoint}"
    headers = {"X-TBA-Auth-Key": TBA_API_KEY}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": f"API request failed with status {response.status_code}"}

def get_team_info(team_number):
    # Gets team information from TBA.
    return get_tba_data(f"team/frc{team_number}")

def get_team_events(team_number):
    # Gets team events from TBA.
    year = datetime.datetime.now().year
    return get_tba_data(f"team/frc{team_number}/events/{year}")

# Not implemented yet so placeholder text is used
def generate_ai_insights(team_data):
    return "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam euismod, nisi vel consectetur interdum, nisl nisi aliquam nisi, eget consectetur nisl nisi vel nisi. Nullam euismod, nisi vel consectetur interdum, nisl nisi aliquam nisi, eget consectetur nisl nisi vel nisi."

# Stores reports as JSON files
def save_report(report_data):
    # Save a scouting report to JSON file.
    team_number = report_data.get("team_number")
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{team_number}_{timestamp}.json"
    filepath = os.path.join(REPORTS_DIR, filename)
    
    with open(filepath, "w") as f:
        json.dump(report_data, f, indent=2)
    
    return filename

def get_all_reports():
    # Gets all scouting reports.
    reports = []
    for filename in os.listdir(REPORTS_DIR):
        if filename.endswith(".json"):
            filepath = os.path.join(REPORTS_DIR, filename)
            with open(filepath, "r") as f:
                report = json.load(f)
                report["filename"] = filename # Add's the filename to the report to retrieve later
                reports.append(report)
    return reports

def get_report(filename):
    # Gets a specific scouting report.
    filepath = os.path.join(REPORTS_DIR, filename)
    try:
        with open(filepath, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return None

# Flask stuff
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/scout")
def scout():
    team_number = request.args.get('team_number')
    if team_number:
        return redirect(url_for('scout_team', team_number=team_number))
    return render_template("scout_team.html")

@app.route("/scout/<team_number>")
def scout_team(team_number):
    team_info = get_team_info(team_number)
    if "error" in team_info:
        flash(f"Error: {team_info['error']}")
        return redirect(url_for("scout"))
    
    team_events = get_team_events(team_number)
    
    return render_template("scout_form.html", team=team_info, events=team_events)

@app.route("/submit_report", methods=["POST"])
def submit_report():
    report_data = {
        "team_number": request.form.get("team_number"),
        "team_name": request.form.get("team_name"),
        "event": request.form.get("event"),
        "scout_name": request.form.get("scout_name"),
        "auto_scoring": request.form.get("auto_scoring"),
        "teleop_scoring": request.form.get("teleop_scoring"),
        "endgame": request.form.get("endgame"),
        "notes": request.form.get("notes"),
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Not implemented yet so it's just a placeholder
    report_data["ai_insights"] = generate_ai_insights(report_data)
    
    # Save the filename of the report
    filename = save_report(report_data)
    
    flash("Report submitted successfully!")
    return redirect(url_for("view_report", filename=filename))

@app.route("/reports")
def reports():
    all_reports = get_all_reports()
    return render_template("reports.html", reports=all_reports)

@app.route("/report/<filename>")
def view_report(filename):
    report = get_report(filename)
    if not report:
        flash("Report not found")
        return redirect(url_for("reports"))
    
    return render_template("report.html", report=report)

if __name__ == "__main__":
    app.run(debug=True)