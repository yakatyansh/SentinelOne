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

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def punish(self, ctx, member: discord.Member, *, reason):
        points = MutePointSystem.get_points(reason)
        total_points = db.add_punishment(ctx.guild.id, member.id, reason, points)
        duration = MutePointSystem.DURATIONS.get(points)

        yellow_card_role = discord.utils.get(ctx.guild.roles, name="·˚ YELLOW CARD")

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
