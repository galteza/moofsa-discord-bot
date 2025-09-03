# import discord
# from discord.ext import commands
# import os
# from dotenv import load_dotenv

# load_dotenv()

# TOKEN = os.getenv("DISCORD_TOKEN")

# intents = discord.Intents.default()
# intents.members = False
# intents.message_content = True

# bot = commands.Bot(command_prefix="!", intents=intents)

# print(TOKEN)

# # # Load cogs (modules)
# # initial_cogs = ["cogs.greeter", "cogs.roles", "cogs.polls"]

# # @bot.event
# # async def on_ready():
# #     print(f"✅ Logged in as {bot.user}")

# # for cog in initial_cogs:
# #     bot.load_extension(cog)

# # bot.run("YOUR_BOT_TOKEN")




# # import discord
# # from discord.ext import commands

# # intents = discord.Intents.default()
# # intents.message_content = True  # Required for reading messages

# # bot = commands.Bot(command_prefix="!", intents=intents)

# @bot.event
# async def on_ready():
#     print(f"Logged in as {bot.user}")



# bot.run(TOKEN)

import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = "REMOVED"

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

bot.run(TOKEN)
