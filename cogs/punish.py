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
        if points == 0:
            await ctx.send("❌ Invalid reason. Please use a valid one like `spam`, `toxicity`, etc.")
            return
        
        total_points = db.add_punishment(ctx.guild.id, member.id, reason, points)

        try:
            await member.send(
                f"You have been punished in **{ctx.guild.name}** for **{reason}**.\n"
                f"Points added: **{points} MP**\n"
                f"Total mute points: **{total_points} MP**"
            )
        except:
            await ctx.send(f"⚠️ Could not send DM to {member.mention}.")

        await ctx.send(f"✅ {member.mention} has been punished for **{reason}** with **{points} MP**. Total: **{total_points} MP**.")




async def setup(bot):
    await bot.add_cog(Punishments(bot))
