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

def generate_team_stats(reports):
    stats = {
        "games_played": len(reports),
        "percent_moved": 0,
        "auto": {
            "percent_moved": 0,
            "avg_coral": 0,
            "avg_score": 0,
        },
        "teleop": {
            "avg_coral": 0,
            "avg_score": 0,
            "avg_cycles": 0,
            "percent_successful_cycles": 0,
            "avg_l4": 0,
            "avg_net": 0,
        },
        "endgame": {
            "percent_park": 0,
            "percent_shallow_climb": 0,
            "percent_deep_climb": 0,
            "avg_score": 0,
        }
    }
    
    if not reports:
        return stats
    
    # Calculate overall metrics
    moved_count = 0
    auto_moved_count = 0
    park_count = 0
    shallow_climb_count = 0
    deep_climb_count = 0
    
    # Accumulate values for averaging
    auto_coral_total = 0
    auto_score_total = 0
    teleop_coral_total = 0
    teleop_score_total = 0
    teleop_cycles_total = 0
    teleop_successful_cycles_total = 0
    teleop_l4_total = 0
    teleop_net_total = 0
    endgame_score_total = 0
    
    for report in reports:
        # Overall movement
        if report.get("autonomous", {}).get("move") == "yes":
            moved_count += 1
            auto_moved_count += 1
        
        # Auto stats
        auto = report.get("autonomous", {})
        auto_coral_total += auto.get("coral_count", 0)
        auto_score_total += auto.get("score", 0)
        
        # Teleop stats
        teleop = report.get("teleop", {})
        teleop_coral_total += teleop.get("coral_count", 0)
        teleop_score_total += teleop.get("score", 0)
        teleop_cycles_total += teleop.get("cycles", 0)
        teleop_successful_cycles_total += teleop.get("successful_cycles", 0)
        teleop_l4_total += teleop.get("scoring", {}).get("l4_count", 0)
        teleop_net_total += teleop.get("scoring", {}).get("net_count", 0)
        
        # Endgame stats
        endgame = report.get("endgame", {})
        endgame_score_total += endgame.get("score", 0)
        position = endgame.get("position", "none")
        if position == "park":
            park_count += 1
        elif position == "shallow_climb":
            shallow_climb_count += 1
        elif position == "deep_climb":
            deep_climb_count += 1
    
    # Calculate final stats
    stats["percent_moved"] = round(moved_count / len(reports) * 100, 2)
    
    # Auto stats
    stats["auto"]["percent_moved"] = round(auto_moved_count / len(reports) * 100, 2)
    stats["auto"]["avg_coral"] = round(auto_coral_total / len(reports), 2)
    stats["auto"]["avg_score"] = round(auto_score_total / len(reports), 2)
    
    # Teleop stats
    stats["teleop"]["avg_coral"] = round(teleop_coral_total / len(reports), 2)
    stats["teleop"]["avg_score"] = round(teleop_score_total / len(reports), 2)
    stats["teleop"]["avg_cycles"] = round(teleop_cycles_total / len(reports), 2)
    
    if teleop_cycles_total > 0: #Annoying little error fix
        stats["teleop"]["percent_successful_cycles"] = round(teleop_successful_cycles_total / teleop_cycles_total * 100, 2)
    stats["teleop"]["avg_l4"] = round(teleop_l4_total / len(reports), 2)
    stats["teleop"]["avg_net"] = round(teleop_net_total / len(reports), 2)
    
    # Endgame stats
    stats["endgame"]["percent_park"] = round(park_count / len(reports) * 100, 2)
    stats["endgame"]["percent_shallow_climb"] = round(shallow_climb_count / len(reports) * 100, 2)
    stats["endgame"]["percent_deep_climb"] = round(deep_climb_count / len(reports) * 100, 2)
    stats["endgame"]["avg_score"] = round(endgame_score_total / len(reports), 2)
    
    return stats

# Flask stuff
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/scout")
def scout():
    team_number = request.args.get('team_number')
    if (team_number):
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
    # Determine endgame position based on form inputs
    endgame_position = "none"
    if request.form.get("endgame_park") == "yes":
        endgame_position = "park"
    elif request.form.get("endgame_deep_climb") == "yes":
        endgame_position = "deep_climb"
    elif request.form.get("endgame_shallow_climb") == "yes":
        endgame_position = "shallow_climb"
    
    # Calculate auto coral count
    auto_coral_count = int(request.form.get("auto_l4_count") or 0) + int(request.form.get("auto_l3_count") or 0) + int(request.form.get("auto_l2_count") or 0) + int(request.form.get("auto_l1_count") or 0) + int(request.form.get("auto_net_count") or 0)
    
    # Calculate teleop coral count
    teleop_coral_count = int(request.form.get("teleop_l4_count") or 0) + int(request.form.get("teleop_l3_count") or 0) + int(request.form.get("teleop_l2_count") or 0) + int(request.form.get("teleop_l1_count") or 0) + int(request.form.get("teleop_net_count") or 0)
    
    # Calculate scores based on point system
    # Auto scoring
    auto_score = 0
    if request.form.get("auto_move") == "yes":
        auto_score += 3  # 3 points for leaving starting zone
    auto_score += int(request.form.get("auto_l4_count") or 0) * 7   # L4 branch: 7 pts
    auto_score += int(request.form.get("auto_l3_count") or 0) * 6   # L3 branch: 6 pts
    auto_score += int(request.form.get("auto_l2_count") or 0) * 4   # L2 branch: 4 pts
    auto_score += int(request.form.get("auto_l1_count") or 0) * 3   # L1 trough: 3 pts
    auto_score += int(request.form.get("auto_net_count") or 0) * 4  # Net: 4 pts
    
    # Teleop scoring
    teleop_score = 0
    teleop_score += int(request.form.get("teleop_l4_count") or 0) * 5   # L4 branch: 5 pts
    teleop_score += int(request.form.get("teleop_l3_count") or 0) * 4   # L3 branch: 4 pts
    teleop_score += int(request.form.get("teleop_l2_count") or 0) * 3   # L2 branch: 3 pts
    teleop_score += int(request.form.get("teleop_l1_count") or 0) * 2   # L1 trough: 2 pts
    teleop_score += int(request.form.get("teleop_net_count") or 0) * 4  # Net: 4 pts
    
    # Add processor points if used
    if request.form.get("teleop_processor") == "yes":
        teleop_score += 6  # Processor: 6 pts
    
    # Endgame scoring
    endgame_score = 0
    if endgame_position == "park":
        endgame_score = 2  # Park: 2 pts
    elif endgame_position == "shallow_climb":
        endgame_score = 6  # Shallow climb: 6 pts
    elif endgame_position == "deep_climb":
        endgame_score = 12  # Deep climb: 12 pts
    
    # Build a structured report from the form data
    report_data = {
        "team_number": request.form.get("team_number"),
        "team_name": request.form.get("team_name"),
        "event": request.form.get("event"),
        "scout_name": request.form.get("scout_name"),
        "match_number": request.form.get("match_number"),
        "autonomous": {
            "move": request.form.get("auto_move"),
            "coral_count": auto_coral_count,
            "score": auto_score,
            "scoring": {
                "l4_count": int(request.form.get("auto_l4_count") or 0),
                "l3_count": int(request.form.get("auto_l3_count") or 0),
                "l2_count": int(request.form.get("auto_l2_count") or 0),
                "l1_count": int(request.form.get("auto_l1_count") or 0),
                "net_count": int(request.form.get("auto_net_count") or 0)
            },
            "notes": request.form.get("auto_notes")
        },
        "teleop": {
            "coral_count": teleop_coral_count,
            "score": teleop_score,
            "cycles": int(request.form.get("teleop_cycles") or 0),
            "successful_cycles": int(request.form.get("teleop_successful_cycles") or 0),
            "processor": request.form.get("teleop_processor"),
            "scoring": {
                "l4_count": int(request.form.get("teleop_l4_count") or 0),
                "l3_count": int(request.form.get("teleop_l3_count") or 0),
                "l2_count": int(request.form.get("teleop_l2_count") or 0),
                "l1_count": int(request.form.get("teleop_l1_count") or 0),
                "net_count": int(request.form.get("teleop_net_count") or 0)
            },
            "notes": request.form.get("teleop_notes")
        },
        "endgame": {
            "park": request.form.get("endgame_park"),
            "deep_climb": request.form.get("endgame_deep_climb"),
            "shallow_climb": request.form.get("endgame_shallow_climb"),
            "position": endgame_position,
            "score": endgame_score,
            "notes": request.form.get("endgame_notes")
        },
        "additional_notes": request.form.get("additional_notes"),
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    
    # Save the filename of the report
    filename = save_report(report_data)
    
    flash("Report submitted successfully!")
    return redirect(url_for("view_report", filename=filename))

@app.route("/reports")
def reports():
    return render_template("view_report.html", reports=get_all_reports())

@app.route("/report/<filename>")
def view_report(filename):
    report = get_report(filename)
    if not report:
        flash("Report not found")
        return redirect(url_for("reports"))
    
    return render_template("report.html", report=report)

@app.route("/team_stats/<team_number>")
def team_stats(team_number):
    # Get team info from TBA API
    team = get_team_info(team_number)
    if "error" in team:
        flash("Team not found")
        return redirect(url_for("full_stats"))
    
    # Get all reports for this team
    reports = []
    for filename in os.listdir(REPORTS_DIR):
        if filename.startswith(f"{team_number}_") and filename.endswith(".json"):
            report_path = os.path.join(REPORTS_DIR, filename)
            with open(report_path, 'r') as f:
                report = json.load(f)
                report['filename'] = filename
                reports.append(report)
    
    # Sort reports by match number if available
    def get_match_number(report):
        return int(report.get("match_number", 0))
    
    reports.sort(key=get_match_number)
    
    # Generate statistics
    stats = generate_team_stats(reports)
    
    # Get event name from the first report, or default
    event_name = "All Events"
    if reports and 'event' in reports[0]:
        event_key = reports[0]['event']
        event = get_tba_data(f"event/{event_key}")
        if event and "error" not in event:
            event_name = event.get('name', event_key)
    
    return render_template("team_stats.html", team=team, stats=stats, reports=reports, event_name=event_name)

@app.route("/full_stats")
def full_stats():
    # Get all reports
    all_reports = []
    for filename in os.listdir(REPORTS_DIR):
        if filename.endswith(".json"):
            with open(os.path.join(REPORTS_DIR, filename), 'r') as f:
                report = json.load(f)
                all_reports.append(report)
    
    # Group reports by team
    teams_data = {}
    for report in all_reports:
        team_number = report.get("team_number")
        if team_number not in teams_data:
            team_info = get_team_info(team_number)
            teams_data[team_number] = {
                "team_info": team_info,
                "reports": []
            }
        teams_data[team_number]["reports"].append(report)
    
    # Calculate statistics for each team
    for team_number, data in teams_data.items():
        data["stats"] = generate_team_stats(data["reports"])
    
    # Convert to sorted list for template
    teams_list = [
        {
            "team_number": team_number,
            "team_name": data["team_info"].get("nickname", f"Team {team_number}"),
            "reports_count": len(data["reports"]),
            "stats": data["stats"]
        }
        for team_number, data in teams_data.items()
    ]
    
    return render_template("full_stats.html", teams=teams_list)

if __name__ == "__main__":
    app.run(debug=True)

    #I wanna crash out