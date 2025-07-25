from datetime import timedelta
from typing import Optional

class MutePointSystem:
    OFFENSES = {
        1: ['Light spam', 'Mild trolling', 'Using caps unnecessarily', 'Off-topic messages'],
        2: ['Repeated spam', 'Ignoring staff pings', 'Mini-modding', 'Borderline toxic language'],
        3: ['Excessive trolling', 'Minor toxicity', 'Arguing with staff', 'Spam pings', 'Baiting drama'],
        4: ['Swearing at members', 'Harassment warnings', 'Disturbing messages', 'Repeated disruption'],
        5: ['Light hate speech', 'Mass ping (once)', 'Evading mutes', 'NSFW language'],
        6: ['Offensive memes', 'Provoking fights', 'Toxic DMs to members', 'Ignoring multiple warnings'],
        7: ['Targeted harassment', 'Repeated bigotry', 'Serious raid baiting', 'Impersonation'],
        8: ['Consistent toxic behavior', 'Use of hate symbols', 'NSFW content', 'Threatening tone in arguments'],
        9: ['Staff disrespect', 'Malicious intent', 'Spamming harmful links', 'Calling for raids'],
        10: ['Severe/ongoing disruption', 'Zero improvement', 'Server risk', 'Ban vote triggered']
    }

    DURATIONS = {
        0: timedelta(minutes=5),
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
        return 0  # default if nothing matches

    @classmethod
    def get_duration(cls, total_points: int) -> Optional[timedelta]:
        if total_points >= 10:
            return None
        return cls.DURATIONS.get(total_points, timedelta(minutes=20))

    @classmethod
    def format_duration(cls, duration: Optional[timedelta]) -> str:
        if duration is None:
            return "Ban Vote Triggered"
        minutes = duration.total_seconds() / 60
        if minutes >= 60:
            hours = minutes / 60
            return f"{hours:.1f} hours"
        return f"{int(minutes)} minutes"
