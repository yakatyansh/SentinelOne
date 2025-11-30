import discord
from discord.ext import commands




class Games(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        @commands.command(name="xmas")
        async def xmas(self, ctx):
            """Send a Merry Xmas message"""
            embed = discord.Embed(
                title="🎄 Merry Christmas!",
                description=(
                    f"Happy holidays, {ctx.author.mention}!\n\n"
                    "Wishing you joy, peace, and plenty of good vibes this season. "
                    "Stay safe and enjoy the holidays! 🎁✨"
                ),
                color=discord.Color.red(),
                timestamp=ctx.message.created_at
            )
            embed.set_footer(text="From Markaroni and Team")
            try:
                await ctx.send(embed=embed)
                await ctx.message.add_reaction("🎄")
            except Exception:
                # Ignore send/react errors (e.g., missing permissions)
                pass


            