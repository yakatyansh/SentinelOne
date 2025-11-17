from datetime import datetime, timedelta
from asyncio import sleep
import discord
from discord.ext import commands
from utils import db
from utils.mutepoint import MutePointSystem


class Punishments(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def log_punishment(self, ctx, target_user, reason, mp_given, duration):
        log_channel_id = 1406574258573803661  
        log_channel = ctx.guild.get_channel(log_channel_id)
        if log_channel:
            embed = discord.Embed(
                title="🔨 Punishment Issued",
                color=discord.Color.orange(),
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="Punished User", value=target_user.mention, inline=True)
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Mute Points Given", value=str(mp_given), inline=True)
            embed.add_field(name="Timeout Duration", value=MutePointSystem.format_duration(duration) if duration else "N/A", inline=True)
            await log_channel.send(embed=embed)

    async def trigger_ban_vote(self, ctx, member):
        mod_channel_id = 771072621595983893  
        mod_channel = ctx.guild.get_channel(mod_channel_id)
        mod_roles_ping = "@୧ : ASSISTANT REFREE ᐟ⋆ @୧ :REFEREE ᐟ⋆ @୧ : CLUB DIRECTOR ᐟ⋆"

        if mod_channel:
            embed = discord.Embed(
                title="🚨 Ban Vote Triggered",
                description=f"{mod_roles_ping}\n{member.mention} has reached **15 MP**. Vote to ban this user.",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            message = await mod_channel.send(embed=embed)
            await message.add_reaction("✅")  # Yes
            await message.add_reaction("❌")  # No

            def check(reaction, user):
                return (
                    reaction.message.id == message.id
                    and str(reaction.emoji) in ["✅", "❌"]
                    and not user.bot
                )

            await sleep(120)  # Wait for 2 minutes
            message = await mod_channel.fetch_message(message.id)

            yes_votes = sum(1 for r in message.reactions if str(r.emoji) == "✅" for _ in await r.users().flatten() if not _.bot)
            no_votes = sum(1 for r in message.reactions if str(r.emoji) == "❌" for _ in await r.users().flatten() if not _.bot)

            if yes_votes > no_votes:
                try:
                    await member.ban(reason="Reached 15 Mute Points - Voted Ban")
                    await mod_channel.send(f"🔨 {member.mention} has been **banned** following a successful vote.")
                except discord.Forbidden:
                    await mod_channel.send(f"❌ Failed to ban {member.mention}. Please check permissions.")
            else:
                await mod_channel.send(f"✅ {member.mention} has been **spared**. Vote did not pass.")

    async def remove_yellow_card_after_timeout(self, member: discord.Member, duration: int):
            
            await sleep(duration)
            guild = member.guild
            member = guild.get_member(member.id)
            if not member:
                return

            yellow_card_role = discord.utils.get(guild.roles, name="ﾒ YELLOW CARD ᵎᵎ")
            if yellow_card_role and yellow_card_role in member.roles:
                await member.remove_roles(yellow_card_role, reason="Timeout duration expired")


    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def punish(self, ctx, member: discord.Member, *, reason):
        """Punish a user based on the offense reason."""
        if member.id == ctx.author.id:
            await ctx.send("❌ You cannot punish yourself.")
            return

        total_points = await db.check_expired_points(ctx.guild.id, member.id)
        
        valid_reasons = list(MutePointSystem.POINTS.keys())
        reason = reason.lower().strip()

        if reason not in valid_reasons:
            await ctx.send(f"❌ Invalid reason. Use one of: {', '.join(valid_reasons)}.")
            return

        if reason == "advisory":
            warning_count = await db.get_warning_count(ctx.guild.id, member.id)
            warning_count, should_mute = await db.add_warning(ctx.guild.id, member.id, ctx.author.id, reason)
            
            if warning_count == 1:
                await ctx.send(f"⚠️ **Warning #{warning_count}** issued to {member.mention}")
                duration = None
            elif warning_count == 2:
                duration = MutePointSystem.DURATIONS[0]  
                try:
                    await member.timeout(duration, reason="Second advisory warning")
                    await ctx.send(f"⏳ {member.mention} has been muted for **5 minutes** (Warning #{warning_count})")
                    yellow_card_role = discord.utils.get(ctx.guild.roles, name="ﾒ YELLOW CARD ᵎᵎ")
                    if yellow_card_role:
                        await member.add_roles(yellow_card_role, reason="Mute issued by bot (advisory warning)")
                        self.bot.loop.create_task(
                            self.remove_yellow_card_after_timeout(
                                member, 
                                int(duration.total_seconds())
                            )
                        )
                except discord.Forbidden:
                    await ctx.send("❌ I don't have permission to mute this user.")
            else:  
                points = 1  
                total_points = await db.add_punishment(ctx.guild.id, member.id, "advisory_conversion", points)
                duration = MutePointSystem.DURATIONS[1]  # 15 minutes
                yellow_card_role = discord.utils.get(ctx.guild.roles, name="ﾒ YELLOW CARD ᵎᵎ")
                if yellow_card_role:
                    await member.add_roles(yellow_card_role, reason="Mute issued by bot (advisory conversion)")
                    self.bot.loop.create_task(
                        self.remove_yellow_card_after_timeout(
                            member, 
                            int(duration.total_seconds())
                        )
                    )
                await member.timeout(duration, reason="Third advisory warning converted to MP")
                await ctx.send(f"⚠️ {member.mention} has received **1 MP** after 3 warnings")
                await db.clear_warnings(ctx.guild.id, member.id)
            
            await self.log_punishment(ctx, member, f"Advisory Warning #{warning_count}", 0, duration)
            return

        # Handle regular punishments
        points = MutePointSystem.POINTS[reason]
        total_points = await db.add_punishment(ctx.guild.id, member.id, reason, points)
        
        # Check MP thresholds first
        if total_points >= 15:
            await ctx.send(f"🚨 **Ban vote triggered for {member.mention}** (15 MP reached).")
            await self.trigger_ban_vote(ctx, member)
            return
        elif total_points >= 10:
            duration = MutePointSystem.MP_THRESHOLDS[10]  # 7-day mute
        elif total_points >= 8:
            duration = MutePointSystem.MP_THRESHOLDS[8]   # 3-day mute
        elif total_points >= 5:
            duration = MutePointSystem.MP_THRESHOLDS[5]   # 1-day mute
        else:
            duration = MutePointSystem.DURATIONS[points]  # Base duration for offense

        yellow_card_role = discord.utils.get(ctx.guild.roles, name="ﾒ YELLOW CARD ᵎᵎ")

        try:
            await member.timeout(duration, reason=f"Punished for: {reason}")
            await ctx.send(f"⏳ {member.mention} has been muted for **{MutePointSystem.format_duration(duration)}**.")

            if yellow_card_role:
                await member.add_roles(yellow_card_role, reason="Mute issued by bot")
                self.bot.loop.create_task(
                    self.remove_yellow_card_after_timeout(
                        member, 
                        int(duration.total_seconds())
                    )
                )
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to mute or assign roles to this user.")
        except Exception as e:
            await ctx.send(f"⚠️ Failed to mute or assign role: {e}")

        # Send DM
        try:
            await member.send(
                f"You have been punished in **{ctx.guild.name}** for **{reason}**.\n"
                f"Points added: **{points} MP**\n"
                f"Total mute points: **{total_points} MP**\n"
                f"Mute duration: **{MutePointSystem.format_duration(duration)}**"
            )
        except:
            await ctx.send(f"⚠️ Could not send DM to {member.mention}.")

        # Log the punishment
        await self.log_punishment(ctx, member, reason, points, duration)

    @commands.command(name="release")
    @commands.has_permissions(manage_messages=True)
    async def release(self, ctx, member: discord.Member):
        """Release a user from timeout and remove the 'Yellow Card' role."""
        yellow_card_role = discord.utils.get(ctx.guild.roles, name="ﾒ YELLOW CARD ᵎᵎ")

        try:
            await member.timeout(None, reason="Manual unmute by moderator.")
            await ctx.send(f"🔓 {member.mention} has been released (unmuted).")

            if yellow_card_role in member.roles:
                await member.remove_roles(yellow_card_role, reason="User unmuted")
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to unmute or modify roles.")
        except Exception as e:
            await ctx.send(f"⚠️ Failed to unmute or remove role: {e}")

        # Send DM
        try:
            await member.send(
                f"You have been unmuted in **{ctx.guild.name}** by a moderator."
            )
        except:
            await ctx.send(f"⚠️ Could not send DM to {member.mention}.")

    @staticmethod
    def _parse_duration(s: str):
        """Parse duration strings like '1d', '2h30m', '45m', '90s', '1:30' (hh:mm) -> timedelta or None."""
        import re
        from datetime import timedelta

        if not s:
            return None
        s = s.strip().lower()
        # plain number -> seconds
        if s.isdigit():
            return timedelta(seconds=int(s))
        # combined format: 1d2h30m10s
        m = re.fullmatch(r'(?:(\d+)d)?(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?', s)
        if m and any(m.groups()):
            days = int(m.group(1) or 0)
            hours = int(m.group(2) or 0)
            minutes = int(m.group(3) or 0)
            seconds = int(m.group(4) or 0)
            if days + hours + minutes + seconds == 0:
                return None
            return timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)
        # colon format: hh:mm or mm:ss or hh:mm:ss
        if ':' in s:
            parts = s.split(':')
            try:
                if len(parts) == 2:
                    h = int(parts[0]); m_ = int(parts[1])
                    # interpret as hh:mm if hours < 24 else as mm:ss - we'll treat as hh:mm
                    return timedelta(hours=h, minutes=m_)
                if len(parts) == 3:
                    return timedelta(hours=int(parts[0]), minutes=int(parts[1]), seconds=int(parts[2]))
            except:
                return None
        return None

    @commands.command(name="sybau")
    @commands.has_permissions(manage_messages=True)
    async def mute(self, ctx, member: discord.Member, duration: str, *, reason: str = "Muted by staff"):
        """Temporarily mute a member for a custom duration.
        Duration examples: 1d, 2h30m, 45m, 90s, 1:30 (hh:mm). This command does NOT add MP.
        """

        td = self._parse_duration(duration)
        if not td or td.total_seconds() <= 0:
            await ctx.send("❌ Invalid duration. Examples: `1d`, `2h30m`, `45m`, `90s`, `1:30`.")
            return

        yellow_card_role = discord.utils.get(ctx.guild.roles, name="ﾒ YELLOW CARD ᵎᵎ")
        try:
            await member.timeout(td, reason=reason)
            # add yellow card role if exists
            if yellow_card_role:
                try:
                    await member.add_roles(yellow_card_role, reason="Mute issued by bot")
                except discord.Forbidden:
                    # continue even if role assign fails
                    pass

                # schedule removal task using existing helper
                self.bot.loop.create_task(
                    self.remove_yellow_card_after_timeout(
                        member,
                        int(td.total_seconds())
                    )
                )

            await ctx.send(f"⏳ {member.mention} has been muted for **{MutePointSystem.format_duration(td)}**. Reason: {reason}")
            # log, mp_given = 0 because this is a manual mute
            await self.log_punishment(ctx, member, reason, 0, td)
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to mute this user.")
        except Exception as e:
            await ctx.send(f"⚠️ Failed to mute: {e}")

async def setup(bot):
    await bot.add_cog(Punishments(bot))
