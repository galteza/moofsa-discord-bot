import discord
from discord.ext import commands
import os
import json

# ==== JSON LOADER PARAMETERS + FUNCTIONS ====

DATA_FILE = "welcome.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)


# ==== ACTUAL WELCOME CODE ====

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.data = load_data()
        self.guild_id = None
        self.message_id = None
        self.title = None
        self.desc = None

    def retrieve_guild_data(self, guild_id):
        if str(guild_id) not in self.data:
            return
        else:
            self.message_id = self.data[str(guild_id)]["message_id"]
            self.title = self.data[str(guild_id)]["title"]
            self.desc = self.data[str(guild_id)]["desc"]
        return


    @commands.command()
    async def setup_welcome(self, ctx, title_user : str = None, desc_user : str = None):

        # ==== DELETING COMMAND MESSAGE ====
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            print("Bot doesn't have permission to delete messages.")

        # ==== LOAD GUILD INFO ====

        self.guild_id = ctx.guild.id
        self.retrieve_guild_data(self.guild_id)

        # ==== POST MESSAGE ====

        title = title_user if title_user else self.title
        desc = desc_user if desc_user else self.desc
        embed = discord.Embed(
            title=title,
            description=desc,
            color=0x00ff00
        )

        msg = await ctx.send(embed=embed)
        self.message_id = msg.id

        await msg.add_reaction("🐄")

        # ==== UPDATE JSON ====

        guild_id = ctx.guild.id
        self.data[str(guild_id)] = {
            "message_id" : msg.id,
            "title" : title,
            "desc" : desc
        } 

        save_data(self.data)


    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        # ==== GET GUILD, CHANNEL, MEMBER, & MESSAGE OF PAYLOAD ====
        
        
        guild_id = payload.guild_id
        message_id = self.data[str(guild_id)]["message_id"]
        self.retrieve_guild_data(guild_id)
        guild = self.bot.get_guild(guild_id)

        # ==== CHECK IF PAYLOAD WAS ON A MESSAGE STORED ====

        if (str(guild_id) not in self.data or message_id != payload.message_id):
            print("Not in storage")
            return
        
        member = guild.get_member(payload.user_id) or await guild.fetch_member(payload.user_id)
        if member.bot:
            return

        if str(payload.emoji) == "🐄":
            role_name = "Member"
            role = discord.utils.get(guild.roles, name=role_name)
            await member.add_roles(role)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        # ==== GET GUILD, CHANNEL, MEMBER, & MESSAGE OF PAYLOAD ====
        
        guild_id = payload.guild_id
        message_id = self.data[str(guild_id)]["message_id"]
        self.retrieve_guild_data(guild_id)
        guild = self.bot.get_guild(guild_id)


        # ==== CHECK IF PAYLOAD WAS ON A MESSAGE STORED ====

        if (str(guild_id) not in self.data or message_id != payload.message_id):
            print("Not in storage")
            return
        
        member = guild.get_member(payload.user_id) or await guild.fetch_member(payload.user_id)
        if member.bot:
            return
        
        if str(payload.emoji) == "🐄":
            role_name = "Member"
            role = discord.utils.get(guild.roles, name=role_name)
            if role in member.roles:
                await member.remove_roles(role)
        
async def setup(bot):
    await bot.add_cog(Welcome(bot))