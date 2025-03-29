import datetime
import json

class Report:
    # Scouting report data model
    
    def __init__(self, team_number, team_name, event, scout_name, match_number):
        self.team_number = team_number
        self.team_name = team_name
        self.event = event
        self.scout_name = scout_name
        self.match_number = match_number
        self.timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Initialize sections
        self.autonomous = {
            "move": "no",
            "coral_count": 0,
            "score": 0,
            "scoring": {
                "l4_count": 0,
                "l3_count": 0,
                "l2_count": 0,
                "l1_count": 0,
                "net_count": 0
            },
            "notes": ""
        }
        
        self.teleop = {
            "coral_count": 0,
            "score": 0,
            "cycles": 0,
            "successful_cycles": 0,
            "processor": "no",
            "scoring": {
                "l4_count": 0,
                "l3_count": 0,
                "l2_count": 0,
                "l1_count": 0,
                "net_count": 0
            },
            "notes": ""
        }
        
        self.endgame = {
            "park": "no",
            "deep_climb": "no",
            "shallow_climb": "no",
            "position": "none",
            "score": 0,
            "notes": ""
        }
        
        self.additional_notes = ""
        self.filename = None
    
    def calculate_scores(self):
        # Calculate scores for auto, teleop, and endgame
        # Auto scoring
        self.autonomous["score"] = 0
        self.autonomous["score"] += self.auto_successful("l4_branch") * 7  # L4: 7 pts
        self.autonomous["score"] += self.auto_successful("l3_branch") * 6  # L3: 6 pts
        self.autonomous["score"] += self.auto_successful("l2_branch") * 4  # L2: 4 pts
        self.autonomous["score"] += self.auto_successful("l1_trough") * 3  # L1: 3 pts
        self.autonomous["score"] += self.auto_successful("net") * 4        # Net: 4 pts
        
        # Calculate auto coral count
        self.autonomous["coral_count"] = (
            self.auto_successful("l4_branch") +
            self.auto_successful("l3_branch") +
            self.auto_successful("l2_branch") +
            self.auto_successful("l1_trough") +
            self.auto_successful("net")
        )
        
        # Teleop scoring
        self.teleop["score"] = 0
        self.teleop["score"] += self.teleop_successful("l4_branch") * 5  # L4: 5 pts
        self.teleop["score"] += self.teleop_successful("l3_branch") * 4  # L3: 4 pts
        self.teleop["score"] += self.teleop_successful("l2_branch") * 3  # L2: 3 pts
        self.teleop["score"] += self.teleop_successful("l1_trough") * 2  # L1: 2 pts
        self.teleop["score"] += self.teleop_successful("net") * 4        # Net: 4 pts
        
        # Calculate teleop coral count
        self.teleop["coral_count"] = (
            self.teleop_successful("l4_branch") +
            self.teleop_successful("l3_branch") +
            self.teleop_successful("l2_branch") +
            self.teleop_successful("l1_trough") +
            self.teleop_successful("net")
        )
        
        # Endgame scoring
        self.endgame["score"] = 0
        if self.endgame["position"] == "park":
            self.endgame["score"] = 2  # Park: 2 pts
        elif self.endgame["position"] == "shallow_climb":
            self.endgame["score"] = 6  # Shallow climb: 6 pts
        elif self.endgame["position"] == "deep_climb":
            self.endgame["score"] = 12  # Deep climb: 12 pts
    
    def auto_successful(self, key):
        # Get auto successful count for a scoring location
        return self.autonomous.get("scoring", {}).get(f"{key}_successful", 0)
    
    def teleop_successful(self, key):
        # Get teleop successful count for a scoring location
        return self.teleop.get("scoring", {}).get(f"{key}_successful", 0)
    
    def to_dict(self):
        # Convert report to dictionary
        return {
            "team_number": self.team_number,
            "team_name": self.team_name,
            "event": self.event,
            "scout_name": self.scout_name,
            "match_number": self.match_number,
            "timestamp": self.timestamp,
            "autonomous": self.autonomous,
            "teleop": self.teleop,
            "endgame": self.endgame,
            "additional_notes": self.additional_notes,
            "filename": self.filename
        }
    
    @classmethod
    def from_dict(cls, data):
        # Create a report from dictionary data
        report = cls(
            data.get("team_number"), 
            data.get("team_name"),
            data.get("event"),
            data.get("scout_name"),
            data.get("match_number")
        )
        
        report.timestamp = data.get("timestamp", report.timestamp)
        report.autonomous = data.get("autonomous", report.autonomous)
        report.teleop = data.get("teleop", report.teleop)
        report.endgame = data.get("endgame", report.endgame)
        report.additional_notes = data.get("additional_notes", "")
        report.filename = data.get("filename")
        
        return report