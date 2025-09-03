import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import logging 

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.members = False
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

@bot.command()
async def hello(ctx):
    await ctx.send("Hello! 👋")

# # Load cogs (modules)
# initial_cogs = ["cogs.greeter", "cogs.roles", "cogs.polls"]


# for cog in initial_cogs:
#     bot.load_extension(cog)

bot.run(TOKEN, log_handler=handler, log_level=logging.DEBUG)
