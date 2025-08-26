import discord
from discord.ext import commands
from utils import db
from utils.mutepoint import MutePointSystem, OffenseLevel
from datetime import datetime, timedelta

class Points(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="points")
    @commands.has_permissions(manage_messages=True)
    async def points(self, ctx, member: discord.Member):
        """Get detailed points and warnings information for a member"""
        # Check for expired points first
        total_points = await db.check_expired_points(ctx.guild.id, member.id)
        user_info = await db.get_user_info(ctx.guild.id, member.id)
        warnings = await db.get_warning_count(ctx.guild.id, member.id)
        
        embed = discord.Embed(
            title=f"Points Info for {member.display_name}",
            color=discord.Color.blue(),
            timestamp=ctx.message.created_at
        )

        # Add warnings information with next action
        next_action = "warning"
        if warnings == 1:
            next_action = "5min mute"
        elif warnings == 2:
            next_action = "1 MP (15min mute)"

        embed.add_field(
            name="⚪ Advisory Warnings",
            value=(
                f"Current warnings: **{warnings}/3**\n"
                f"Next warning results in: **{next_action}**"
            ),
            inline=False
        )

        # Add MP information
        total_points = user_info.get("total_points", 0) if user_info else 0
        embed.add_field(
            name="📊 Mute Points",
            value=(
                f"Current MP: **{total_points}**\n"
                f"{self._get_threshold_info(total_points)}"
            ),
            inline=False
        )

        # Add recent punishments
        if user_info and user_info.get('punishments'):
            recent_punishments = user_info['punishments'][-3:]  # Get last 3
            punishment_list = []
            for p in recent_punishments:
                points = p.get('points', 0)
                if points > 0:
                    timestamp = int(p['timestamp'].timestamp())
                    punishment_list.append(
                        f"• {p['reason']} ({points} MP) - <t:{timestamp}:R>"
                    )
                else:
                    timestamp = int(p['timestamp'].timestamp())
                    punishment_list.append(
                        f"• Advisory Warning - <t:{timestamp}:R>"
                    )
            
            embed.add_field(
                name="📝 Recent Actions",
                value="\n".join(punishment_list) or "None",
                inline=False
            )

        if user_info and user_info.get('punishments'):
            recent_punishments = user_info['punishments'][-3:]
            punishment_list = []
            for p in recent_punishments:
                timestamp = p['timestamp']
                expiry_date = timestamp + timedelta(days=20)
                remaining_days = (expiry_date - datetime.utcnow()).days
                
                if remaining_days > 0:
                    punishment_list.append(
                        f"• {p['reason']} ({p['points']} MP) - Expires in {remaining_days} days"
                    )
            
            if punishment_list:
                embed.add_field(
                    name="📝 Active Punishments",
                    value="\n".join(punishment_list),
                    inline=False
                )

        await ctx.send(embed=embed)

    def _get_threshold_info(self, points: int) -> str:
        """Get information about MP thresholds"""
        if points >= 15:
            return "⛔ Account has reached permanent mute threshold"
        
        thresholds = {
            5: "1-day mute",
            8: "3-day mute",
            10: "7-day mute",
            15: "Permanent mute"
        }
        
        next_threshold = min((t for t in thresholds.keys() if t > points), default=None)
        if next_threshold:
            return f"Next threshold: **{next_threshold} MP** ({thresholds[next_threshold]})"
        return "Maximum threshold reached"

    @commands.command(name="clearpoints")
    @commands.has_permissions(manage_messages=True)
    async def clearpoints(self, ctx, member: discord.Member):
        """Clear all points and warnings for a member"""
        confirm_msg = await ctx.send(
            f"⚠️ Are you sure you want to clear all points and warnings for {member.mention}?\n"
            "React with ✅ to confirm."
        )
        await confirm_msg.add_reaction("✅")

        try:
            def check(reaction, user):
                return (user == ctx.author and 
                       str(reaction.emoji) == "✅" and 
                       reaction.message.id == confirm_msg.id)

            await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
            
            # Fix: Add await to database operations
            await db.clear_points(ctx.guild.id, member.id)
            await db.clear_warnings(ctx.guild.id, member.id)
            await ctx.send(f"✅ All points and warnings cleared for {member.mention}")

        except TimeoutError:
            await ctx.send("❌ Command timed out. No changes were made.")
        except Exception as e:
            await ctx.send(f"❌ Error clearing points: {str(e)}")

    @commands.command(name="senti")
    @commands.has_permissions(manage_messages=True)
    async def help(self, ctx):
        """Display help information for the points system"""
        embed = discord.Embed(
            title="SentinelOne Points System Help",
            description="Mute Point Framework (MPF) Commands:",
            color=discord.Color.blue()
        )

        # Update command sections with new durations
        mod_commands = [
            ("!punish @user advisory", "Warning system (3 warnings = 1 MP)"),
            ("!punish @user notice", "1 MP → 15min mute"),
            ("!punish @user warning", "2 MP → 40min mute"),
            ("!punish @user penalty", "3 MP → 2hr mute"),
            ("!punish @user suspension", "4 MP → 6hr mute"),
            ("!punish @user expulsion", "5 MP → 24hr mute")
        ]

        warning_info = [
            "• First warning: Warning only",
            "• Second warning: 5min mute",
            "• Third warning: Converts to 1 MP (15min mute)"
        ]

        embed.add_field(
            name="⚠️ Advisory Warning System",
            value="\n".join(warning_info),
            inline=False
        )

        embed.add_field(
            name="🛡️ Moderation Commands",
            value="\n".join(f"`{cmd}` • {desc}" for cmd, desc in mod_commands),
            inline=False
        )

        utility_commands = [
            ("!points @user", "Check warnings and MP"),
            ("!clearpoints @user", "Clear all warnings and MP"),
            ("!release @user", "Remove active mute"),
            ("Report", "React 🆘 to report message")
        ]

        embed.add_field(
            name="🔧 Utility Commands",
            value="\n".join(f"`{cmd}` • {desc}" for cmd, desc in utility_commands),
            inline=False
        )

        embed.add_field(
            name="⚖️ MP Thresholds",
            value=(
                "• 5 MP → 1-day mute\n"
                "• 8 MP → 3-day mute\n"
                "• 10 MP → 7-day mute\n"
                "• 15 MP → Permanent mute"
            ),
            inline=False
        )

        await ctx.send(embed=embed)

    @commands.command(name="expires")
    @commands.has_permissions(manage_messages=True)
    async def expires(self, ctx, member: discord.Member):
        """View when points will expire for a user"""
        user_info = await db.get_user_info(ctx.guild.id, member.id)
        
        if not user_info or not user_info.get('punishments'):
            await ctx.send(f"{member.mention} has no active punishments.")
            return

        embed = discord.Embed(
            title=f"Point Expiration for {member.display_name}",
            color=discord.Color.blue(),
            timestamp=ctx.message.created_at
        )

        active_punishments = []
        for p in user_info['punishments']:
            timestamp = p['timestamp']
            expiry_date = timestamp + timedelta(days=20)
            remaining_days = (expiry_date - datetime.utcnow()).days
            
            if remaining_days > 0:
                active_punishments.append(
                    f"• {p['reason']} ({p['points']} MP) - Expires <t:{int(expiry_date.timestamp())}:R>"
                )

        if active_punishments:
            embed.description = "\n".join(active_punishments)
        else:
            embed.description = "No active punishments."

        await ctx.send(embed=embed)
        
async def setup(bot):
    await bot.add_cog(Points(bot))
