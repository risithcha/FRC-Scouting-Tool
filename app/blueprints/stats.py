from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.services.report_service import report_service
from app.api.tba import TBAClient
from app.utils.logger import log_activity
from app.utils.site_settings import get_site_settings
from app.utils.stats_utils import generate_team_stats

stats_bp = Blueprint('stats', __name__, url_prefix='/stats')

@stats_bp.route("/team/<team_number>")
def team_stats(team_number):
    # Team statistics page
    # Get team info from TBA API
    team = TBAClient.get_team_info(team_number)
    if "error" in team:
        flash("Team not found")
        return redirect(url_for("stats.full_stats"))
    
    # Get all reports for this team
    reports = report_service.get_team_reports(team_number)
    
    # Generate statistics
    stats = generate_team_stats(reports)
    
    # Get event name from the first report
    event_name = "All Events"
    event_key = "2025wabon"
    if reports and 'event' in reports[0]:
        event_key = reports[0]['event']
        event = TBAClient.get_data(f"event/{event_key}")
        if event and "error" not in event:
            event_name = event.get('name', event_key)
    
    # Get team OPR data
    opr_data = TBAClient.get_team_oprs(event_key, team_number)
    
    return render_template(
        "team_stats.html", 
        team=team, 
        stats=stats, 
        reports=reports, 
        event_name=event_name, 
        opr_data=opr_data
    )

@stats_bp.route("/full")
def full_stats():
    # Full team statistics page
    # Get all reports
    all_reports = report_service.get_all_reports()
    
    # Determine which event to use for rankings
    event_key = "2025wabon"  # Default to a predetermined event
    
    # Get rankings data from TBA
    rankings_data = TBAClient.get_data(f"event/{event_key}/rankings")
    rankings_dict = {}
    
    # Process rankings data
    if rankings_data and "rankings" in rankings_data:
        for team_ranking in rankings_data["rankings"]:
            team_key = team_ranking["team_key"]
            team_number = team_key.replace("frc", "")
            rankings_dict[team_number] = {
                "rank": team_ranking["rank"],
                "record": f"{team_ranking.get('record', {}).get('wins', 0)}-{team_ranking.get('record', {}).get('losses', 0)}-{team_ranking.get('record', {}).get('ties', 0)}",
                "ranking_score": team_ranking.get("sort_orders", [0])[0]
            }
    
    # Group reports by team
    teams_data = {}
    for report in all_reports:
        team_number = report.get("team_number")
        if team_number not in teams_data:
            team_info = TBAClient.get_team_info(team_number)
            teams_data[team_number] = {
                "team_info": team_info,
                "reports": []
            }
        teams_data[team_number]["reports"].append(report)
    
    # Calculate statistics for each team
    for team_number, data in teams_data.items():
        data["stats"] = generate_team_stats(data["reports"])
        
        # Add ranking data if available
        if team_number in rankings_dict:
            data["ranking"] = rankings_dict[team_number]
        else:
            data["ranking"] = {"rank": 999, "record": "0-0-0", "ranking_score": 0}
    
    # Convert to list
    teams_list = []
    for team_number, data in teams_data.items():
        teams_list.append({
            "team_number": team_number,
            "team_name": data["team_info"].get("nickname", f"Team {team_number}"),
            "reports_count": len(data["reports"]),
            "stats": data["stats"],
            "rank": data.get("ranking", {}).get("rank", 999),
            "record": data.get("ranking", {}).get("record", "0-0-0"),
            "ranking_score": data.get("ranking", {}).get("ranking_score", 0)
        })
    
    # Sort teams by rank
    def get_team_rank(team):
        return team["rank"]
    teams_list.sort(key=get_team_rank)
    
    return render_template("full_stats.html", teams=teams_list, event_key=event_key)

def generate_team_stats(reports):
    # Generate team statistics from reports
    stats = {
        "games_played": 0,
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
    
    # Convert reports to a list if it's not already, and ensure it's valid!
    if not isinstance(reports, list):
        print(f"Warning: reports is not a list, it's a {type(reports)}")
        return stats
        
    if not reports:
        return stats
    
    # Set games played
    stats["games_played"] = len(reports)
    
    # Calculate overall metrics
    moved_count = 0
    auto_moved_count = 0
    park_count = 0
    shallow_climb_count = 0
    deep_climb_count = 0
    
    # Values for averaging
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
    num_reports = len(reports)
    stats["percent_moved"] = round(moved_count / num_reports * 100, 2)
    
    # Auto stats
    stats["auto"]["percent_moved"] = round(auto_moved_count / num_reports * 100, 2)
    stats["auto"]["avg_coral"] = round(auto_coral_total / num_reports, 2)
    stats["auto"]["avg_score"] = round(auto_score_total / num_reports, 2)
    
    # Teleop stats
    stats["teleop"]["avg_coral"] = round(teleop_coral_total / num_reports, 2)
    stats["teleop"]["avg_score"] = round(teleop_score_total / num_reports, 2)
    stats["teleop"]["avg_cycles"] = round(teleop_cycles_total / num_reports, 2)
    
    if teleop_cycles_total > 0:
        stats["teleop"]["percent_successful_cycles"] = round(teleop_successful_cycles_total / teleop_cycles_total * 100, 2)
    
    stats["teleop"]["avg_l4"] = round(teleop_l4_total / num_reports, 2)
    stats["teleop"]["avg_net"] = round(teleop_net_total / num_reports, 2)
    
    # Endgame stats
    stats["endgame"]["percent_park"] = round(park_count / num_reports * 100, 2)
    stats["endgame"]["percent_shallow_climb"] = round(shallow_climb_count / num_reports * 100, 2)
    stats["endgame"]["percent_deep_climb"] = round(deep_climb_count / num_reports * 100, 2)
    stats["endgame"]["avg_score"] = round(endgame_score_total / num_reports, 2)
    
    return stats