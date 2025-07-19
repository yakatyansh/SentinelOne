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
        # Check if it's the SOS emoji (🆘)
        if str(payload.emoji) != '🆘':
            print(f"[DEBUG] Ignoring emoji: {payload.emoji}")
            return

        print(f"[DEBUG] SOS reaction detected by user {payload.user_id}")

        # Get guild
        guild = self.bot.get_guild(payload.guild_id)
        user = guild.get_member(payload.user_id)
        channel = guild.get_channel(payload.channel_id)
        try:
            message = await channel.fetch_message(payload.message_id)
        except discord.NotFound:
            return
        except discord.Forbidden:
            return

        # Don't allow reporting your own messages
        if message.author.id == user.id:
            try:
                await user.send("❌ You cannot report your own messages.")
            except discord.Forbidden:
                pass
            return

        try:
            await user.send(
                f"🚨 **Report System**\n"
                f"You are reporting a message from **{message.author.display_name}** in **#{channel.name}**.\n\n"
                f"**Message content:**\n"
                f">>> {message.content[:1000] if message.content else '*[No text content]*'}\n\n"
                f"**Please reply with your reason for reporting this message.**\n"
                f"*You have 60 seconds to respond.*"
            )


            def check(m):
                return (
                    m.author.id == user.id and 
                    isinstance(m.channel, discord.DMChannel) and 
                    len(m.content.strip()) > 0  # Ensure they actually typed something
                )

            try:
                response = await self.bot.wait_for('message', check=check, timeout=60.0)
                print(f"[DEBUG] Received response: {response.content[:50]}...")

                # Send to log channel
                log_channel_id = 1395499760676376577  # Replace with your actual log channel ID
                log_channel = guild.get_channel(log_channel_id)
                
                if log_channel:
                    embed = discord.Embed(
                        title="🚨 Message Reported",
                        color=discord.Color.red(),
                        timestamp=discord.utils.utcnow()
                    )
                    embed.add_field(name="Reported by", value=f"{user.mention} ({user.id})", inline=True)
                    embed.add_field(name="Message author", value=f"{message.author.mention} ({message.author.id})", inline=True)
                    embed.add_field(name="Channel", value=f"{channel.mention}", inline=True)
                    embed.add_field(name="Message content", value=message.content[:1024] if message.content else "*[No text content]*", inline=False)
                    embed.add_field(name="Report reason", value=response.content[:1024], inline=False)
                    embed.add_field(name="Message link", value=f"[Jump to message]({message.jump_url})", inline=False)

                    await log_channel.send(embed=embed)

                # Send confirmation
                await user.send("✅ **Thank you for your report!**\nOur moderation team will review it shortly.")

            except asyncio.TimeoutError:
                await user.send("⏰ **Report timed out.**\nYou took too long to respond. Please try again if needed.")

        except discord.Forbidden:
            # User has DMs disabled
            try:
                await channel.send(
                    f"{user.mention}, I cannot send you a direct message. "
                    f"Please enable DMs from server members to use the report feature.",
                    delete_after=10
                )
                print(f"[DEBUG] User {user.display_name} has DMs disabled.")
            except discord.Forbidden:
                print(f"[DEBUG] Cannot send message in channel {channel.name}")

        except Exception as e:
            print(f"[ERROR] Unexpected error in report system: {e}")
            try:
                await user.send("❌ **An error occurred while processing your report.**\nPlease contact a moderator directly.")
            except:
                pass


# Load the cog
async def setup(bot):
    await bot.add_cog(ReportSystem(bot))

# If running this file directly
if __name__ == "__main__":
    # Add your bot token here
    # bot.run('YOUR_BOT_TOKEN')
    pass