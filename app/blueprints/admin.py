from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from app.blueprints.auth import admin_required
from app.services.report_service import report_service
from app.services.user_service import user_manager
from app.api.tba import TBAClient
from app.utils.site_settings import get_site_settings, save_site_settings
from app.utils.logger import log_activity, get_recent_logs
from app.utils.cache import cache
from app.utils.stats_utils import invalidate_team_stats_cache
from app.utils.cache_tracker import get_cache_info, update_cache_info
import os
import datetime

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route("")
@admin_required
def dashboard():
    # Admin dashboard
    # Count local reports
    reports_dir = os.path.join("data", "reports")
    local_count = len([f for f in os.listdir(reports_dir) if f.endswith('.json')])
    
    # Get last sync time
    last_sync = get_last_sync_time()
    
    # Get recent logs
    logs = get_recent_logs()
    
    # Get cache info
    cache_info = get_cache_info()
    
    return render_template(
        "admin_dashboard.html",
        local_count=local_count,
        last_sync=last_sync,
        logs=logs,
        cache_info=cache_info
    )

@admin_bp.route("/sync", methods=["POST"])
@admin_required
def sync_from_drive():
    # Sync reports from Google Drive to local storage
    result = report_service.sync_reports_from_drive()
    
    flash(f"Sync completed: {result['synced']} files downloaded, {result['failed']} failed") #How exactly does this work?
    log_activity("Manual Sync", f"Synced {result['synced']} files from Google Drive to local storage")
    
    return redirect(url_for("admin.dashboard"))

@admin_bp.route("/event_settings", methods=["GET", "POST"])
@admin_required
def event_settings():
    # Edit site-wide event settings
    site_settings = get_site_settings()
    
    if request.method == "POST":
        # Get form data
        active_events = request.form.getlist("active_events")
        default_event = request.form.get("default_event")
        system_notice = request.form.get("system_notice", "")
        
        # Update settings
        site_settings["active_events"] = active_events
        site_settings["default_event"] = default_event
        site_settings["system_notice"] = system_notice
        
        # Save settings
        save_site_settings(site_settings)
        
        flash("Event settings updated successfully")
        log_activity("Admin Action", f"Updated event settings: {len(active_events)} active events, default: {default_event}")
        
        return redirect(url_for("admin.event_settings"))
    
    # Get all available events from TBA (current year)
    all_events = TBAClient.get_events()
    
    return render_template(
        "admin_event_settings.html",
        site_settings=site_settings,
        all_events=all_events
    )

@admin_bp.route("/user_management")
@admin_required
def user_management():
    # User management page
    # Get all users
    users = user_manager.get_all_users()
    
    return render_template(
        "admin_user_management.html",
        users=users,
        env_admin_username=current_app.config.get('ADMIN_USERNAME', '') #What's this for?
    )

@admin_bp.route("/clear_cache", methods=["POST"])
@admin_required
def clear_cache():
    # Clear all cached data
    cache.clear()
    update_cache_info('general', cleared=True, active=False, items=0)
    flash("Cache cleared successfully")
    log_activity("Admin Action", "Cleared application cache")
    return redirect(url_for("admin.dashboard"))

@admin_bp.route("/clear_stats_cache", methods=["POST"])
@admin_required
def clear_stats_cache():
    # Clear cached stats data
    invalidate_team_stats_cache()
    flash("Statistics cache cleared successfully")
    log_activity("Admin Action", "Cleared statistics cache")
    return redirect(url_for("admin.dashboard"))

@admin_bp.route("/clear_tba_cache", methods=["POST"])
@admin_required
def clear_tba_cache():
    # Clear TBA API cached data
    # Find all TBA methods that are cached then delete them
    for attr_name in dir(TBAClient):
        attr = getattr(TBAClient, attr_name)
        if hasattr(attr, 'uncached') and getattr(attr, 'cache_type', None) == 'tba':
            cache.delete_memoized(attr)
    
    update_cache_info('tba', cleared=True, active=False, items=0)
    flash("TBA API cache cleared successfully")
    log_activity("Admin Action", "Cleared TBA API cache")
    return redirect(url_for("admin.dashboard"))

@admin_bp.route("/user/<username>/toggle_admin", methods=["POST"])
@admin_required
def toggle_admin_status(username):
    # Toggle admin status for a user
    # Only the admin ADMIN (from the .env file) will be able to change admin status
    if session.get('username') != current_app.config.get('ADMIN_USERNAME') and not session.get('admin_logged_in'):
        flash("Only the system administrator can change admin status")
        return redirect(url_for("admin.user_management"))
    
    # Get the requested action
    action = request.form.get("action")
    
    if action == "promote":
        # Set user as admin
        user_manager.set_admin_status(username, True)
        flash(f"User {username} has been promoted to admin")
        log_activity("Admin Action", f"Promoted {username} to admin status")
    elif action == "demote":
        # Remove admin status
        user_manager.set_admin_status(username, False)
        flash(f"User {username} has been demoted from admin")
        log_activity("Admin Action", f"Removed admin status from {username}")
    else:
        flash("Invalid action")
    
    return redirect(url_for("admin.user_management"))

def get_last_sync_time():
    # Get the last time reports were synced from Google Drive
    sync_file = os.path.join("data", "last_sync.txt")
    if os.path.exists(sync_file):
        with open(sync_file, 'r') as f:
            return f.read().strip()
    return "Never"