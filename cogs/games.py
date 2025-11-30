import discord
from discord.ext import commands
from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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
            pass

    @commands.command(name="roast")
    async def roast(self, ctx, member: discord.Member = None):
        """Roast the command author or a mentioned member using ChatGPT"""
        target = member if member else ctx.author
        
        roles = [role.name for role in target.roles if role.name != "@everyone"]
        roles_str = ", ".join(roles) if roles else "no roles"
        
        prompt = (
            f"Write a funny, lighthearted roast (2-3 sentences max) for a Discord user with these roles: {roles_str}. "
            f"The roast should be playful and not mean-spirited. Keep it under 150 characters."
        )
        
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100,
                temperature=0.7
            )
            roast_text = response.choices[0].message.content.strip()
            
            embed = discord.Embed(
                title="🔥 Roast Alert",
                description=f"{target.mention}\n\n{roast_text}",
                color=discord.Color.orange(),
                timestamp=ctx.message.created_at
            )
            embed.set_footer(text="Roasted by Collina")
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ Error generating roast: {str(e)}")


async def setup(bot):
    await bot.add_cog(Games(bot))