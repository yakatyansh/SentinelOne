import discord
from discord.ext import commands


class Punishments(commands.Cog):
    def __init__(self,bot):
        self.bot = bot

        @commands.command()
        @commands.has_permissions(manage_messages=True)
        async def punish(self, ctx, member: discord.Member, points: int, *, reason ):
            total_points = db.add_punishments()
            try:
                await member.send(
                    "you have been punished in {ctx.guild.name} for {reason}. "
                    "points added: {points}"
                    "You have a total of {total_points} points."
                )
            except:
                await ctx.send(
                    f"Failed to send DM to {member.mention}. "
                    "Please ensure they have DMs enabled."
                )
            await ctx.send(f"✅ {member.mention} has been punished with {points} MP. Total: {total_points} MP.")    

async def setup(bot):
    await bot.add_cog(Punishments(bot))
