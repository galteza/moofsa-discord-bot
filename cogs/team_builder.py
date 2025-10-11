import discord
from discord.ext import commands
import os
import json

# ==== JSON LOADER PARAMETERS + FUNCTIONS ====

DATA_FILE = "teams.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# ==== TEAM BUILDER CODE ====

class BuildTeam(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # ==== LOADING DATA FROM JSON FILE ====

        self.data = load_data()

        self.guild_id = None
    
    def get_guild_data(self, guild_id):
        if str(guild_id) not in self.data:
            self.data[str(guild_id)] = {}
        return self.data[str(guild_id)]

    @commands.command()
    async def setup_team(self, ctx, team_role: str, desc: str = None):

        # !setup_team "<team role name>" "<emoji>" "<description>"

        # ==== DELETING COMMAND MESSAGE ====

        try:
            await ctx.message.delete()
        except discord.Forbidden:
            print("Bot doesn't have permission to delete messages.")

        # ==== LOAD GUILD INFO ====

        self.guild_id = ctx.guild.id

        # ==== POST MESSAGE ====

        embed = discord.Embed(
            title=team_role,
            description=desc,
            color=0x00ff00
        )

        msg = await ctx.send(embed=embed)
        self.message_id = msg.id

        await msg.add_reaction("✅")

        # ==== UPDATE JSON ====

        guild_id = ctx.guild.id
        self.get_guild_data(guild_id)
        self.data[str(guild_id)][str(msg.id)] = {
            "team_name": team_role,
            "description": desc
        }
        save_data(self.data)


    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        # ==== GET GUILD, CHANNEL, MEMBER, & MESSAGE OF PAYLOAD ====
        
        guild_id = payload.guild_id
        message_id = payload.message_id
        guild = self.bot.get_guild(guild_id)

        # ==== CHECK IF PAYLOAD WAS ON A MESSAGE STORED ====

        if (str(guild_id) not in self.data or str(message_id) not in self.data[str(guild_id)]):
            return
        
        member = guild.get_member(payload.user_id) or await guild.fetch_member(payload.user_id)
        if member.bot:
            return

        if str(payload.emoji) == "✅":
            role_name = self.data[str(guild_id)][str(payload.message_id)]["team_name"]
            print(role_name)
            role = discord.utils.get(guild.roles, name=role_name)
            await member.add_roles(role)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        # ==== GET GUILD, CHANNEL, MEMBER, & MESSAGE OF PAYLOAD ====
        
        guild_id = payload.guild_id
        guild = self.bot.get_guild(guild_id)

        # ==== CHECK IF PAYLOAD WAS ON A MESSAGE STORED ====

        if (str(guild_id) not in self.data or str(payload.message_id) not in self.data[str(guild_id)]):
            return
        
        member = guild.get_member(payload.user_id) or await guild.fetch_member(payload.user_id)
        if member.bot:
            return
        
        if str(payload.emoji) == "✅":
            role_name = self.data[str(guild_id)][str(payload.message_id)]["team_name"]
            role = discord.utils.get(guild.roles, name=role_name)
            if role in member.roles:
                await member.remove_roles(role)
        
async def setup(bot):
    await bot.add_cog(BuildTeam(bot))