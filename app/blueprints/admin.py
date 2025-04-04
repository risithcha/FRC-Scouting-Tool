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
from app.utils.background_tasks import task_manager
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
    
    # Get task status for the dashboard
    sync_task_status = task_manager.get_task_status('sync_reports')
    
    return render_template(
        "admin_dashboard.html",
        local_count=local_count,
        last_sync=last_sync,
        logs=logs,
        cache_info=cache_info,
        task_status=sync_task_status
    )

@admin_bp.route("/sync_status")
@admin_required
def sync_status():
    # Check the status of background sync tasks
    status = task_manager.get_task_status('sync_reports')
    
    if not status or status.get('status') == 'not_found':
        flash("No recent sync task found")
        return redirect(url_for("admin.dashboard"))
    
    return render_template(
        "admin_sync_status.html", 
        status=status,
        is_running=status.get('status') == 'running'
    )

@admin_bp.route("/sync", methods=["POST"])
@admin_required
def sync_from_drive():
    # Start background sync from Google Drive to local storage
    result = task_manager.start_task(
        'sync_reports', 
        report_service.sync_reports_from_drive
    )
    
    if result['status'] == 'already_running':
        flash("A sync is already in progress. Please wait for it to complete.")
    else:
        flash("Sync started in the background. You can continue using the app while it runs.")
        log_activity("Manual Sync", "Started background sync from Google Drive")
    
    return redirect(url_for("admin.sync_status"))

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
        env_admin_username=current_app.config.get('ADMIN_USERNAME', '')
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

@admin_bp.route("/delete_user/<username>", methods=["POST"])
@admin_required
def delete_user(username):
    # Delete a user
    # Only the root admin can delete users
    if session.get('username') != current_app.config.get('ADMIN_USERNAME'):
        flash("Only the system administrator can delete users")
        return redirect(url_for("admin.user_management"))
    
    # Don't allow deleting the root admin
    if username == current_app.config.get('ADMIN_USERNAME'):
        flash("Cannot delete the system administrator account")
        return redirect(url_for("admin.user_management"))
    
    # Delete the user
    result = user_manager.delete_user(username)
    
    if result:
        flash(f"User {username} has been deleted")
        log_activity("Admin Action", f"Deleted user {username}")
    else:
        flash(f"Failed to delete user {username}")
    
    return redirect(url_for("admin.user_management"))

def get_last_sync_time():
    # Get the last time reports were synced from Google Drive
    sync_file = os.path.join("data", "last_sync.txt")
    if os.path.exists(sync_file):
        with open(sync_file, 'r') as f:
            return f.read().strip()
    return "Never"