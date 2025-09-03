import discord
from discord.ext import commands

class Polls(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def poll(self, ctx, question: str, *options):
        """Create a poll: !poll 'Best color?' Red Blue Green"""
        if len(options) < 2:
            await ctx.send("You need at least 2 options!")
            return

        description = ""
        emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣"]

        for i, option in enumerate(options):
            description += f"{emojis[i]} {option}\n"

        embed = discord.Embed(title=question, description=description, color=0x00ff00)
        msg = await ctx.send(embed=embed)

        for i in range(len(options)):
            await msg.add_reaction(emojis[i])

def setup(bot):
    bot.add_cog(Polls(bot))
