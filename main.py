import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
if not TOKEN:
    raise ValueError("No DISCORD_BOT_TOKEN found in environment variables.")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.reactions = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event 
async def on_ready():
    print(f'Logged in as {bot.user.name} (ID: {bot.user.id})')
    print('------')

initial_extensions = ['cogs.punishments','cogs.reports']  

for ext in initial_extensions:
    try:
        bot.load_extension(ext)
        print(f'Loaded extension: {ext}')
    except Exception as e:
        print(f'Failed to load extension {ext}.', file=sys.stderr)
        print(e)

bot.run(TOKEN)          