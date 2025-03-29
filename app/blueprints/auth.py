from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask import current_app
from app.services.user_service import user_manager
from app.utils.logger import log_activity
from app.utils.site_settings import get_site_settings
from app.api.tba import TBAClient
from functools import wraps

auth_bp = Blueprint('auth', __name__)

# Authentication decorators
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash("Please log in to access this page")
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'is_admin' not in session or not session['is_admin']:
            flash("Admin access required")
            return redirect(url_for('auth.admin_login'))
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    # User registration
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        if user_manager.create_user(username, password):
            flash("Registration successful! Please log in.")
            log_activity("User Registration", f"New user registered: {username}")
            return redirect(url_for("auth.login"))
        else:
            flash("Username already exists")
    
    return render_template("register.html")

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    # User login
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        if user_manager.authenticate_user(username, password):
            session['username'] = username
            session['is_admin'] = user_manager.is_admin(username)
            flash(f"Welcome back, {username}!")
            log_activity("User Login", f"User logged in: {username}")
            return redirect(url_for("main.index"))
        else:
            flash("Invalid username or password")
    
    return render_template("login.html")

@auth_bp.route("/logout")
def logout():
    # User logout
    username = session.get('username', 'Unknown')
    log_activity("User Logout", f"User logged out: {username}")
    
    session.pop('username', None)
    session.pop('is_admin', None)
    flash("You have been logged out")
    return redirect(url_for("main.index"))

@auth_bp.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    # Admin login
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        # Debug output
        print(f"Admin login attempt: {username}")
        print(f"Config admin username: {current_app.config.get('ADMIN_USERNAME')}")
        print(f"Match: {username == current_app.config.get('ADMIN_USERNAME')}")
        
        if (username == current_app.config.get("ADMIN_USERNAME") and 
            password == current_app.config.get("ADMIN_PASSWORD")):
            session['admin_logged_in'] = True
            session['is_admin'] = True
            session['username'] = username
            flash("Admin login successful")
            log_activity("Admin Login", "Admin user logged in")
            return redirect(url_for("admin.dashboard"))
        else:
            flash("Invalid admin credentials")
    
    return render_template("admin_login.html")

@auth_bp.route("/admin/logout")
def admin_logout():
    # Admin logout
    session.pop('admin_logged_in', None)
    session.pop('is_admin', None)
    flash("You have been logged out")
    return redirect(url_for("main.index"))


@auth_bp.route("/settings", methods=["GET", "POST"])
@login_required
def user_settings():
    # User settings page
    if request.method == "POST":
        # Get current username from session
        username = session.get('username')
        
        # Collect settings from form
        settings = {
            "default_event": request.form.get("default_event", "")
        }
        
        # Update user settings
        success = user_manager.update_user_settings(username, settings)
        
        if success:
            flash("Settings saved successfully!")
            log_activity("Settings Update", f"User {username} updated their settings")
        else:
            flash("Error saving settings")
            
        return redirect(url_for("auth.user_settings"))
        
    # GET request - show settings form
    username = session.get('username')
    
    # Get current settings
    settings = user_manager.get_user_settings(username)
    
    # Get site settings (for active events)
    site_settings = get_site_settings()
    
    # Get only active events for dropdown
    all_events = TBAClient.get_events()
    active_events = []
    
    for event in all_events:
        if event.get("key") in site_settings.get("active_events", []):
            active_events.append(event)
    
    return render_template("user_settings.html", settings=settings, events=active_events)