import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import logging 

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ==== STARTUP BOT ====

@bot.event
async def on_ready():
    print(f"✅ Time to enter, {bot.user}!")

# ==== HELLO WORLD ====

@bot.command()
async def hello(ctx):
    await ctx.send("Hello! 👋")

# ==== COG LOADING ======
initial_cogs = [
    "cogs.welcome_greeter",
    "cogs.batch_assigner",
    "cogs.team_builder",
    "cogs.poll_maker",
    "cogs.birthday_greeter"
]

async def load_cogs():
    for cog in initial_cogs:
        try:
            await bot.load_extension(cog)
            print(f"✅ {cog} has been loaded")
        except Exception as e:
            print(f"❌ {cog} failed to load: {e}")


# Setup hook is immediately called upon startup (run)
@bot.event
async def setup_hook():
    await load_cogs()

bot.run(TOKEN, log_handler=handler, log_level=logging.DEBUG)
