import discord
from discord.ext import commands

class Greeter(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        channel = member.guild.system_channel  # or choose a specific welcome channel
        if channel:
            await channel.send(
                f"👋 Welcome {member.mention} to **{member.guild.name}**!\n"
                f"Please check the rules and pick your role!"
            )

def setup(bot):
    bot.add_cog(Greeter(bot))
