from discord.ext import commands
import discord
from utils.db import insert_punishment
from datetime import datetime
import traceback

class Punishments(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def punish(self, ctx, member: discord.Member, points: int, *, reason: str):
        time = datetime.now().isoformat()

        total_points = 0
        try:
            total_points = await insert_punishment(ctx.guild.id, member.id, ctx.author.id, reason, time, points)
        except Exception as e:
            traceback.print_exc()
            await ctx.send(f"❌ Failed to update punishment database for {member.mention}.")
            return  

        try:
            await member.send(
                f"You have been punished in **{ctx.guild.name}** for **{reason}**.\n"
                f"Points added: **{points}**\n"
                f"Total MP: **{total_points}**"
            )
        except discord.Forbidden:
            await ctx.send(
                f"⚠️ Could not send DM to {member.mention} — they may have DMs off."
            )

        await ctx.send(
            f"✅ {member.mention} has been punished with **{points} MP**. Total: **{total_points} MP**."
        )

async def setup(bot):
    await bot.add_cog(Punishments(bot))
