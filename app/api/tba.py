import requests
from flask import current_app
import datetime
from app.utils.cache import tracked_memoize, cache
from app.utils.cache_tracker import update_cache_info

class TBAClient:
    # Communicate with the Blue Alliance API
    
    @staticmethod
    @tracked_memoize(timeout=3600, cache_type='tba')  # Cache API responses for 1 hour
    def get_data(endpoint):
        # Get data from The Blue Alliance API
        url = f"https://www.thebluealliance.com/api/v3/{endpoint}"
        headers = {"X-TBA-Auth-Key": current_app.config["TBA_API_KEY"]}
        
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"API request failed with status {response.status_code}"}
    
    @staticmethod
    @tracked_memoize(timeout=86400, cache_type='tba')  # Cache for 24 hours since team data almost never changes
    def get_team_info(team_number):
        # Get team information
        return TBAClient.get_data(f"team/frc{team_number}")
    
    @staticmethod
    @tracked_memoize(timeout=1800, cache_type='tba')  # Cache for 30 minutes since OPRs change during events
    def get_team_oprs(event_key, team_number):
        # Get OPR data for a team at an event
        oprs = TBAClient.get_data(f"event/{event_key}/oprs")
        if "oprs" not in oprs or f"frc{team_number}" not in oprs["oprs"]:
            return {"opr": "N/A", "dpr": "N/A", "ccwm": "N/A"}
        
        return {
            "opr": round(oprs["oprs"][f"frc{team_number}"], 2),
            "dpr": round(oprs["dprs"][f"frc{team_number}"], 2),
            "ccwm": round(oprs["ccwms"][f"frc{team_number}"], 2)
        }
    
    @staticmethod
    @tracked_memoize(timeout=3600, cache_type='tba')
    def get_events():
        # Get all events for {CURRENT YEAR}
        year = 2025
        
        events = TBAClient.get_data(f"events/{year}")
        return events