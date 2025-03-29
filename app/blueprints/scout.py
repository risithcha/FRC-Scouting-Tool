from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.blueprints.auth import login_required
from app.services.user_service import user_manager
from app.services.report_service import report_service
from app.api.tba import TBAClient
from app.utils.site_settings import get_site_settings
from app.utils.logger import log_activity
from app.utils.stats_utils import invalidate_team_stats_cache

scout_bp = Blueprint('scout', __name__, url_prefix='/scout')

@scout_bp.route("/team")
@login_required
def scout_team():
    return render_template("scout_team.html")

@scout_bp.route("", methods=["GET"])
@login_required
def scout():
    # Scout a team
    team_number = request.args.get("team_number")
    
    if not team_number:
        return redirect(url_for("scout.scout_team"))
    
    # Get team info from TBA
    team = TBAClient.get_team_info(team_number)
    
    # Check if team info was retrieved successfully
    if isinstance(team, dict) and "error" in team:
        flash(f"Error retrieving team {team_number}: {team.get('error')}")
        return redirect(url_for("scout.scout_team"))
    
    # If we have no data at all for the team
    if not team:
        flash(f"No information found for team {team_number}")
        team = {
            "team_number": team_number,
            "nickname": f"Team {team_number}"
        }
    
    # Get site settings (for active events)
    site_settings = get_site_settings()
    
    # Get only active events for dropdown
    all_events = TBAClient.get_events()
    active_events = []
    
    for event in all_events:
        if event.get("key") in site_settings.get("active_events", []):
            active_events.append(event)
    
    # Get user settings for default values
    username = session.get('username')
    user_settings = user_manager.get_user_settings(username)
    
    return render_template(
        "scout_form.html", 
        team=team, 
        events=active_events, 
        username=username,
        user_settings=user_settings,
        system_notice=site_settings.get("system_notice", "")
    )

@scout_bp.route("/submit", methods=["POST"])
@login_required
def submit_report():
    # Submit a scouting report
    # Process endgame position
    endgame_position = "none"
    if request.form.get("endgame_park") == "yes":
        endgame_position = "park"
    elif request.form.get("endgame_deep_climb") == "yes":
        endgame_position = "deep_climb"
    elif request.form.get("endgame_shallow_climb") == "yes":
        endgame_position = "shallow_climb"
    
    # Build a report from the form data
    report_data = {
        "team_number": request.form.get("team_number"),
        "team_name": request.form.get("team_name"),
        "event": request.form.get("event"),
        "scout_name": request.form.get("scout_name"),
        "match_number": request.form.get("match_number"),
        "autonomous": {
            "move": request.form.get("auto_move"),
            "scoring": {
                "l4_branch_successful": int(request.form.get("auto_l4_branch_successful") or 0),
                "l3_branch_successful": int(request.form.get("auto_l3_branch_successful") or 0),
                "l2_branch_successful": int(request.form.get("auto_l2_branch_successful") or 0),
                "l1_trough_successful": int(request.form.get("auto_l1_trough_successful") or 0),
                "net_successful": int(request.form.get("auto_net_successful") or 0)
            },
            "notes": request.form.get("auto_notes")
        },
        "teleop": {
            "cycles": int(request.form.get("teleop_cycles") or 0),
            "successful_cycles": int(request.form.get("teleop_successful_cycles") or 0),
            "processor": request.form.get("teleop_processor"),
            "scoring": {
                "l4_branch_successful": int(request.form.get("teleop_l4_branch_successful") or 0),
                "l3_branch_successful": int(request.form.get("teleop_l3_branch_successful") or 0),
                "l2_branch_successful": int(request.form.get("teleop_l2_branch_successful") or 0),
                "l1_trough_successful": int(request.form.get("teleop_l1_trough_successful") or 0),
                "net_successful": int(request.form.get("teleop_net_successful") or 0)
            },
            "notes": request.form.get("teleop_notes")
        },
        "endgame": {
            "park": request.form.get("endgame_park"),
            "deep_climb": request.form.get("endgame_deep_climb"),
            "shallow_climb": request.form.get("endgame_shallow_climb"),
            "position": endgame_position,
            "notes": request.form.get("endgame_notes")
        },
        "additional_notes": request.form.get("additional_notes"),
    }
    
    # Save the report
    filename = report_service.save_report(report_data)
    
    # After saving the report, invalidate the cache for this team
    team_number = request.form.get("team_number")
    invalidate_team_stats_cache(team_number)
    
    # Log the activity
    log_activity(
        "Scouting Report", 
        f"New report submitted for Team {report_data['team_number']} at Event {report_data['event']}"
    )
    
    flash("Report submitted successfully!")
    return redirect(url_for("reports.view_reports"))