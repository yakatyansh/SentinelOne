import discord
from discord.ext import commands
import asyncio
from datetime import datetime
from utils.db import (
    insert_punishment,
    get_guild_settings,
    update_guild_setting,
    get_user_punishments,
    get_user_total_points,
    get_database_info,
    get_recent_punishments,
    get_top_offenders,
    init_database,
    close_database
)
from .mutepoint import MutePointSystem, MutePointHelper  

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

class ReportSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_initialized = False
    
    async def cog_load(self):
        """Called when the cog is loaded"""
        if not self.db_initialized:
            await init_database()
            self.db_initialized = True
    
    async def cog_unload(self):
        """Called when the cog is unloaded"""
        await close_database()

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        # Check if it's the SOS emoji (🆘)
        if str(payload.emoji) != '🆘':
            print(f"[DEBUG] Ignoring emoji: {payload.emoji}")
            return

        print(f"[DEBUG] SOS reaction detected by user {payload.user_id}")

        # Get guild
        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            print("[DEBUG] Guild not found.")
            return

        # Get user who reacted
        user = guild.get_member(payload.user_id)
        if not user or user.bot:
            print(f"[DEBUG] User is bot or not found. User: {user}")
            return

        # Get channel
        channel = guild.get_channel(payload.channel_id)
        if not channel:
            print("[DEBUG] Channel not found.")
            return

        # Get message
        try:
            message = await channel.fetch_message(payload.message_id)
            print(f"[DEBUG] Found message: {message.content[:50]}...")
        except discord.NotFound:
            print("[DEBUG] Message not found.")
            return
        except discord.Forbidden:
            print("[DEBUG] No permission to fetch message.")
            return

        # Don't allow reporting your own messages
        if message.author.id == user.id:
            try:
                await user.send("❌ You cannot report your own messages.")
            except discord.Forbidden:
                pass
            return

        try:
            # Create DM channel and send prompt with offense categories
            categories_text = MutePointSystem.get_all_categories_formatted()
            
            await user.send(
                f"🚨 **Report System - Mute Point Framework**\n"
                f"You are reporting a message from **{message.author.display_name}** in **#{channel.name}**.\n\n"
                f"**Message content:**\n"
                f">>> {message.content[:800] if message.content else '*[No text content]*'}\n\n"
                f"**Offense Categories:**\n{categories_text}\n\n"
                f"**Please reply with your reason for reporting this message.**\n"
                f"*Include keywords that match the offense type for accurate point assignment.*\n"
                f"*You have 90 seconds to respond.*"
            )

            print(f"[DEBUG] DM sent to {user.display_name}. Waiting for response...")

            # Wait for DM response
            def check(m):
                return (
                    m.author.id == user.id and 
                    isinstance(m.channel, discord.DMChannel) and 
                    len(m.content.strip()) > 0
                )

            try:
                response = await self.bot.wait_for('message', check=check, timeout=90.0)
                reason = response.content.strip()
                print(f"[DEBUG] Received response: {reason[:50]}...")

                # Classify the offense and get mute points using our imported system
                mute_points = MutePointSystem.classify_offense(reason)
                print(f"[DEBUG] Classified as {mute_points} MP offense")

                # Insert punishment into database and get total points
                time = datetime.now().isoformat()
                try:
                    total_points = await insert_punishment(
                        guild.id, 
                        message.author.id, 
                        user.id,  # Reporter as moderator
                        reason, 
                        time, 
                        mute_points
                    )
                    print(f"[DEBUG] Total points for user: {total_points}")
                except Exception as e:
                    print(f"[ERROR] Database error: {e}")
                    await user.send("❌ **Database error occurred.**\nPlease contact a moderator directly.")
                    return
                
                mute_duration = MutePointSystem.get_mute_duration(total_points)
                
                if total_points >= 10:
                    punishment_action = "🔴 **BAN VOTE TRIGGERED**"
                    await self.notify_staff_ban_vote(guild, message.author, total_points, reason)
                else:
                    success, status_msg = await MutePointHelper.apply_mute_role(
                        guild, 
                        message.author, 
                        f"Auto-mute via report system: {reason[:100]}"
                    )
                    duration_text = MutePointSystem.format_duration(mute_duration)
                    punishment_action = f"{status_msg} for {duration_text}"

                log_channel_id = 771072621595983893  
                log_channel = guild.get_channel(log_channel_id)
                
                if log_channel:
                    embed = MutePointHelper.create_punishment_embed(
                        reporter=user,
                        reported_member=message.author,
                        channel=channel,
                        message=message,
                        reason=reason,
                        mute_points=mute_points,
                        total_points=total_points,
                        action_taken=punishment_action
                    )
                    
                    await log_channel.send(embed=embed)
                    print("[DEBUG] Report successfully logged with embed.")
                else:
                    print(f"[ERROR] Log channel with ID {log_channel_id} not found.")

                try:
                    if total_points >= 10:
                        await message.author.send(
                            f"🔴 **SERIOUS VIOLATION DETECTED**\n"
                            f"You have been reported in **{guild.name}** for **{reason}**.\n"
                            f"Mute Points added: **{mute_points} MP**\n"
                            f"Total MP: **{total_points} MP**\n\n"
                            f"**A ban vote has been triggered by staff.**\n"
                            f"Please wait for staff decision."
                        )
                    else:
                        duration_text = MutePointSystem.format_duration(mute_duration)
                        await message.author.send(
                            f"⚠️ **You have been muted in {guild.name}**\n"
                            f"Reason: **{reason}**\n"
                            f"Mute Points added: **{mute_points} MP**\n"
                            f"Total MP: **{total_points} MP**\n"
                            f"Mute Duration: **{duration_text}**\n\n"
                            f"Please review the server rules and improve your behavior."
                        )
                except discord.Forbidden:
                    pass

                await user.send(
                    f"✅ **Report Processed Successfully!**\n"
                    f"**{message.author.display_name}** has been assigned **{mute_points} MP** (Total: **{total_points} MP**).\n"
                    f"Action taken: {punishment_action}\n\n"
                    f"Thank you for helping maintain our community standards!"
                )
                print(f"[DEBUG] Report completed for {user.display_name}")

            except asyncio.TimeoutError:
                await user.send("⏰ **Report timed out.**\nYou took too long to respond. Please try again if needed.")
                print(f"[DEBUG] Report timed out for {user.display_name}")

        except discord.Forbidden:
            try:
                await channel.send(
                    f"{user.mention}, I cannot send you a direct message. "
                    f"Please enable DMs from server members to use the report feature.",
                    delete_after=10
                )
                print(f"[DEBUG] User {user.display_name} has DMs disabled.")
            except discord.Forbidden:
                print(f"[DEBUG] Cannot send message in channel {channel.name}")

        except Exception as e:
            print(f"[ERROR] Unexpected error in report system: {e}")
            try:
                await user.send("❌ **An error occurred while processing your report.**\nPlease contact a moderator directly.")
            except:
                pass

    async def notify_staff_ban_vote(self, guild, member, total_points, reason):
        """Notify staff about ban vote trigger"""
        # Find staff channel (you might want to configure this)
        staff_channels = ['staff', 'mod-chat', 'moderators', 'admin']
        staff_channel = None
        
        for channel_name in staff_channels:
            staff_channel = discord.utils.get(guild.channels, name=channel_name)
            if staff_channel:
                break
        
        if staff_channel:
            embed = discord.Embed(
                title="🔴 BAN VOTE TRIGGERED",
                description=f"{member.mention} has reached **{total_points} MP**",
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow()
            )
            embed.add_field(name="Latest Offense", value=reason, inline=False)
            embed.add_field(name="Action Required", value="Staff vote required for ban decision", inline=False)
            
            await staff_channel.send("@here", embed=embed)

    @commands.command(name="test_report")
    @commands.has_permissions(administrator=True)
    async def test_report(self, ctx):
        await ctx.send("✅ Enhanced Report System with MPF is active! React with 🆘 to any message to test it.")

    @commands.command(name="mpf_info")
    async def mpf_info(self, ctx):
        """Display Mute Point Framework information"""
        embed = discord.Embed(
            title="🚨 Mute Point Framework (MPF)",
            description="Our automated moderation system",
            color=discord.Color.blue()
        )
        
        categories_text = MutePointSystem.get_all_categories_formatted()
        embed.add_field(name="Offense Categories & Punishments", value=categories_text, inline=False)
        embed.add_field(
            name="How it works", 
            value="React with 🆘 to report messages. The system automatically assigns mute points based on your reason and applies appropriate punishments.", 
            inline=False
        )
        
        await ctx.send(embed=embed)

    @commands.group(name="config")
    @commands.has_permissions(administrator=True)
    async def config(self, ctx):
        """Configuration commands for the report system"""
        if ctx.invoked_subcommand is None:
            await ctx.send("Please specify a configuration subcommand. Use `!help config` for more info.")

    @config.command(name="setlogchannel")
    @commands.has_permissions(administrator=True)
    async def set_log_channel(self, ctx, channel: discord.TextChannel):
        """Set the channel for report logs"""
        try:
            await update_guild_setting(ctx.guild.id, "mod_log_channel", channel.id)
            await ctx.send(f"✅ Report logs will now be sent to {channel.mention}")
        except Exception as e:
            await ctx.send(f"❌ Error setting log channel: {str(e)}")

    @config.command(name="setmuterole")
    @commands.has_permissions(administrator=True)
    async def set_mute_role(self, ctx, role: discord.Role):
        """Set the mute role for the server"""
        try:
            await update_guild_setting(ctx.guild.id, "mute_role_id", role.id)
            await ctx.send(f"✅ Mute role set to {role.mention}")
        except Exception as e:
            await ctx.send(f"❌ Error setting mute role: {str(e)}")

    @commands.command(name="stats")
    @commands.has_permissions(manage_messages=True)
    async def report_stats(self, ctx, user: discord.Member = None):
        """Show report statistics for the server or a specific user"""
        try:
            if user:
                punishments = await get_user_punishments(ctx.guild.id, user.id)
                total_points = await get_user_total_points(ctx.guild.id, user.id)
                
                embed = discord.Embed(
                    title=f"📊 Report Statistics for {user.display_name}",
                    color=discord.Color.blue()
                )
                
                embed.add_field(name="Total Points", value=total_points, inline=False)
                embed.add_field(name="Total Reports", value=len(punishments), inline=True)
                
                if punishments:
                    recent_reports = "\n".join([
                        f"• {p['reason'][:50]}... ({p['points']} MP)" 
                        for p in punishments[:3]
                    ])
                    embed.add_field(
                        name="Recent Reports",
                        value=recent_reports or "None",
                        inline=False
                    )
            else:
                info = await get_database_info()
                recent = await get_recent_punishments(ctx.guild.id, 24)
                top_offenders = await get_top_offenders(ctx.guild.id, 5)
                
                embed = discord.Embed(
                    title=f"📊 Report Statistics for {ctx.guild.name}",
                    color=discord.Color.blue()
                )
                
                embed.add_field(name="Total Reports", value=info['total_punishments'], inline=True)
                embed.add_field(name="Last 24 Hours", value=len(recent), inline=True)
                
                if top_offenders:
                    top_users = "\n".join([
                        f"• <@{stats['user_id']}>: {stats['total_points']} MP" 
                        for stats in top_offenders
                    ])
                    embed.add_field(
                        name="Top Offenders",
                        value=top_users or "None",
                        inline=False
                    )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ Error retrieving stats: {str(e)}")

# Remove the standalone bot commands and just keep the setup function
async def setup(bot):
    await bot.add_cog(ReportSystem(bot))