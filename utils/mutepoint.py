from datetime import timedelta
from typing import Optional, Dict, List, Tuple
from enum import Enum

class OffenseLevel(Enum):
    ADVISORY = "Advisory"
    NOTICE = "Notice"
    WARNING = "Warning"
    PENALTY = "Penalty"
    SUSPENSION = "Suspension"
    EXPULSION = "Expulsion"

class MutePointSystem:
    OFFENSE_CATEGORIES: Dict[OffenseLevel, Dict[str, Tuple[int, List[str]]]] = {
        OffenseLevel.ADVISORY: {
            "Minor Disruption": (0, ["spam", "wrong channel", "bot misuse"]),
            "Self Promotion": (0, ["self-promo", "advertising"]),
            "Chat Etiquette": (0, ["caps", "sticker spam", "emoji spam", "gif spam", "weird gif"]),
            "Bold Text": (0, ["bold text", "text formatting"])
        },
        OffenseLevel.NOTICE: {
            "Offensive Language": (1, ["offensive", "toxic", "bait"]),
            "Mass Ping": (1, ["mass ping", "mass mention"]),
            "Light Toxicity": (1, ["light toxic", "baiting"]),
            "Tickets": (1, ["ticket abuse", "unnecessary ticket"]),
            "Mild Disrespect": (1, ["mild disrespect", "attitude"])
        },
        OffenseLevel.WARNING: {
            "Repeated Spam": (2, ["repeated spam", "continued disruption"]),
            "Trolling": (2, ["troll", "provoke"]),
            "Mod Defiance": (2, ["ignore mod", "mod instruction"])
        },
        OffenseLevel.PENALTY: {
            "Political Content": (3, ["political", "regional"]),
            "Aggressive Trolling": (3, ["aggressive troll", "disruption"]),
            "Targeted Harassment": (3, ["targeted", "harass"])
        },
        OffenseLevel.SUSPENSION: {
            "Family Arguments": (4, ["family", "involving family"]),
            "Staff Disrespect": (4, ["staff disrespect", "extreme disrespect"]),
            "Repeated Harassment": (4, ["repeated harass", "continued harassment"])
        },
        OffenseLevel.EXPULSION: {
            "Serious Targeting": (5, ["serious targeting", "family targeting"]),
            "Hate Speech": (5, ["hate speech", "slur"]),
            "NSFW Content": (5, ["nsfw", "explicit"]),
            "Security Threat": (5, ["raid", "doxx", "threat", "impersonation"])
        }
    }

    # Updated durations based on MP count
    DURATIONS = {
        1: timedelta(minutes=15),     # 1 MP = 15min
        2: timedelta(minutes=40),     # 2 MP = 40min
        3: timedelta(hours=2),        # 3 MP = 2hr
        4: timedelta(hours=6),        # 4 MP = 6hr
        5: timedelta(hours=24),       # 5 MP = 24hr
    }

    # Thresholds for accumulated MPs
    MP_THRESHOLDS = {
        5: timedelta(days=1),         # 5 MP → 1-day mute
        8: timedelta(days=3),         # 8 MP → 3-day mute
        10: timedelta(days=7),        # 10 MP → 7-day mute
        15: None                      # 15 MP → Permanent mute/ban
    }

    @classmethod
    def get_advisory_action(cls, warnings: int) -> Tuple[str, Optional[timedelta]]:
        """
        Determine action for advisory offenses based on warning count
        Returns: (action_type, duration)
        """
        if warnings == 0:
            return "warning", None
        elif warnings == 1:
            return "mute", timedelta(minutes=5)
        else:  # 3rd warning
            return "mp", timedelta(minutes=15)  # Converts to 1 MP

    @classmethod
    def get_points(cls, offense_type: str, warnings: int = 0) -> int:
        """Get points based on offense type and warning count"""
        if offense_type.lower() == "advisory":
            return 1 if warnings >= 2 else 0
            
        for level in OffenseLevel:
            if level.value.lower() in offense_type.lower():
                base_points = list(cls.OFFENSE_CATEGORIES[level].values())[0][0]
                return base_points
                
        return 0

    @classmethod
    def get_duration(cls, total_points: int) -> Optional[timedelta]:
        """Get mute duration based on total points"""
        # Check MP thresholds first
        for threshold, duration in sorted(cls.MP_THRESHOLDS.items(), reverse=True):
            if total_points >= threshold:
                return duration

        # If below thresholds, use regular durations
        return cls.DURATIONS.get(total_points, timedelta(minutes=5))

    @classmethod
    def format_duration(cls, duration: Optional[timedelta]) -> str:
        if duration is None:
            return "Permanent Mute/Ban"
        
        total_minutes = int(duration.total_seconds() / 60)
        
        if total_minutes < 60:
            return f"{total_minutes} minutes"
        elif total_minutes < 1440:  # Less than 24 hours
            hours = total_minutes / 60
            return f"{hours:.1f} hours"
        else:
            days = total_minutes / 1440
            return f"{days:.1f} days"

    @classmethod
    def get_offense_info(cls, offense_type: str, warnings: int = 0) -> Tuple[OffenseLevel, str, int]:
        """Get detailed information about an offense"""
        if offense_type.lower() == "advisory":
            action, _ = cls.get_advisory_action(warnings)
            if action == "mp":
                return OffenseLevel.NOTICE, "Repeated Advisory", 1
            return OffenseLevel.ADVISORY, f"Advisory Warning #{warnings + 1}", 0
            
        for level in OffenseLevel:
            if level.value.lower() in offense_type.lower():
                return level, level.value, cls.get_points(offense_type)
                    
        return OffenseLevel.ADVISORY, "Unknown", 0
