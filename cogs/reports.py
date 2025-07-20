import discord
from discord.ext import commands
import asyncio


class ReportSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_initialized = False
    
    async def cog_load(self):
        """Called when the cog is loaded"""
        if not self.db_initialized:
            await init_database()
            self.db_initialized = True
    
    async def cog_unload(self):
        await close_database()

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.emoji.name == '🆘':
            return
        
