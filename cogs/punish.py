from discord.ext import commands
import discord
from utils import  db  # Update import to use mongo.py
from datetime import datetime
import traceback
from .mutepoint import MutePointSystem, MutePointHelper
from utils.db import clear_user_points
import asyncio  # Add this for TimeoutError handling

class Punishments(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.users_collection = db.Users  # Access collection directly
        
    async def update_user_points(self, guild_id: int, user_id: int, points: int, reason: str, mod_id: int) -> int:
        """Update user's punishment points in MongoDB"""
        timestamp = datetime.utcnow()
        
        punishment_doc = {
            "guild_id": guild_id,
            "user_id": user_id,
            "mod_id": mod_id,
            "reason": reason,
            "points": points,
            "timestamp": timestamp
        }
        
        # Insert the new punishment
        await self.users_collection.insert_one(punishment_doc)
        
        # Calculate total points
        pipeline = [
            {
                "$match": {
                    "guild_id": guild_id,
                    "user_id": user_id
                }
            },
            {
                "$group": {
                    "_id": None,
                    "total_points": {"$sum": "$points"}
                }
            }
        ]
        
        result = await self.users_collection.aggregate(pipeline).to_list(1)
        return result[0]["total_points"] if result else points

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def punish(self, ctx, member: discord.Member, points: int, *, reason: str):
        """
        Manual punishment command for moderators
        Usage: !punish @user <points> <reason>
        """
        if points < 1 or points > 10:
            await ctx.send("❌ Mute points must be between 1 and 10.")
            return
            
        time = datetime.now().isoformat()

        total_points = 0
        try:
            # Update to use new MongoDB function
            total_points = await self.update_user_points(
                ctx.guild.id,
                member.id,
                points,
                reason,
                ctx.author.id
            )
        except Exception as e:
            traceback.print_exc()
            await ctx.send(f"❌ Failed to update punishment database for {member.mention}.")
            return

        # Apply automatic punishment based on total points using our MPF system
        mute_duration = MutePointSystem.get_mute_duration(total_points)
        
        if total_points >= 10:
            punishment_action = "🔴 **BAN VOTE TRIGGERED**"
            # Notify staff for ban vote
            await self.notify_staff_ban_vote(ctx, member, total_points, reason)
        else:
            # Apply mute using our helper
            success, status_msg = await MutePointHelper.apply_mute_role(
                ctx.guild, 
                member, 
                f"Manual punishment: {reason[:100]}"
            )
            duration_text = MutePointSystem.format_duration(mute_duration)
            punishment_action = f"{status_msg} for {duration_text}"

        # Send DM to punished user
        try:
            if total_points >= 10:
                await member.send(
                    f"🔴 **SERIOUS VIOLATION - BAN VOTE TRIGGERED**\n"
                    f"You have been punished in **{ctx.guild.name}** for **{reason}**.\n"
                    f"Points added: **{points} MP**\n"
                    f"Total MP: **{total_points} MP**\n\n"
                    f"**A ban vote has been triggered by staff.**\n"
                    f"Please wait for staff decision."
                )
            else:
                duration_text = MutePointSystem.format_duration(mute_duration)
                await member.send(
                    f"⚠️ **You have been punished in {ctx.guild.name}**\n"
                    f"Reason: **{reason}**\n"
                    f"Points added: **{points} MP**\n"
                    f"Total MP: **{total_points} MP**\n"
                    f"Punishment: **{duration_text} mute**\n\n"
                    f"Please review the server rules and improve your behavior."
                )
        except discord.Forbidden:
            await ctx.send(
                f"⚠️ Could not send DM to {member.mention} — they may have DMs off."
            )

        # Send confirmation to moderator
        await ctx.send(
            f"✅ {member.mention} has been punished with **{points} MP**. Total: **{total_points} MP**.\n"
            f"Action: {punishment_action}"
        )

    async def notify_staff_ban_vote(self, ctx, member, total_points, reason):
        """Notify staff about ban vote trigger"""
        embed = discord.Embed(
            title="🔴 BAN VOTE TRIGGERED",
            description=f"{member.mention} has reached **{total_points} MP**",
            color=discord.Color.red(),
            timestamp=discord.utils.utcnow()
        )
        embed.add_field(name="Punished by", value=ctx.author.mention, inline=True)
        embed.add_field(name="Latest Offense", value=reason, inline=False)
        embed.add_field(name="Action Required", value="Staff vote required for ban decision", inline=False)
        
        await ctx.send(embed=embed)

    @commands.command(name="mpf_classify")
    @commands.has_permissions(manage_messages=True)
    async def classify_reason(self, ctx, *, reason: str):
        """
        Test the MPF classification system with a reason
        Usage: !mpf_classify <reason>
        """
        points = MutePointSystem.classify_offense(reason)
        category_info = MutePointSystem.get_category_info(points)
        duration = MutePointSystem.get_mute_duration(points)
        duration_text = MutePointSystem.format_duration(duration)
        
        embed = discord.Embed(
            title="🔍 MPF Classification Test",
            description=f"**Reason:** {reason}",
            color=discord.Color.blue(),
            timestamp=discord.utils.utcnow()
        )
        embed.add_field(name="Classified Points", value=f"**{points} MP**", inline=True)
        embed.add_field(name="Category", value=category_info['name'], inline=True)
        embed.add_field(name="Severity", value=category_info['severity'], inline=True)
        embed.add_field(name="Mute Duration", value=duration_text, inline=True)
        embed.add_field(name="Description", value=category_info['description'], inline=False)
        
        await ctx.send(embed=embed)

    @commands.command(name="mpf_info")
    @commands.has_permissions(manage_messages=True)
    async def mpf_system_info(self, ctx):
        """
        Display information about the Mute Point Framework system
        Usage: !mpf_info
        """
        embed = discord.Embed(
            title="🛡️ Mute Point Framework (MPF) System",
            description="Automated punishment classification and progressive discipline system",
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow()
        )
        
        # Add category information
        categories = [
            ("1 MP", "Minor offense", "5 min mute"),
            ("2 MP", "Light offense", "15 min mute"), 
            ("3 MP", "Moderate offense", "1 hour mute"),
            ("4 MP", "Serious offense", "6 hour mute"),
            ("5 MP", "Major offense", "1 day mute"),
            ("6-9 MP", "Severe offense", "3-7 days mute"),
            ("10+ MP", "Critical offense", "Ban vote triggered")
        ]
        
        category_text = "\n".join([f"**{cat[0]}:** {cat[1]} → {cat[2]}" for cat in categories])
        embed.add_field(name="Point Categories", value=category_text, inline=False)
        
        embed.add_field(
            name="How it works", 
            value="• Offenses are automatically classified by keywords\n"
                  "• Points accumulate over time\n"
                  "• Mute duration increases with total points\n"
                  "• Ban vote at 10+ total points", 
            inline=False
        )
        
        embed.add_field(
            name="Commands",
            value="• `!punish @user <points> <reason>` - Manual punishment\n"
                  "• `!mpf_classify <reason>` - Test classification\n"
                  "• `!mpf_info` - Show this information",
            inline=False
        )
        
        await ctx.send(embed=embed)

    @commands.command(name="check_points", aliases=["points", "mp"])
    @commands.has_permissions(manage_messages=True)
    async def check_user_points(self, ctx, member: discord.Member = None):
        """
        Check a user's current mute points
        Usage: !check_points [@user]
        """
        if member is None:
            member = ctx.author
            
        try:
            # Query MongoDB for user's points
            pipeline = [
                {
                    "$match": {
                        "guild_id": ctx.guild.id,
                        "user_id": member.id
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "total_points": {"$sum": "$points"}
                    }
                }
            ]
            
            result = await self.users_collection.aggregate(pipeline).to_list(1)
            total_points = result[0]["total_points"] if result else 0
            
            mute_duration = MutePointSystem.get_mute_duration(total_points)
            duration_text = MutePointSystem.format_duration(mute_duration)
            category_info = MutePointSystem.get_category_info(total_points) if total_points > 0 else None
            
            embed = discord.Embed(
                title=f"📊 Mute Points for {member.display_name}",
                color=discord.Color.orange() if total_points >= 5 else discord.Color.green(),
                timestamp=discord.utils.utcnow()
            )
            
            embed.add_field(name="Total Points", value=f"**{total_points} MP**", inline=True)
            
            if total_points >= 10:
                embed.add_field(name="Status", value="🔴 **BAN VOTE ELIGIBLE**", inline=True)
            elif total_points > 0:
                embed.add_field(name="Next Mute Duration", value=duration_text, inline=True)
                embed.add_field(name="Current Category", value=category_info['name'], inline=True)
            else:
                embed.add_field(name="Status", value="✅ **CLEAN RECORD**", inline=True)
                
            await ctx.send(embed=embed)
            
        except Exception as e:
            traceback.print_exc()
            await ctx.send(f"❌ Failed to retrieve points for {member.mention}.")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def clearpoints(self, ctx, member: discord.Member = None):
        """
        Clear mute points for a user or the entire server
        Usage: !clearpoints [@user] - If no user is specified, clears points for entire server
        """
        try:
            if member:
                count = await db.clear_user_points(ctx.guild.id, member.id)
                await ctx.send(f"✅ Cleared {count} punishment records for {member.mention}")
            else:
                # Ask for confirmation before clearing all points
                confirm_msg = await ctx.send("⚠️ Are you sure you want to clear ALL mute points for the entire server? React with ✅ to confirm.")
                await confirm_msg.add_reaction("✅")
                
                try:
                    def check(reaction, user):
                        return user == ctx.author and str(reaction.emoji) == "✅" and reaction.message.id == confirm_msg.id
                    
                    await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
                    
                    count = await clear_user_points(ctx.guild.id)
                    await ctx.send(f"✅ Cleared {count} punishment records for the entire server")
                
                except asyncio.TimeoutError:
                    await ctx.send("❌ Confirmation timed out. No points were cleared.")
                    
        except Exception as e:
            await ctx.send(f"❌ Error clearing points: {str(e)}")
            traceback.print_exc()

    @punish.error
    async def punish_error(self, ctx, error):
        """Handle errors for the punish command"""
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ You don't have permission to use this command.")
        elif isinstance(error, commands.MemberNotFound):
            await ctx.send("❌ Member not found. Please mention a valid user.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("❌ Invalid arguments. Usage: `!punish @user <points> <reason>`")
        else:
            await ctx.send("❌ An error occurred while processing the punishment.")
            traceback.print_exc()

# Setup function for the bot
async def setup(bot):
    await bot.add_cog(Punishments(bot))