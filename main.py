import sys
import discord
from discord.ext import commands
import os
import asyncio
from dotenv import load_dotenv
from aiohttp import web   # NEW: to run a dummy server

load_dotenv()
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
if not TOKEN:
    raise ValueError("No DISCORD_BOT_TOKEN found in environment variables.")

# intents
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

# Dummy web server to keep Render happy
async def handle(request):
    return web.Response(text="Bot is running!")

async def web_server():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", int(os.getenv("PORT", 8080)))
    await site.start()

async def main():
    await load_extensions()
    await asyncio.gather(
        bot.start(TOKEN),
        web_server()   # run bot + server together
    )

asyncio.run(main())
