from datetime import timedelta
from typing import Optional

class MutePointSystem:
    OFFENSES = {
        1: ['spam', 'unnecessary', 'flooding'],
        2: ['toxic', 'passive aggressive', 'baiting'],
        3: ['repeated', 'drama', 'filter bypass'],
        4: ['harassment', 'personal attack'],
        5: ['hate speech', 'slur', 'nsfw'],
        6: ['trolling', 'disruption'],
        7: ['extreme disrespect', 'targeting staff'],
        8: ['multiple offenses', 'serious violation'],
        9: ['final warning', 'major offense'],
        10: ['raid', 'doxx', 'threat', 'impersonation']
    }

    DURATIONS = {
        1: timedelta(minutes=20),
        2: timedelta(hours=1),
        3: timedelta(hours=3),
        4: timedelta(hours=6),
        5: timedelta(hours=12),
        6: timedelta(days=1),
        7: timedelta(days=2),
        8: timedelta(days=3),
        9: timedelta(days=5),
        10: None  # Ban vote
    }

    @classmethod
    def get_points(cls, reason: str) -> int:
        reason = reason.lower()
        for points in sorted(cls.OFFENSES.keys(), reverse=True):
            for keyword in cls.OFFENSES[points]:
                if keyword in reason:
                    return points
        return 1  # default if nothing matches

    @classmethod
    def get_duration(cls, total_points: int) -> Optional[timedelta]:
        if total_points >= 10:
            return None
        return cls.DURATIONS.get(total_points, timedelta())

    @classmethod
    def format_duration(cls, duration: Optional[timedelta]) -> str:
        if duration is None:
            return "Ban Vote Triggered"
        minutes = duration.total_seconds() / 60
        if minutes >= 60:
            hours = minutes / 60
            return f"{hours:.1f} hours"
        return f"{int(minutes)} minutes"
