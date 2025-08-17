import discord
from discord.ext import commands
from utils import db
from utils.mutepoint import MutePointSystem, OffenseLevel

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.reactions = True

bot = commands.Bot(command_prefix="!", intents=intents)

class Points(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="points")
    @commands.has_permissions(manage_messages=True)
    async def points(self, ctx, member: discord.Member):
        """Get detailed points and warnings information for a member"""
        user_info = db.get_user_info(ctx.guild.id, member.id)
        warnings = db.get_warning_count(ctx.guild.id, member.id)
        total_points = db.get_points(ctx.guild.id, member.id)

        embed = discord.Embed(
            title=f"Points Info for {member.display_name}",
            color=discord.Color.blue(),
            timestamp=ctx.message.created_at
        )

        # Add warnings information
        embed.add_field(
            name="⚪ Advisory Warnings",
            value=f"{warnings}/3 warnings\n" + 
                  f"Next warning will result in: {'5min mute' if warnings == 1 else '1 MP' if warnings == 2 else 'warning'}", 
            inline=False
        )

        # Add MP information
        embed.add_field(
            name="📊 Mute Points",
            value=f"Current MP: **{total_points}**\n" +
                  self._get_threshold_info(total_points),
            inline=False
        )

        if user_info and user_info.get('punishments'):
            recent_punishments = user_info['punishments'][-3:]  # Get last 3 punishments
            punishment_list = "\n".join(
                f"• {p['reason']} ({p['points']} MP) - <t:{int(p['timestamp'].timestamp())}:R>"
                for p in recent_punishments
            )
            embed.add_field(
                name="📝 Recent Punishments",
                value=punishment_list or "None",
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
    @commands.has_permissions(administrator=True)
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
            
            db.clear_points(ctx.guild.id, member.id)
            db.clear_warnings(ctx.guild.id, member.id)
            await ctx.send(f"✅ All points and warnings cleared for {member.mention}")

        except TimeoutError:
            await ctx.send("❌ Command timed out. No changes were made.")

    @commands.command(name="senti")
    async def help(self, ctx):
        """Display help information for the points system"""
        embed = discord.Embed(
            title="SentinelOne Points System Help",
            description="Mute Point Framework (MPF) Commands:",
            color=discord.Color.blue()
        )

        # Command sections
        mod_commands = [
            ("!punish @user advisory", "Give advisory warning (3 warnings = 1 MP)"),
            ("!punish @user notice", "1 MP - 15min mute"),
            ("!punish @user warning", "2 MP - 40min mute"),
            ("!punish @user penalty", "3 MP - 2hr mute"),
            ("!punish @user suspension", "4 MP - 6hr mute"),
            ("!punish @user expulsion", "5 MP - 24hr mute")
        ]

        utility_commands = [
            ("!points @user", "Check user's warnings and MP"),
            ("!clearpoints @user", "Clear user's warnings and MP"),
            ("!release @user", "Remove user's current mute"),
            ("Report", "React with 🆘 to report a message")
        ]

        # Add command sections to embed
        embed.add_field(
            name="🛡️ Moderation Commands",
            value="\n".join(f"`{cmd}` • {desc}" for cmd, desc in mod_commands),
            inline=False
        )

        embed.add_field(
            name="🔧 Utility Commands",
            value="\n".join(f"`{cmd}` • {desc}" for cmd, desc in utility_commands),
            inline=False
        )

        # Add MP thresholds
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

async def setup(bot):
    await bot.add_cog(Points(bot))
