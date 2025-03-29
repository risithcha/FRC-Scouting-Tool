import datetime
import json
import os
from flask import current_app
import traceback

CACHE_TRACKING_FILE = os.path.join("data", "cache_tracking.json")

def ensure_tracking_file():
    # Make sure the tracking file exists
    if not os.path.exists(CACHE_TRACKING_FILE):
        os.makedirs(os.path.dirname(CACHE_TRACKING_FILE), exist_ok=True)
        with open(CACHE_TRACKING_FILE, 'w') as f:
            json.dump({
                "general": {"last_cleared": None, "item_count": 0, "active": False},
                "stats": {"last_cleared": None, "item_count": 0, "active": False},
                "tba": {"last_cleared": None, "item_count": 0, "active": False}
            }, f)

def get_cache_info():
    # Get cache tracking information
    ensure_tracking_file()
    try:
        with open(CACHE_TRACKING_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error reading cache tracking: {e}")
        # Return default structure on error
        return {
            "general": {"last_cleared": None, "item_count": 0, "active": False},
            "stats": {"last_cleared": None, "item_count": 0, "active": False},
            "tba": {"last_cleared": None, "item_count": 0, "active": False}
        }

def update_cache_info(cache_type, cleared=False, items=None, active=None):
    # Update cache tracking information
    # 
    # Args:
    #     cache_type: 'general', 'stats', or 'tba'
    #     cleared: If True, update last_cleared timestamp
    #     items: If provided, update item count
    #     active: If provided, update active status
    try:
        ensure_tracking_file()
        info = get_cache_info()
        
        if cleared:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            info[cache_type]["last_cleared"] = timestamp
            try:
                from app.utils.logger import log_activity
                log_activity("Cache Cleared", f"{cache_type.title()} cache was cleared")
            except Exception:
                pass
        
        if items is not None:
            info[cache_type]["item_count"] = items
        
        if active is not None:
            info[cache_type]["active"] = active
            try:
                from app.utils.logger import log_activity
                state = "activated" if active else "deactivated"
                log_activity("Cache Status", f"{cache_type.title()} cache was {state}")
            except Exception:
                pass
        
        with open(CACHE_TRACKING_FILE, 'w') as f:
            json.dump(info, f)
            
    except Exception as e:
        print(f"Error updating cache tracking: {e}")

def record_cache_hit(cache_type, key=None):
    # Record a cache record
    try:
        # Only update the active status and increment counter if it hasn't been activated yet
        info = get_cache_info()
        if not info[cache_type]["active"]:
            update_cache_info(cache_type, active=True)
        
        # Update item count
        update_cache_info(cache_type, items=info[cache_type]["item_count"] + 1)
    except Exception as e:
        print(f"Error recording cache hit: {e}")