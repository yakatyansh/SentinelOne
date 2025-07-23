from datetime import datetime, timedelta
import discord
from discord.ext import commands
from utils import db
from utils.mutepoint import MutePointSystem


intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.reactions = True

bot = commands.Bot(command_prefix="!", intents=intents)

class Punishments(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

   

    async def log_punishment(self, ctx, target_user, reason, mp_given, duration):
        log_channel_id = 771065948764372996
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
        mod_channel_id =  771072621595983893
        mod_channel = ctx.guild.get_channel(mod_channel_id)
        mod_roles_ping = "@୧ : ASSISTANT REFREE ᐟ⋆ @୧ :REFEREE ᐟ⋆ @୧ : CLUB DIRECTOR ᐟ⋆"  

        if mod_channel:
            embed = discord.Embed(
                title="🚨 Ban Vote Triggered",
                description=f"{mod_roles_ping}\n{member.mention} has reached **10 MP**. Vote to ban this user.",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            message = await mod_channel.send(embed=embed)
            await message.add_reaction("✅")  # Tick
            await message.add_reaction("❌")  # Cross

            def check(reaction, user):
                return (
                    reaction.message.id == message.id
                    and str(reaction.emoji) in ["\u2705", "\u274c"]
                    and not user.bot
                )

            await discord.utils.sleep_until(datetime.utcnow() + timedelta(seconds=120))
            message = await mod_channel.fetch_message(message.id)

            ticks = sum(1 for r in message.reactions if str(r.emoji) == "✅" for _ in await r.users().flatten() if not _.bot)
            crosses = sum(1 for r in message.reactions if str(r.emoji) == "❌" for _ in await r.users().flatten() if not _.bot)

            if ticks > crosses:
                try:
                    await member.ban(reason="Reached 10 Mute Points - Voted Ban")
                    await mod_channel.send(f"🔨 {member.mention} has been **banned** following a successful vote.")
                except:
                    await mod_channel.send(f"❌ Failed to ban {member.mention}. Please check permissions.")
            else:
                await mod_channel.send(f"✅ {member.mention} has been **spared**. Vote did not pass.")
        

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def punish(self, ctx, member: discord.Member, *, reason):
        points = MutePointSystem.get_points(reason)
        total_points = db.add_punishment(ctx.guild.id, member.id, reason, points)
        duration = MutePointSystem.DURATIONS.get(points)

        yellow_card_role = discord.utils.get(ctx.guild.roles, name="ﾒ YELLOW CARD ᵎᵎ")

        if duration:
            try:
                await member.timeout(duration, reason=f"Punished for: {reason}")
                await ctx.send(f"⏳ {member.mention} has been muted for **{MutePointSystem.format_duration(duration)}**.")

                if yellow_card_role:
                    await member.add_roles(yellow_card_role, reason="Mute issued by bot")
                else:
                    await ctx.send("⚠️ Could not find the 'Yellow Card' role. Please make sure it exists.")
            except discord.Forbidden:
                await ctx.send("❌ I don't have permission to mute or assign roles to this user.")
            except Exception as e:
                await ctx.send(f"⚠️ Failed to mute or assign role: {e}")
        else:
            await ctx.send(f"🚨 **Ban vote triggered for {member.mention}** (10 MP reached).")
            await self.trigger_ban_vote(ctx, member)

        # Send DM
        try:
            await member.send(
                f"You have been punished in **{ctx.guild.name}** for **{reason}**.\n"
                f"Points added: **{points} MP**\n"
                f"Total mute points: **{total_points} MP**"
            )
        except:
            await ctx.send(f"⚠️ Could not send DM to {member.mention}.")
        await ctx.send(f"✅ {member.mention} punished for **{reason}**. Added **{points} MP**. Total: **{total_points} MP**.")
        await self.log_punishment(ctx, member, reason, points, duration)

    @commands.command(name="release")
    @commands.has_permissions(manage_messages=True)
    async def release(self, ctx, member: discord.Member):
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

async def setup(bot):
    await bot.add_cog(Punishments(bot))
