import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Load cogs (modules)
initial_cogs = ["cogs.greeter", "cogs.roles", "cogs.polls"]

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

for cog in initial_cogs:
    bot.load_extension(cog)

bot.run("YOUR_BOT_TOKEN")
