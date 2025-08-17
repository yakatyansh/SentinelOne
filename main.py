import sys
import discord
from discord.ext import commands
import os
import asyncio
from dotenv import load_dotenv
from keepalive import keep_alive

load_dotenv()
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
if not TOKEN:
    raise ValueError("No DISCORD_BOT_TOKEN found in environment variables.")

keep_alive()


intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.reactions = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'✅ Logged in as {bot.user.name} (ID: {bot.user.id})')
    print('------')

async def load_extensions():
    initial_extensions = ['cogs.punish','cogs.points','cogs.reports']
    for ext in initial_extensions:
        try:
            await bot.load_extension(ext)
            print(f'🔧 Loaded extension: {ext}')
        except Exception as e:
            print(f'❌ Failed to load extension {ext}', file=sys.stderr)
            print(e)

async def main():
    await load_extensions()
    await asyncio.gather(
        bot.start(TOKEN),
    )

asyncio.run(main())
