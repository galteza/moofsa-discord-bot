import discord
from discord.ext import commands, tasks
import os
import yaml
from datetime import datetime, timezone

# ==== FILE SETUP (ONLY STATIC YAML NOW) ====
CONFIG_FILE = "configs/guild_configs.yaml"

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return yaml.safe_load(f) or {}
    return {}

def save_config(data):
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        yaml.dump(data, f, default_flow_style=False, indent=4)

# ==== ACTUAL REMINDER CODE ====

class EventReminder(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.remind_auto.start()

    def cog_unload(self):
        self.remind_auto.cancel()

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def set_reminder_channel(self, ctx):
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass

        # Save channel ID strictly to the YAML
        config = load_config()
        config["reminder_channel"] = ctx.channel.id
        save_config(config)
        
        msg = await ctx.send(f"✅ Event reminders will now be posted in {ctx.channel.mention}!")
        await msg.delete(delay=3)

    # ==== RUNS EXACTLY EVERY 10 MINUTES ====
    @tasks.loop(minutes=10)
    async def remind_auto(self):
        await self._process_reminders()

    @remind_auto.before_loop
    async def before_remind_auto(self):
        await self.bot.wait_until_ready()

    async def _process_reminders(self):
        config = load_config()
        channel_id = config.get("reminder_channel")
        
        if not channel_id:
            return

        channel = self.bot.get_channel(channel_id)
        if not channel:
            return

        guild = channel.guild
        events = await guild.fetch_scheduled_events()
        now = datetime.now(timezone.utc)
        
        for event in events:
            # Time difference in minutes
            diff = event.start_time - now
            minutes_left = diff.total_seconds() / 60

            # Ignore past events
            if minutes_left < 0:
                continue

            name = event.name
            url = event.url

            # ==== THE STATELESS TRICK ====
            # Because the loop runs every 10 minutes, we check if the event is inside a 10-minute window.
            # This guarantees the reminder only fires exactly once without needing a JSON file to remember!
            
            # 3 Days = 4320 minutes
            if 4320 <= minutes_left < 4330:
                await channel.send(f"📅 Only **3 DAYS LEFT** until **{name}**!!\n{url}")
                
            # 2 Days = 2880 minutes
            elif 2880 <= minutes_left < 2890:
                await channel.send(f"⏳ Only **2 DAYS LEFT** until **{name}**!!\n{url}")
                
            # 1 Day = 1440 minutes
            elif 1440 <= minutes_left < 1450:
                await channel.send(f"🚨 Only **1 DAY LEFT** until **{name}**!!\n{url}")
                
            # 2 Hours = 120 minutes
            elif 120 <= minutes_left < 130: 
                await channel.send(f"🔥 **{name}** starts in **2 HOURS**!!\n{url}")

async def setup(bot):
    await bot.add_cog(EventReminder(bot))