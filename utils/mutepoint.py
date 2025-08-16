from datetime import timedelta
from typing import Optional, Dict, List, Tuple
from enum import Enum

class OffenseLevel(Enum):
    ADVISORY = "⚪ Advisory"
    NOTICE = "🟢 Notice"
    WARNING = "🟡 Warning"
    PENALTY = "🟠 Penalty"
    SUSPENSION = "🟠 Suspension"
    EXPULSION = "🔴 Expulsion"

class MutePointSystem:
    OFFENSE_CATEGORIES: Dict[OffenseLevel, Dict[str, Tuple[int, List[str]]]] = {
        OffenseLevel.ADVISORY: {
            "Minor Disruption": (0, ["spam", "wrong channel", "bold text"]),
            "Self Promotion": (0, ["self-promo", "advertising"]),
            "Chat Etiquette": (0, ["caps", "sticker spam", "emoji spam"]),
            "Language": (0, ["offensive", "inappropriate"])
        },
        OffenseLevel.NOTICE: {
            "Mass Ping": (1, ["mass ping", "mass mention"]),
            "Harassment": (1, ["harass", "personal attack"])
        },
        OffenseLevel.WARNING: {
            "Repeated Offense": (2, ["repeated spam", "trolling", "repeated advisory"])
        },
        OffenseLevel.PENALTY: {
            "Political Content": (3, ["political", "regional"])
        },
        OffenseLevel.SUSPENSION: {
            "Family Arguments": (4, ["family", "involving family"])
        },
        OffenseLevel.EXPULSION: {
            "Serious Targeting": (5, ["serious targeting", "family targeting"]),
            "NSFW Content": (5, ["nsfw", "explicit", "inappropriate content"])
        }
    }

    DURATIONS = {
        0: timedelta(minutes=5),     # Advisory - 5 minutes
        1: timedelta(minutes=30),    # Notice - 30 minutes
        2: timedelta(hours=2),       # Warning - 2 hours
        3: timedelta(hours=12),      # Penalty - 12 hours
        4: timedelta(days=1),        # Suspension - 1 day
        5: timedelta(days=3),        # Expulsion - 3 days
        6: None                      # Ban consideration
    }

    @classmethod
    def get_points(cls, reason: str) -> int:
        reason_lower = reason.lower()
        
        # First check for repeated advisory offenses
        if "repeated" in reason_lower and any(keyword in reason_lower 
            for keywords in cls.OFFENSE_CATEGORIES[OffenseLevel.ADVISORY].values() 
            for keyword in keywords[1]):
            return 1  # Repeated advisory becomes 1 MP
        
        # Check each category and its offenses
        for level in OffenseLevel:
            for offense_name, (points, keywords) in cls.OFFENSE_CATEGORIES[level].items():
                if any(keyword in reason_lower for keyword in keywords):
                    return points
        
        return 0  # Default to advisory if no match

    @classmethod
    def get_duration(cls, total_points: int) -> Optional[timedelta]:
        if total_points >= 6:
            return None  # Trigger ban consideration
        return cls.DURATIONS.get(total_points, timedelta(minutes=5))

    @classmethod
    def format_duration(cls, duration: Optional[timedelta]) -> str:
        if duration is None:
            return "Ban Vote Required"
        
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
    def get_offense_info(cls, reason: str) -> Tuple[OffenseLevel, str, int]:
        """Get detailed information about an offense"""
        reason_lower = reason.lower()
        
        # Check for repeated advisory first
        if "repeated" in reason_lower:
            for offense_name, (_, keywords) in cls.OFFENSE_CATEGORIES[OffenseLevel.ADVISORY].items():
                if any(keyword in reason_lower for keyword in keywords):
                    return OffenseLevel.NOTICE, f"Repeated {offense_name}", 1
        
        # Check regular offenses
        for level in OffenseLevel:
            for offense_name, (points, keywords) in cls.OFFENSE_CATEGORIES[level].items():
                if any(keyword in reason_lower for keyword in keywords):
                    return level, offense_name, points
                    
        return OffenseLevel.ADVISORY, "Other", 0
