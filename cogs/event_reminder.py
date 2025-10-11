import discord
from discord.ext import commands, tasks
import os
import json
from datetime import datetime, timezone

# ==== JSON LOADER PARAMETERS + FUNCTIONS ====

DATA_FILE = "reminders.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)


# ==== ACTUAL WELCOME CODE ====

class EventReminder(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.data = load_data()
        
        self.remind_auto.start()

    def get_guild_data(self, guild_id):
        if str(guild_id) not in self.data:
            self.data[str(guild_id)] = {
                "channel" : None,
                "events" : {}
            }
        return self.data[str(guild_id)]
    
    @commands.Cog.listener()
    async def on_ready(self):
        if not self.remind_auto.is_running():
            self.remind_auto.start()


    @commands.command()
    async def set_reminder_channel(self, ctx):

        # ==== DELETING COMMAND MESSAGE ====
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            print("Bot doesn't have permission to delete messages.")

        # ==== LOAD GUILD INFO ====

        guild_data = self.get_guild_data(ctx.guild.id)
        guild_data["channel"] = ctx.channel.id

        save_data(self.data)

    @tasks.loop(minutes=10)
    async def remind_auto(self):
        for guild in self.bot.guilds:
            await self._reminder(guild)

    @commands.command()
    async def remind_force(self, ctx):
        guild = ctx.guild
        await self._reminder(guild)

    async def _reminder(self, guild):
        guild_data = self.get_guild_data(guild.id)
        channel_id = guild_data["channel"]
        channel = self.bot.get_channel(channel_id)

        if not channel_id or not channel:
            print(f"No channel to post to in {guild.name}!")
            return
        
        events = await guild.fetch_scheduled_events()

        if not events:
            print("No upcoming events!")
            return
        
        now = datetime.now(timezone.utc)

        for event in events:
            name = event.name
            if name not in guild_data["events"]:
                guild_data["events"][name] = {
                    "threedays" : False,
                    "twodays" : False,
                    "oneday" : False,
                    "twohours" : False
                }

            time = event.start_time
            diff = time - now
            hours = diff.total_seconds() / 3600

            if 48 <= hours < 72 and not guild_data["events"][name]["threedays"]:
                await channel.send(f"Only 3 DAYS LEFT until {name}!!")
                guild_data["events"][name]["threedays"] = True
            elif 24 <= hours < 48 and not guild_data["events"][name]["twodays"]:
                await channel.send(f"Only 2 DAYS LEFT until {name}!!")
                guild_data["events"][name]["twodays"] = True
            elif 2 <= hours < 24 and not guild_data["events"][name]["oneday"]:
                await channel.send(f"Only 1 DAY LEFT until {name}!!")
                guild_data["events"][name]["oneday"] = True
            elif 0 <  hours < 2 and not guild_data["events"][name]["twohours"]: 
                await channel.send (f"{name} starts in 2 HOURS!!")
                guild_data["events"][name]["twohours"] = True
        save_data(self.data)
        
async def setup(bot):
    await bot.add_cog(EventReminder(bot))