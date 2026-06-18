import discord
from discord.ext import commands
import os
import yaml

# ==== YAML LOADER PARAMETERS + FUNCTIONS ====

DATA_FILE = "configs/guild_configs.yaml"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return yaml.safe_load(f) or {}
    return {}

def save_data(data):
    # Ensure the 'configs' directory exists before trying to save
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w") as f:
        yaml.dump(data, f, default_flow_style=False, indent=4)

# ==== ACTUAL WELCOME CODE ====

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data = load_data()

    @commands.command()
    async def setup_welcome(self, ctx, title_user: str = None, desc_user: str = None):
        # ==== DELETING COMMAND MESSAGE ====
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            print("Bot doesn't have permission to delete messages.")

        # ==== POST MESSAGE ====
        title = title_user if title_user else "Welcome!"
        desc = desc_user if desc_user else "React below to get your role!"
        
        embed = discord.Embed(
            title=title,
            description=desc,
            color=0x00ff00
        )

        msg = await ctx.send(embed=embed)
        await msg.add_reaction("🐄")

        # ==== UPDATE YAML ====
        # Update the global welcome_message ID directly
        self.data["welcome_message"] = msg.id
        
        save_data(self.data)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        # ==== CHECK IF MESSAGE MATCHES STORED ID ====
        stored_message_id = self.data.get("welcome_message")
        
        if not stored_message_id or payload.message_id != stored_message_id:
            return
        
        # ==== PROCESS REACTION ====
        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return

        member = payload.member or guild.get_member(payload.user_id) or await guild.fetch_member(payload.user_id)
        if member.bot:
            return

        if str(payload.emoji) == "🐄":
            role_name = "Member"
            role = discord.utils.get(guild.roles, name=role_name)
            if role:
                await member.add_roles(role)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        # ==== CHECK IF MESSAGE MATCHES STORED ID ====
        stored_message_id = self.data.get("welcome_message")
        
        if not stored_message_id or payload.message_id != stored_message_id:
            return
        
        # ==== PROCESS REACTION ====
        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return

        member = guild.get_member(payload.user_id) or await guild.fetch_member(payload.user_id)
        if not member or member.bot:
            return
        
        if str(payload.emoji) == "🐄":
            role_name = "Member"
            role = discord.utils.get(guild.roles, name=role_name)
            if role and role in member.roles:
                await member.remove_roles(role)
        
async def setup(bot):
    await bot.add_cog(Welcome(bot))