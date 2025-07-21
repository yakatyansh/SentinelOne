import discord
from discord.ext import commands
from utils import db  

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.reactions = True

bot = commands.Bot(command_prefix="!", intents=intents)

class Points(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @bot.command(name="getpoints")
    async def getpoints(self, ctx, member: discord.Member):
        """Get the total mute points for a member."""
        points = db.get_points(ctx.guild.id, member.id)
        await ctx.send(f"{member.mention} has a total of **{total_points} MP**.")

    @bot.command(name="clearpoints")
    async def clearpoints(self, ctx, member: discord.Member):
        """Clear all mute points for a member."""
        db.clear_points(ctx.guild.id, member.id)
        await ctx.send(f"✅ All mute points for {member.mention} have been cleared.")

async def setup(bot):
    await bot.add_cog(Points(bot))
