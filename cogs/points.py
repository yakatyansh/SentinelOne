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
        total_points = db.get_points(ctx.guild.id, member.id)
        await ctx.send(f"{member.mention} has a total of **{total_points} MP**.")

    @bot.command(name="clearpoints")
    async def clearpoints(self, ctx, member: discord.Member):
        """Clear all mute points for a member."""
        db.clear_points(ctx.guild.id, member.id)
        await ctx.send(f"✅ All mute points for {member.mention} have been cleared.")

    @bot.command(name="sentinelhelp")    
    async def help(self, ctx):
        """Display help information for the points system."""
        embed = discord.Embed(
            title="SentinelOne Points System Help",
            description="Here are the commands available for managing mute points:",
            color=discord.Color.blue()
        )
        embed.add_field(name="!getpoints <member>", value="Get total mute points for a member.", inline=False)
        embed.add_field(name="!clearpoints <member>", value="Clear all mute points for a member.", inline=False)
        embed.add_field(name="!sentinelhelp", value="Display this help message.", inline=False)
        embed.add_field(name="!punish <member> <reason>", value="Punish a member and add mute points.", inline=False)
        embed.add_field(name="!release <member>", value="Release a member from their punishment.", inline=False)
        embed.add_field(name="Report", value="React with 🆘 to any message to report it.", inline=False)
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Points(bot))
