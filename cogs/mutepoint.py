import discord
from datetime import datetime, timedelta
from typing import Optional, Tuple

class MutePointSystem:
    """
    Handles mute point classification and duration calculation
    Based on the Mute Point Framework (MPF) with progressive punishment system
    """
    
    # Mute point categories with keywords and point values
    OFFENSE_CATEGORIES = {
        1: {
            'keywords': ['spam', 'unnecessary', 'flooding', 'repeated messages', 'minor spam', 'low effort'],
            'description': 'Minor spam or unnecessary messages',
            'duration': timedelta(minutes=20)
        },
        2: {
            'keywords': ['toxic', 'passive aggressive', 'rude', 'baiting', 'mild toxicity', 'sarcastic', 'condescending'],
            'description': 'Light toxicity, passive-aggressive behavior, mild baiting',
            'duration': timedelta(hours=1)
        },
        3: {
            'keywords': ['repeated', 'filter bypass', 'drama', 'rule breaking', 'continuing', 'ignoring rules', 'circumvent'],
            'description': 'Repeated rule-breaking, drama baiting, filter bypass',
            'duration': timedelta(hours=3)
        },
        4: {
            'keywords': ['harassment', 'personal attack', 'disrespect', 'targeting', 'bullying', 'mean', 'cruel'],
            'description': 'Harassment, personal attacks, targeted disrespect',
            'duration': timedelta(hours=6)
        },
        5: {
            'keywords': ['hate speech', 'slur', 'nsfw', 'inappropriate content', 'offensive', 'sexual', 'explicit'],
            'description': 'Hate speech, slurs, NSFW content in public areas',
            'duration': timedelta(hours=12)
        },
        6: {
            'keywords': ['trolling', 'disruption', 'aggressive', 'major disruption', 'chaos', 'intentional'],
            'description': 'Aggressive trolling, major disruptions',
            'duration': timedelta(days=1)
        },
        7: {
            'keywords': ['extreme', 'staff', 'ignoring warnings', 'severe disrespect', 'mod abuse', 'authority'],
            'description': 'Extreme disrespect, targeting staff, ignoring warnings',
            'duration': timedelta(days=2)
        },
        8: {
            'keywords': ['multiple offenses', 'serious violation', 'escalated', 'pattern', 'habitual'],
            'description': 'Multiple past offenses + serious new violation',
            'duration': timedelta(days=3)
        },
        9: {
            'keywords': ['final warning', 'major offense', 'last chance', 'severe', 'extreme violation'],
            'description': 'Final major offense before ban territory',
            'duration': timedelta(days=5)
        },
        10: {
            'keywords': ['raid', 'doxx', 'threat', 'impersonation', 'ban worthy', 'violence', 'illegal', 'criminal'],
            'description': 'Raiding, doxxing, threats, impersonation → Instant Ban Vote',
            'duration': None  # Ban vote triggered
        }
    }
    
    @classmethod
    def classify_offense(cls, reason: str) -> int:
        """
        Classify offense reason and return mute points
        
        Args:
            reason (str): The reason provided for the offense
            
        Returns:
            int: Number of mute points (1-10)
        """
        reason_lower = reason.lower().strip()
        
        # Check each category for keyword matches (starting from highest severity)
        for points in reversed(range(1, 11)):  # Check 10, 9, 8... down to 1
            category = cls.OFFENSE_CATEGORIES.get(points)
            if category:
                for keyword in category['keywords']:
                    if keyword in reason_lower:
                        return points
        
        # Default to 2 points if no specific category is found
        return 2
    
    @classmethod
    def get_mute_duration(cls, total_points: int) -> Optional[timedelta]:
        """
        Get mute duration based on total mute points
        
        Args:
            total_points (int): Total accumulated mute points
            
        Returns:
            Optional[timedelta]: Duration to mute, None if ban vote should be triggered
        """
        if total_points >= 10:
            return None  # Ban vote triggered
        elif total_points in cls.OFFENSE_CATEGORIES:
            return cls.OFFENSE_CATEGORIES[total_points]['duration']
        else:
            # Fallback calculation for edge cases
            if total_points <= 0:
                return timedelta(minutes=20)
            return timedelta(minutes=20 * min(total_points, 9))
    
    @classmethod
    def get_category_info(cls, points: int) -> dict:
        """
        Get information about a specific offense category
        
        Args:
            points (int): Mute points value
            
        Returns:
            dict: Category information or empty dict if not found
        """
        return cls.OFFENSE_CATEGORIES.get(points, {})
    
    @classmethod
    def format_duration(cls, duration: Optional[timedelta]) -> str:
        """
        Format duration into human-readable string
        
        Args:
            duration: Timedelta object or None
            
        Returns:
            str: Formatted duration string
        """
        if duration is None:
            return "Ban Vote Triggered"
        
        if duration.days > 0:
            return f"{duration.days} day{'s' if duration.days != 1 else ''}"
        
        hours = duration.total_seconds() / 3600
        if hours >= 1:
            return f"{hours:.1f} hour{'s' if hours != 1 else ''}"
        
        minutes = duration.total_seconds() / 60
        return f"{int(minutes)} minute{'s' if minutes != 1 else ''}"
    
    @classmethod
    def get_all_categories_formatted(cls) -> str:
        """
        Get all offense categories formatted for display
        
        Returns:
            str: Formatted string of all categories
        """
        categories_text = ""
        for points, info in cls.OFFENSE_CATEGORIES.items():
            duration_text = cls.format_duration(info['duration'])
            categories_text += f"**{points} MP** - {info['description']} → {duration_text}\n"
        return categories_text
    
    @classmethod
    def suggest_keywords(cls, points: int) -> str:
        """
        Get keyword suggestions for a specific point value
        
        Args:
            points (int): Mute points value
            
        Returns:
            str: Comma-separated keywords
        """
        category = cls.get_category_info(points)
        if category and 'keywords' in category:
            return ", ".join(category['keywords'][:5])  # Show first 5 keywords
        return "No keywords available"

class MutePointHelper:
    """
    Helper class for common mute point operations
    """
    
    @staticmethod
    async def apply_mute_role(guild: discord.Guild, member: discord.Member, reason: str = "Auto-mute via MPF") -> Tuple[bool, str]:
        """
        Apply mute role to a member
        
        Args:
            guild: Discord guild
            member: Member to mute
            reason: Reason for mute
            
        Returns:
            Tuple[bool, str]: (Success, Status message)
        """
        try:
            # Look for mute role (common names)
            mute_role = (
                discord.utils.get(guild.roles, name="Muted") or 
                discord.utils.get(guild.roles, name="Mute") or 
                discord.utils.get(guild.roles, name="Timeout") or
                discord.utils.get(guild.roles, name="Silenced")
            )
            
            if not mute_role:
                return False, "⚠️ **Mute role not configured**"
            
            if mute_role in member.roles:
                return True, "🔇 **Already muted**"
            
            await member.add_roles(mute_role, reason=reason)
            return True, "🔇 **Successfully muted**"
            
        except discord.Forbidden:
            return False, "⚠️ **No permission to mute**"
        except Exception as e:
            return False, f"❌ **Mute failed: {str(e)}**"
    
    @staticmethod
    async def remove_mute_role(guild: discord.Guild, member: discord.Member, reason: str = "Auto-unmute via MPF") -> Tuple[bool, str]:
        """
        Remove mute role from a member
        
        Args:
            guild: Discord guild
            member: Member to unmute
            reason: Reason for unmute
            
        Returns:
            Tuple[bool, str]: (Success, Status message)
        """
        try:
            mute_role = (
                discord.utils.get(guild.roles, name="·˚ YELLOW CARD")
            )
    
            if not mute_role:
                return False, "⚠️ **Mute role not configured**"
            
            if mute_role not in member.roles:
                return True, "🔊 **Not currently muted**"
            
            await member.remove_roles(mute_role, reason=reason)
            return True, "🔊 **Successfully unmuted**"
            
        except discord.Forbidden:
            return False, "⚠️ **No permission to unmute**"
        except Exception as e:
            return False, f"❌ **Unmute failed: {str(e)}**"
    
    @staticmethod
    def create_punishment_embed(
        reporter: discord.Member,
        reported_member: discord.Member, 
        channel: discord.TextChannel,
        message: discord.Message,
        reason: str,
        mute_points: int,
        total_points: int,
        action_taken: str
    ) -> discord.Embed:
        """
        Create a formatted embed for punishment logging
        
        Returns:
            discord.Embed: Formatted punishment embed
        """
        embed = discord.Embed(
            title="🚨 Message Reported & Processed",
            color=discord.Color.red() if total_points >= 10 else discord.Color.orange(),
            timestamp=discord.utils.utcnow()
        )
        
        embed.add_field(name="Reported by", value=f"{reporter.mention} ({reporter.id})", inline=True)
        embed.add_field(name="Message author", value=f"{reported_member.mention} ({reported_member.id})", inline=True)
        embed.add_field(name="Channel", value=f"{channel.mention}", inline=True)
        
        message_content = message.content[:1024] if message.content else "*[No text content]*"
        if len(message.attachments) > 0:
            message_content += f"\n*[{len(message.attachments)} attachment(s)]*"
        
        embed.add_field(name="Message content", value=message_content, inline=False)
        embed.add_field(name="Report reason", value=reason[:1024], inline=False)
        embed.add_field(name="Mute Points Added", value=f"**{mute_points} MP**", inline=True)
        embed.add_field(name="Total Mute Points", value=f"**{total_points} MP**", inline=True)
        embed.add_field(name="Action Taken", value=action_taken, inline=True)
        embed.add_field(name="Message link", value=f"[Jump to message]({message.jump_url})", inline=False)
        
        return embed

# Example usage and testing functions
if __name__ == "__main__":
    # Test the classification system
    test_reasons = [
        "This user is spamming the chat",
        "Harassment and personal attacks against me",
        "They used hate speech and slurs",
        "Raiding our server with bots",
        "Being toxic and rude to everyone"
    ]
    
    print("=== Mute Point System Test ===")
    for reason in test_reasons:
        points = MutePointSystem.classify_offense(reason)
        duration = MutePointSystem.get_mute_duration(points)
        duration_text = MutePointSystem.format_duration(duration)
        print(f"Reason: '{reason}' → {points} MP → {duration_text}")
    
    print(f"\n=== All Categories ===")
    print(MutePointSystem.get_all_categories_formatted())