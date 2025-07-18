import discord
from discord.ext import commands
import asyncio

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

class ReportSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    
    async def on_raw_reaction_add(self, payload):
        if payload.emoji.name == '🆘':
            print(f"Reaction added by {payload.user_id} in guild {payload.guild_id} on message {payload.message_id}")

        

            guild = self.bot.get_guild(payload.guild_id)
            if not guild:
                return
            
            channel = guild.get_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)
            user = guild.get_member(payload.user_id)

            if user.bot:
                return
            
            try :
                dm = await user.create_dm()
                prompt = await dm.send(
                    f"You reported a message from **{message.author}** in **#{channel}**.\n"
                    f"Content: \"{message.content}\"\n\n"
                    f"Please reply with the reason for reporting this message. You have 60 seconds."
                )
                def check(m):
                    return m.author == user and m.channel == dm and m.reference is None
                
                response = await self.bot.wait_for('message', check=check, timeout=60.0)
                await prompt.delete()
                await response.delete() 

                log_channel = guild.get_channel(1395499760676376577)
                if log_channel:
                     log_channel.send(
                        f"🚨 **Report Received**\n"
                        f"**Reported By:** {user.mention}\n"
                        f"**Message By:** {message.author.mention}\n"
                        f"**Channel:** {channel.mention}\n"
                        f"**Content:** {message.content}\n"
                        f"**Reason:** {response.content}"
                    )
                
            except asyncio.TimeoutError:
                await dm.send("You took too long to respond. Report cancelled.")
            except discord.Forbidden:
                await channel.send(
                    f"{user.mention}, I cannot send you a direct message. Please enable DMs from server members to use the report feature."
                )
async def setup(bot):
    await bot.add_cog(ReportSystem(bot))
            
