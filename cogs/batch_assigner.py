import discord
from discord.ext import commands, tasks
from datetime import date
import json
import os
import asyncio

# ==== JSON LOADER PARAMETERS + FUNCTIONS ====

DATA_FILE = "batches.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        return json.dump(data, f, indent=4)

# ==== ACTUAL BATCH CHOOSING CODE ====

class ChooseBatch(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # ==== LOADING DATA FROM JSON FILE ====

        self.data = load_data()

        # ==== INITIALIZING PARAMETERS ====

        self.batches = None
        self.guild_id = None
        self.message_id = None
        self.channel_id = None
        self.user_tasks = {}

        # self.check_rollover.start()

    # def cog_unload(self):
    #     self.check_rollover.cancel()

    def get_guild_data(self, guild_id):
        if str(guild_id) not in self.data:
            self.data[str(guild_id)] = {
                "batch_message_id": None,
                "batch_channel_id": None,
                "batches": {
                    "🎓": "Alumni",
                    "🟦": "2025",
                    "🟩": "2026",
                    "🟨": "2027",
                    "🟧": "2028",
                    "🟥": "2029"
                }
            }
        return self.data[str(guild_id)]
    
    def retrieve_guild_data(self, guild_id):
        if str(guild_id) not in self.data:
            return
        else:
            self.message_id = self.data[str(guild_id)]["batch_message_id"]
            self.channel_id = self.data[str(guild_id)]["batch_channel_id"]
            self.batches = self.data[str(guild_id)]["batches"]
        return
        
    
    @commands.command(name="setup_batches")
    async def setup_batches(self, ctx):

        # ==== DELETING COMMAND MESSAGE ====
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            print("Bot doesn't have permission to delete messages.")

        # ==== LOADING GUILD INFO ====

        self.data = load_data()
        self.guild_id = ctx.guild.id
        self.batches = self.get_guild_data(self.guild_id)["batches"]

        # ==== POSTING REACTION ROLE MESSAGE ====
        
        choices = "\n".join([f"{emoji} → {role}" for emoji, role in self.batches.items()])
        desc = f"When will you be graduating?\n\n{choices}"

        embed = discord.Embed(
            title="CHOOSE YOUR BATCH",
            description=desc,
            color=0x00ff00
        )

        msg = await ctx.send(embed=embed)

        for emoji in self.batches:
            await msg.add_reaction(emoji)

        # ==== FILLS IN JSON FILE BASED ON WHAT WAS OUTPUT ====

        # self.data[str(self.guild_id)] = {
        #     "batch_message_id": self.message_id,
        #     "batch_channel_id": self.channel_id,
        #     "batches": self.batches
        # }
        # save_data(self.data)

        self.data[str(self.guild_id)]["batch_message_id"] = msg.id
        self.data[str(self.guild_id)]["batch_channel_id"] = ctx.channel.id
        save_data(self.data)


    # @tasks.loop(hours=24)
    
    # async def check_rollover(self):
    #     today = date.today()
    #     if today.month == 4 and today.day == 1:
    #         await self.its_rollover_time()

    @commands.command(name="its_rollover_time")
    async def its_rollover_time(self, ctx=None):
        for guild in self.bot.guilds:
            try:
                self.retrieve_guild_data(guild.id)
                if self.message_id:
                    # ==== ACCESS CHANNEL AND MESSAGE ====
                    channel = guild.get_channel(self.channel_id)
                    msg = await channel.fetch_message(self.message_id)

                    # ==== GETTING GUILD & IMPORTANT INFO ====

                    self.guild_id = guild.id
                    guild_data = self.get_guild_data(self.guild_id)

                    self.channel_id = guild_data["batch_channel_id"]
                    self.message_id = guild_data["batch_message_id"]
                    self.batches = guild_data["batches"]
                    
                    # ==== DIVIDING LIST OF BATCHES INTO ALUM AND NON-ALUM ====
                    alumni = {"🎓": "Alumni"}
                    non_alumni = [(k, v) for k, v in self.batches.items() if v != "Alumni"]

                    # ==== SORTS NON-ALUM ONES DOWN-UP ====
                    oldest_emoji, oldest_batch = sorted(
                        non_alumni,
                        key=lambda x: int(x[1])
                    )[0]
                    
                    # ==== GRABS THE ALUM & TO-BE-REMOVED ROLE IN DISCORD ====
                    alumni_role = discord.utils.get(guild.roles, name="Alumni")
                    oldest_role = discord.utils.get(guild.roles, name=oldest_batch)
                    print(alumni_role)
                    print(oldest_batch)

                    for member in oldest_role.members:
                        print(member.id)
                        await member.add_roles(alumni_role)
                    
                    # ==== CHANGING RECENTLY GRADUATED BATCH TO NEW BATCH ====

                    new_batch = str(int(max(int(v) for k, v in non_alumni)) + 1)
                    self.batches[oldest_emoji] = new_batch

                    # ==== ROTATING LIST SO THAT NEW BATCH GOES TO THE BOTTOM ====
                    
                    rotated = non_alumni[1:] + [(oldest_emoji, new_batch)]
                    self.batches = {**alumni, **dict(rotated)}

                    # ==== UPDATES MESSAGE TO REFLECT CHANGES ====

                    await msg.clear_reaction(oldest_emoji)
                    await msg.add_reaction(oldest_emoji)

                    choices = "\n".join([f"{emoji} → {role}" for emoji, role in self.batches.items()])
                    desc = f"When will you be graduating?\n\n{choices}"

                    embed = discord.Embed(
                        title="CHOOSE YOUR BATCH",
                        description=desc,
                        color=0x00ff00
                    )
                    await msg.edit(embed=embed)

                    # ==== UPDATE JSON ====

                    self.data[str(guild.id)] = {
                        "batch_message_id": self.message_id,
                        "batch_channel_id": self.channel_id,
                        "batches": self.batches
                    }
                    save_data(self.data)
            except Exception as e:
                print(f"⚠️ Error in rollover: {e}")
        

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):

        # ==== GUILD, CHANNEL, MESSAGE, EXECUTING MEMBER INFO ====
        guild = self.bot.get_guild(payload.guild_id)
        self.retrieve_guild_data(guild.id)

        # ==== CHECK IF PAYLOAD WAS ON THE RIGHT MESSAGE ====
        if payload.message_id != self.message_id:
            return

        channel = guild.get_channel(self.channel_id)
        member = guild.get_member(payload.user_id) or await guild.fetch_member(payload.user_id)
        message = await channel.fetch_message(self.message_id)

        # ==== IGNORING BOT REACTIONS ====

        if member.bot:
            return
        
        # ==== EMOJI REACTION FROM PAYLOAD ====
        
        chosen_emoji = str(payload.emoji)
        
        # ==== CANCEL ALL PREVIOUS INSTANCES OF TASK IF STILL RUNNING & UNFINISHED ====
        if member.id in self.user_tasks:
            task = self.user_tasks[member.id]
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        # ==== START ACTUAL TASK USING MOST RECENT CHOSEN EMOJI ====
        task = asyncio.create_task(self._handle_role_change(guild, member, message, chosen_emoji))
        self.user_tasks[member.id] = task

    async def _handle_role_change(self, guild, member, message, chosen_emoji):
        
        # ==== REMOVE EMOJI REACTIONS IF NOT CHOSEN EMOJI ====
        
        for reaction in message.reactions:
            reaction_emoji = str(reaction.emoji)
            if reaction_emoji != chosen_emoji:
                await reaction.remove(member)

        # ==== ACCESS CORRESPONDING ROLE TO CHOSEN EMOJI ====
        chosen_role_name = self.batches.get(chosen_emoji)
        if not chosen_role_name:
            return
        chosen_role = discord.utils.get(guild.roles, name=chosen_role_name)

        # ==== REMOVE ROLES THAT AREN'T CORRESPONDING CHOSEN ROLE ====
        for emoji, role_name in list(self.batches.items())[1:]:
            role = discord.utils.get(guild.roles, name=role_name)
            if role and role_name != chosen_role_name and role in member.roles:
                await member.remove_roles(role)

        # ==== FINALLY ADD CHOSEN ROLE ====
        if chosen_role not in member.roles:
            await member.add_roles(chosen_role)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        # ==== GUILD, CHANNEL, MESSAGE, EXECUTING MEMBER INFO ====
        guild = self.bot.get_guild(payload.guild_id)
        self.retrieve_guild_data(guild.id)
        
        # ==== CHECK IF PAYLOAD WAS ON THE RIGHT MESSAGE ==== 
        if payload.message_id != self.message_id:
            return

        # ==== IDENTIFY MEMBER WHO INDUCES PAYLOAD ====
        member = guild.get_member(payload.user_id) or await guild.fetch_member(payload.user_id)
        if member.bot:
            return

        # ==== REMOVE ROLE CORRESPODING TO PAYLOAD EMOJI ====
        role_name = self.batches.get(str(payload.emoji))
        role = discord.utils.get(guild.roles, name=role_name)
        if role in member.roles:
            await member.remove_roles(role)


async def setup(bot):
    await bot.add_cog(ChooseBatch(bot))