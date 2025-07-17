import discord
from discord.ext import commands
import asyncio


class ReportSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.emoji.name == '🆘':
            return
        
