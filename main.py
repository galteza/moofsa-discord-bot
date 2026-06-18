import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import logging 
from flask import Flask
from threading import Thread

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# ==== FLASK KEEP-ALIVE SERVER ====
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is awake and healthy! 🟢"

def run_server():
    # Render dynamically assigns a PORT environment variable. 
    # We must bind to this port and 0.0.0.0 for Render to detect the web service.
    port = int(os.environ.get("PORT", 10000))
    # Disable Flask's startup banner and debug mode so it doesn't spam your Discord logs
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

def keep_alive():
    # Run the Flask server in a separate background thread
    server = Thread(target=run_server)
    server.daemon = True  # Ensures the thread dies if the main bot crashes
    server.start()


# ==== DISCORD BOT SETUP ====
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
    "cogs.event_reminder"
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

# ==== EXECUTE ====
if __name__ == "__main__":
    # 1. Start the web server thread
    keep_alive()
    
    # 2. Start the Discord bot (this blocks the main thread)
    bot.run(TOKEN, log_handler=handler, log_level=logging.DEBUG)