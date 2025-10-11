import discord
from discord.ext import commands, tasks
import os
import json
from datetime import date

# ==== JSON LOADER PARAMETERS + FUNCTIONS ====

DATA_FILE = "birthdays.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# ==== TEAM BUILDER CODE ====

class BirthdayGreeter(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # ==== LOADING DATA FROM JSON FILE ====

        self.data = load_data()
        self.birthday_today = False

        self.grab_users_daily.start()
        self.greet_daily.start()
    
    def get_guild_data(self, guild_id):
        self.data = load_data()
        if str(guild_id) not in self.data:
            self.data[str(guild_id)] = {
                "channel" : None,
                "members" : {}
            }
        return self.data[str(guild_id)]

    @commands.command()
    async def set_bday_channel(self, ctx):
        try:
            await ctx.message.delete()
        except:
            print("No permission to delete messages")

        self.data[str(ctx.guild.id)]["channel"] = ctx.channel.id
        save_data(self.data)
    
    @tasks.loop(hours=24)
    async def grab_users_daily(self):
        for guild in self.bot.guilds:
            try:
                self.update_users(guild)
            except:
                print(f"Cannot grab new users from {guild.name} today")
        

    @commands.command()
    async def grab_users(self, ctx):
        self.update_users(ctx.guild)

    def update_users(self, guild):
        guild_data = self.get_guild_data(guild.id)
        for member in guild.members:
            if member.bot:
                continue
            user_id = str(member.id)
            if user_id not in guild_data["members"]:
                guild_data["members"][user_id] = {
                    "display" : member.display_name,
                    "birthday" : None
                }
        save_data(self.data)
                
    async def greet(self, guild, today):
        guild_data = self.get_guild_data(guild.id)
        channel = guild.get_channel(guild_data["channel"])
        if not channel:
            return
        self.birthday_today = False
        found = False
        for user_id, info in guild_data["members"].items():
            if info["birthday"] == today:
                member = guild.get_member(int(user_id))
                if member and channel:
                    await channel.send(f"🎉 It's {member.mention} day!! 🎂")
                    found = True
        self.birthday_today = found
                
    @tasks.loop(hours=24)
    async def greet_daily(self):
        today = date.today().strftime("%m-%d")
        for guild in self.bot.guilds:
            await self.greet(guild, today)


    @commands.command()
    async def force_greet(self, ctx):
        today = date.today().strftime("%m-%d")
        await self.greet(ctx.guild, today)
        if not self.birthday_today:
            await ctx.send(f"No birthday today! {today}")


    @greet_daily.before_loop
    async def before_greet(self):
        await self.bot.wait_until_ready()

        
async def setup(bot):
    await bot.add_cog(BirthdayGreeter(bot))