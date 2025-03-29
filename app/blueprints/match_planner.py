from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.blueprints.auth import login_required
from app.services.user_service import user_manager 
from app.services.report_service import report_service
from app.api.tba import TBAClient
from app.utils.site_settings import get_site_settings
import datetime

planner_bp = Blueprint('planner', __name__, url_prefix='/match_planner')

@planner_bp.route("")
@login_required
def match_planner():
    # Match planner home page
    # Get site settings
    site_settings = get_site_settings()
    
    # Default to the event in user settings, then site default, then fallback
    username = session.get('username')
    user_settings = user_manager.get_user_settings(username)
    event_key = user_settings.get("default_event") or site_settings.get("default_event", "2025wabon")
    
    # Get event info
    event = TBAClient.get_data(f"event/{event_key}")
    event_name = event.get("name", event_key) if not isinstance(event, dict) or "error" not in event else event_key
    
    # Get matches with scouting status
    planner_data = get_match_scouting_status(event_key)
    
    # Get list of active events
    all_events = TBAClient.get_events()
    active_events = []
    
    for event in all_events:
        if event.get("key") in site_settings.get("active_events", []):
            active_events.append(event)
    
    # Current time
    current_time = int(datetime.datetime.now().timestamp())
    
    return render_template(
        "match_planner.html",
        planner_data=planner_data,
        event_key=event_key,
        event_name=event_name,
        events=active_events,
        current_time=current_time,
        system_notice=site_settings.get("system_notice", "")
    )

@planner_bp.route("/<event_key>")
@login_required
def match_planner_event(event_key):
    # Match planner for a specific event
    # Get event info
    event = TBAClient.get_data(f"event/{event_key}")
    event_name = event.get("name", event_key) if not isinstance(event, dict) or "error" not in event else event_key
    
    # Get matches with scouting status
    planner_data = get_match_scouting_status(event_key)
    
    # Get list of all events
    events = TBAClient.get_events()
    
    # Current time
    current_time = int(datetime.datetime.now().timestamp())
    
    return render_template(
        "match_planner.html",
        planner_data=planner_data,
        event_key=event_key,
        event_name=event_name,
        events=events,
        current_time=current_time
    )

def get_event_matches(event_key, sort_by_time=True):
    # Get all matches for a specific event
    matches = TBAClient.get_data(f"event/{event_key}/matches")
    
    # If not valid response just return empty list
    if not isinstance(matches, list):
        return []
    
    # Sort matches by either predicted time or match number
    if sort_by_time:
        matches.sort(key=lambda x: x.get("predicted_time", x.get("time", 0)) or 0) #lambda :0
    else:
        # Sort by comp level, then match number
        def match_sort_key(match):
            comp_level = match.get("comp_level", "zz")  # Default to high value if missing
            match_number = match.get("match_number", 999)  # Default to high value if missing
            
            # Sort by qualification, quarters, semis, finals
            level_order = {"qm": 0, "qf": 1, "sf": 2, "f": 3}
            level_val = level_order.get(comp_level, 999)
            
            return (level_val, match_number)
            
        matches.sort(key=match_sort_key)
    
    return matches

def get_match_scouting_status(event_key):
    # Get scouting status for all teams in all matches
    matches = get_event_matches(event_key)
    if not matches:
        return []
    
    # Get all reports
    all_reports = report_service.get_all_reports()
    
    # Build a dict of team numbers to count of reports
    team_scouted = {}
    match_scouted = {}  # Track which teams have been scouted in which matches
    
    for report in all_reports:
        if report.get("event") == event_key:
            team_number = report.get("team_number")
            match_number = report.get("match_number", "0")
            
            # Track if team has been scouted
            if team_number:
                team_scouted[team_number] = True
            
            # Track if team has been scouted in this specific match
            if team_number and match_number:
                match_key = f"{team_number}_{match_number}"
                match_scouted[match_key] = True
    
    # Data for the match planner
    planner_data = []
    
    for match in matches:
        match_data = {
            "match_key": match.get("key"),
            "match_number": match.get("match_number"),
            "comp_level": match.get("comp_level", "qm").upper(),
            "time": match.get("predicted_time", match.get("time", 0)),
            "alliances": {
                "red": [],
                "blue": []
            }
        }
        
        # Add teams with scouting status
        for alliance_color in ["red", "blue"]:
            alliance = match.get("alliances", {}).get(alliance_color, {})
            for team_key in alliance.get("team_keys", []):
                team_number = team_key.replace("frc", "")
                
                # Get team info from TBA
                team_info = TBAClient.get_team_info(team_number)
                team_name = team_info.get("nickname", team_number) if not isinstance(team_info, dict) or "error" not in team_info else team_number
                
                # Check if this team has been scouted at all
                is_scouted = team_scouted.get(team_number, False)
                
                # Check if this team has been scouted in this specific match
                match_key = f"{team_number}_{match.get('match_number')}"
                this_match_scouted = match_scouted.get(match_key, False)
                
                team_data = {
                    "team_number": team_number,
                    "team_name": team_name,
                    "scouted": is_scouted,
                    "match_scouted": this_match_scouted
                }
                
                match_data["alliances"][alliance_color].append(team_data)
        
        planner_data.append(match_data)
    
    return planner_data