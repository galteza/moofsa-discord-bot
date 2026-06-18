import discord
from discord.ext import commands, tasks
from datetime import date
import yaml
import os
import asyncio

# ==== YAML LOADER PARAMETERS + FUNCTIONS ====

DATA_FILE = "configs/guild_configs.yaml"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return yaml.safe_load(f) or {}
    return {}

def save_data(data):
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w") as f:
        yaml.dump(data, f, default_flow_style=False, indent=4)

# ==== ACTUAL BATCH CHOOSING CODE ====

class ChooseBatch(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data = load_data()
        self.user_tasks = {}
        
        # Start the background task for the yearly rollover
        self.check_rollover.start()

    def cog_unload(self):
        self.check_rollover.cancel()

    # ==== HELPER TO READ BATCHES DIRECTLY FROM DISCORD EMBED ====
    def parse_batches_from_embed(self, message):
        batches = {}
        if not message.embeds:
            return batches
            
        desc = message.embeds[0].description
        for line in desc.split('\n'):
            if '→' in line:
                emoji, role = line.split('→')
                batches[emoji.strip()] = role.strip()
        return batches

    @commands.command(name="setup_batches")
    async def setup_batches(self, ctx):
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            print("Bot doesn't have permission to delete messages.")

        # Default starting point if setting up for the first time
        default_batches = {
            "🎓": "Alumni",
            "🟦": "2025",
            "🟩": "2026",
            "🟨": "2027",
            "🟧": "2028",
            "🟥": "2029"
        }

        choices = "\n".join([f"{emoji} → {role}" for emoji, role in default_batches.items()])
        desc = f"When will you be graduating?\n\n{choices}"

        embed = discord.Embed(
            title="CHOOSE YOUR BATCH",
            description=desc,
            color=0x00ff00
        )

        msg = await ctx.send(embed=embed)

        for emoji in default_batches:
            await msg.add_reaction(emoji)

        # ==== UPDATE YAML (STATIC IDs ONLY) ====
        self.data = load_data()
        self.data["select_role_message"] = msg.id
        self.data["select_role_channel"] = ctx.channel.id
        save_data(self.data)

    # ==== AUTOMATED YEARLY BACKGROUND TASK ====
    @tasks.loop(hours=24)
    async def check_rollover(self):
        today = date.today()
        # Checks if it is July 15th (graduation time for NUFSA members)
        if today.month == 7 and today.day == 15:
            await self.execute_rollover()

    @check_rollover.before_loop
    async def before_check_rollover(self):
        await self.bot.wait_until_ready()

    # ==== MANUAL COMMAND OVERRIDE ====
    @commands.command(name="force_rollover")
    @commands.has_permissions(administrator=True)
    async def force_rollover(self, ctx):
        await self.execute_rollover()
        await ctx.send("Manual rollover executed successfully!")

    # ==== CORE ROLLOVER LOGIC ====
    async def execute_rollover(self):
        self.data = load_data()
        message_id = self.data.get("select_role_message")
        channel_id = self.data.get("select_role_channel")

        if not message_id or not channel_id:
            return

        for guild in self.bot.guilds:
            try:
                channel = guild.get_channel(channel_id)
                if not channel:
                    continue
                    
                msg = await channel.fetch_message(message_id)
                current_batches = self.parse_batches_from_embed(msg)
                
                if not current_batches:
                    continue

                alumni = {"🎓": "Alumni"}
                non_alumni = [(k, v) for k, v in current_batches.items() if v != "Alumni"]

                oldest_emoji, oldest_batch = sorted(non_alumni, key=lambda x: int(x[1]))[0]
                
                alumni_role = discord.utils.get(guild.roles, name="Alumni")
                oldest_role = discord.utils.get(guild.roles, name=oldest_batch)

                # Move members to Alumni
                if oldest_role and alumni_role:
                    for member in oldest_role.members:
                        await member.add_roles(alumni_role)
                
                # Math for new batch
                new_batch = str(int(max(int(v) for k, v in non_alumni)) + 1)

                rotated = non_alumni[1:] + [(oldest_emoji, new_batch)]
                updated_batches = {**alumni, **dict(rotated)}

                await msg.clear_reaction(oldest_emoji)
                await msg.add_reaction(oldest_emoji)

                choices = "\n".join([f"{emoji} → {role}" for emoji, role in updated_batches.items()])
                desc = f"When will you be graduating?\n\n{choices}"

                embed = discord.Embed(
                    title="CHOOSE YOUR BATCH",
                    description=desc,
                    color=0x00ff00
                )
                await msg.edit(embed=embed)
                print(f"Successfully rolled over roles in {guild.name}")
                
            except Exception as e:
                print(f"⚠️ Error in rollover for {guild.name}: {e}")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        stored_message_id = self.data.get("select_role_message")
        if not stored_message_id or payload.message_id != stored_message_id:
            return

        guild = self.bot.get_guild(payload.guild_id)
        if not guild: return

        member = payload.member or guild.get_member(payload.user_id) or await guild.fetch_member(payload.user_id)
        if member.bot: return
        
        channel = guild.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        chosen_emoji = str(payload.emoji)
        
        if member.id in self.user_tasks:
            task = self.user_tasks[member.id]
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        task = asyncio.create_task(self._handle_role_change(guild, member, message, chosen_emoji))
        self.user_tasks[member.id] = task

    async def _handle_role_change(self, guild, member, message, chosen_emoji):
        # Dynamically read the current years from the Discord message embed
        batches = self.parse_batches_from_embed(message)
        
        for reaction in message.reactions:
            if str(reaction.emoji) != chosen_emoji:
                await reaction.remove(member)

        chosen_role_name = batches.get(chosen_emoji)
        if not chosen_role_name: return
            
        chosen_role = discord.utils.get(guild.roles, name=chosen_role_name)

        for emoji, role_name in list(batches.items())[1:]: 
            role = discord.utils.get(guild.roles, name=role_name)
            if role and role_name != chosen_role_name and role in member.roles:
                await member.remove_roles(role)

        if chosen_role and chosen_role not in member.roles:
            await member.add_roles(chosen_role)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        stored_message_id = self.data.get("select_role_message")
        if not stored_message_id or payload.message_id != stored_message_id:
            return

        guild = self.bot.get_guild(payload.guild_id)
        if not guild: return

        member = guild.get_member(payload.user_id) or await guild.fetch_member(payload.user_id)
        if not member or member.bot: return

        channel = guild.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        
        # Dynamically read the current years from the Discord message embed
        batches = self.parse_batches_from_embed(message)
        role_name = batches.get(str(payload.emoji))
        
        if role_name:
            role = discord.utils.get(guild.roles, name=role_name)
            if role and role in member.roles:
                await member.remove_roles(role)

async def setup(bot):
    await bot.add_cog(ChooseBatch(bot))