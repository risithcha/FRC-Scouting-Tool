from app.utils.cache import cache, tracked_memoize
from app.utils.cache_tracker import get_cache_info, update_cache_info
import hashlib
import json

@tracked_memoize(timeout=3600, cache_type='stats')  # Cache for 1 hour
def generate_team_stats(reports):
    # Generate team statistics from reports with caching

    # Create a simple stats object
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
    
    # Convert reports to a list if it's not already, and ensure it's legit
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

def invalidate_team_stats_cache(team_number=None):
    # Invalidate the team stats cache for a specific team or all teams
    # MUH HA HA HA HA. STUPID ERROR GONE
    cache.delete_memoized(generate_team_stats)
    
    # Update cache tracking info
    update_cache_info('stats', cleared=True, active=False, items=0)