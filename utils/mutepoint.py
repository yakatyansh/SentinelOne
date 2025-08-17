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
    OFFENSE_CATEGORIES: Dict[str, Dict[str, List[str]]] = {
        "advisory": {
            "spam": ["minor spam", "wrong channel", "bot misuse"],
            "formatting": ["bold text", "caps"],
            "media": ["sticker spam", "emoji spam", "gif spam", "weird gif"],
            "promotion": ["self-promo"]
        },
        "notice": {
            "language": ["offensive", "toxicity", "disrespect"],
            "disruption": ["mass ping", "ticket abuse", "baiting"]
        },
        "warning": {
            "repeat": ["repeated spam", "trolling"],
            "behavior": ["provoking", "ignore mod"]
        },
        "penalty": {
            "serious": ["political", "regional", "racism", "stereotype"],
            "harassment": ["aggressive trolling", "targeted"]
        },
        "suspension": {
            "severe": ["family", "staff disrespect", "repeated harassment"]
        },
        "expulsion": {
            "critical": ["targeting", "hate speech", "slur", "nsfw", "raid", "doxx", "threat", "impersonation"]
        }
    }

    # Points for each category
    POINTS = {
        "advisory": 0,  # Starts at 0, increases with warnings
        "notice": 1,
        "warning": 2,
        "penalty": 3,
        "suspension": 4,
        "expulsion": 5
    }

    # Durations for different point levels
    DURATIONS = {
        0: timedelta(minutes=5),    # Advisory second warning
        1: timedelta(minutes=15),   # Notice/Third advisory
        2: timedelta(minutes=40),   # Warning
        3: timedelta(hours=2),      # Penalty
        4: timedelta(hours=6),      # Suspension
        5: timedelta(hours=24)      # Expulsion
    }

    # MP Thresholds
    MP_THRESHOLDS = {
        5: timedelta(days=1),       # 5 MP → 1-day mute
        8: timedelta(days=3),       # 8 MP → 3-day mute
        10: timedelta(days=7),      # 10 MP → 7-day mute
        15: None                    # 15 MP → Permanent mute/ban
    }

    @classmethod
    def get_offense_category(cls, reason: str) -> Optional[str]:
        """Get the category for a given reason."""
        reason_lower = reason.lower()
        for category, subcategories in cls.OFFENSE_CATEGORIES.items():
            for _, keywords in subcategories.items():
                if any(keyword in reason_lower for keyword in keywords):
                    return category
        return None

    @classmethod
    def get_points(cls, reason: str, warning_count: int = 0) -> int:
        """Get points for an offense, considering warning count for advisory."""
        category = cls.get_offense_category(reason)
        if not category:
            return 0

        if category == "advisory":
            if warning_count == 0:
                return 0  # First warning
            elif warning_count == 1:
                return 0  # Second warning (5 min mute)
            else:
                return 1  # Third warning converts to 1 MP
        
        return cls.POINTS.get(category, 0)

    @classmethod
    def get_duration(cls, total_points: int, warning_count: int = 0) -> Optional[timedelta]:
        """Get mute duration based on total points and warning count."""
        # Check for permanent mute threshold
        if total_points >= 15:
            return None

        # Check MP thresholds
        for threshold, duration in sorted(cls.MP_THRESHOLDS.items()):
            if total_points >= threshold:
                return duration

        # Handle advisory warnings
        if total_points == 0 and warning_count == 1:
            return timedelta(minutes=5)  # Second warning

        # Regular durations
        return cls.DURATIONS.get(total_points, timedelta(minutes=5))

    @classmethod
    def format_duration(cls, duration: Optional[timedelta]) -> str:
        """Format duration into a human-readable string."""
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
