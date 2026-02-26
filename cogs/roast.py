import discord
from discord.ext import commands
import random

class Roast(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        # Football clubs with their roasts
        self.roasts = {
            "manchester united": [
                "Manchester United: Where spending billions equals finishing nowhere 💀",
                "United's trophy case is gathering dust faster than their transfer spending grows 🏆❌",
                "They managed to turn Old Trafford into a museum of past glories 👻",
                "Manchester United proves money can't buy joy... or wins 😭",
                "Even their manager can't explain their tactics 🤔",
                "United's recent form: a masterclass in disappointment 📉",
            ],
            "manchester city": [
                "Manchester City: Proof that you CAN buy your way to the top... if you're unethical 💷",
                "City's financial fair play violations need their own documentary 🎬",
                "They won trophies the same way they win football matches... with unlimited funds 💰",
                "Manchester City's spending makes other clubs look like they're playing on a budget 😅",
                "At least their money buys them something - unlike United's 💸",
            ],
            "liverpool": [
                "Liverpool: Living off the 1980s harder than they live in the present 👴",
                "Anfield's walls are held up by memories and disappointment 😭",
                "They haven't learned that the 90s were 30 years ago 📅",
                "Liverpool's last exciting moment was when they actually won something 🏆❌",
                "You'd think with all that passion they'd actually win things regularly 🔴",
            ],
            "arsenal": [
                "Arsenal: The club that perfected the art of 'bottling it' 🍾",
                "4th place trophies don't look good in their cabinet... oh wait, they don't have one 🏚️",
                "Arsenal proves that a nice stadium can't compensate for poor decisions 🏟️😅",
                "They've mastered the art of promising everything and delivering nothing 🎭",
                "Arteta's tactics: hope the other team is tired 🤷",
            ],
            "chelsea": [
                "Chelsea: Where billionaires' pet projects come to die 💀",
                "They've changed owners more times than they've changed their league position 🔄",
                "Chelsea's transfer window is less about strategy and more about random chaos 🎲",
                "Stamford Bridge: Where talent goes to underperform 📉",
                "Chelsea's squad has more drama than a reality TV show 🎬",
            ],
            "tottenham": [
                "Tottenham: Consistently mediocre since forever 😴",
                "Spurs' trophy case is lonelier than their European adventures 🏆❌",
                "They're the definition of 'close but not quite' 📏",
                "Tottenham's specialty: looking good but losing when it matters 💔",
                "Kane left for a reason... and it wasn't the winning culture 👋",
            ],
            "real madrid": [
                "Goals from close range are very good. But if you're Ronaldo, it's tap-in .",
                "Real Madrid: The club that thinks spending money is a strategy 💸",
                "Los Blancos: Where history is more important than the present 🏰",
                "Real Madrid's recent form: a reminder that past glories don't guarantee future success 📉",
                "They've got the Galácticos... but where's the galactic performance? 🌌",   
                "Not even the VAR can tell why Real Madrid play like amateurs.",
                

            ],
            "barcelona": [
                "Barcelona: The club that squandered Messi and acted like it was no big deal 🐐",
                "They went from unstoppable to unaffordable real quick 💸",
                "Camp Nou has seen better days... like every day except the recent ones 🏟️😅",
                "Barcelona's recent form: a cautionary tale for spending without thinking 📖",
                "They made Messi leaving look like the best decision ever 👋",
            ],
            "manchester": [
                "Manchester: Where dreams go to compete with disappointment 💭😭",
            ],
            "chelsea fc": [
                "Chelsea: Where billionaires' pet projects come to die 💀",
                "They've changed owners more times than they've changed their league position 🔄",
            ],
            "psg": [
                "PSG: Proof that Neymar's haircuts are more entertaining than their play ✂️",
                "Paris Saint-Germain: Where superstar talent goes to underperform 📉",
                "They've got Mbappé... wait, they lost Mbappé 💔",
            ],
            "juventus": [
                "Juventus: Dominating Serie A like beating up your little brother 👊",
                "They make other Italian clubs look competent 🤷",
                "Juve's European form: not as impressive as their Italian dominance 😅",
                "Old Lady's been sitting on the throne too long 👑😴",
            ],
            "tottenham hotspur": [
                "Tottenham: Consistently mediocre since forever 😴",
                "Spurs' trophy case is lonelier than their European adventures 🏆❌",
                "They're the definition of 'close but not quite' 📏",
            ],
            "newcastle": [
                "Newcastle: Proof that Saudi oil money can't buy a winning culture (yet) 💰",
                "St James' Park is under new management... who also can't figure it out 🤷",
                "Geordie passion meets tactical cluelessness 😅",
            ],
            "luton": [
                "Luton Town: The surprise package that surprised nobody by disappearing 🎁👻",
            ],
            "brighton": [
                "Brighton: Peak entertainment that somehow never translates to trophies 🎪",
                "De Zerbi left because he realized miracles take time 🧙",
            ],
            "west ham": [
                "West Ham: Perpetually stuck between 'nearly' and 'never' 📍",
            ],
            "everton": [
                "Everton: Living in the shadow of their neighbors AND their own history 👻",
                "Goodison Park is haunted by better times 🏟️👻",
            ],
            "aston villa": [
                "Aston Villa: Decent again! For now... 👀",
            ],
            "crystal palace": [
                "Crystal Palace: Roy Hodgson's retirement home ⚪",
            ],
        }

    @commands.command(name="roast")
    @commands.has_permissions(manage_messages=True)
    async def roast_club(self, ctx, *, club_name: str = None):
        """Roast a football club! Usage: !roast [club name]"""
        
        if not club_name:
            embed = discord.Embed(
                title="⚽ Football Club Roaster",
                description="Usage: `!roast [club name]`\n\nSupported clubs: Manchester United, Manchester City, Liverpool, Arsenal, Chelsea, Tottenham, Real Madrid, Barcelona, PSG, Juventus, Newcastle, Aston Villa, Brighton, Everton, West Ham, Crystal Palace, Luton, and more!",
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)
            return
        
        club_key = club_name.lower().strip()
        
        if club_key not in self.roasts:
            # Fuzzy match for common variations
            available = ", ".join(set(c.replace(" fc", "").title() for c in self.roasts.keys()))
            embed = discord.Embed(
                title="❌ Club Not Found",
                description=f"I don't have roasts for **{club_name}**\n\nAvailable clubs:\n{available}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        roast = random.choice(self.roasts[club_key])
        
        embed = discord.Embed(
            title=f"🔥 Roasting {club_name.title()}...",
            description=roast,
            color=discord.Color.red()
        )
        embed.set_footer(text=f"Roasted by {ctx.author.display_name}")
        
        await ctx.send(embed=embed)

    @commands.command(name="roastlist")
    async def roast_list(self, ctx):
        """Show all available clubs to roast"""
        clubs = sorted(set(c.replace(" fc", "").title() for c in self.roasts.keys()))
        
        embed = discord.Embed(
            title="⚽ Available Clubs for Roasting",
            description="\n".join(clubs),
            color=discord.Color.orange()
        )
        embed.set_footer(text=f"Use !roast [club name] to roast a club!")
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Roast(bot))
