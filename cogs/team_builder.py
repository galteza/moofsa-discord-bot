import discord
from discord.ext import commands
import os
from supabase import create_client, Client

# Initialize the persistent cloud client using environment tokens
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

class BuildTeam(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="setup_team")
    @commands.has_permissions(administrator=True)
    async def setup_team(self, ctx, team_role: str, desc: str = None):
        """
        Usage: !setup_team "Summer Internal 26" "Planning our flagship summer event!"
        """
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            print("Bot doesn't have permission to delete messages.")

        guild = ctx.guild
        guild_id = guild.id

        # 1. AUTOMATED ROLE CREATION / FETCHING
        role = discord.utils.get(guild.roles, name=team_role)
        if not role:
            role = await guild.create_role(
                name=team_role, 
                color=discord.Color.blue(), 
                mentionable=True,
                reason=f"NUFSA Team Generation Command for {team_role}"
            )

        # 2. CHANNEL & CATEGORY SECURITY PERMISSIONS
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            role: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            
            # Upgraded Bot Permissions
            guild.me: discord.PermissionOverwrite(
                view_channel=True, 
                manage_channels=True, 
                manage_permissions=True
            )
        }

        # 3. AUTOMATED CATEGORY & CHANNELS GENERATION
        category_name = f"👥 {team_role}"
        category = await guild.create_category(name=category_name, overwrites=overwrites)

        await guild.create_text_channel(name="📢announcements", category=category)
        await guild.create_text_channel(name="💬general-chat", category=category)

        # 4. POST INTERACTIVE JOIN EMBED PANEL
        embed = discord.Embed(
            title=f"Join Team: {team_role}",
            description=(
                f"{desc}\n\n"
                "**How to Join:**\n"
                "React with ✅ below to join this organizing committee! "
                "Doing so automatically grants you the role and unlocks the private workspace category channels.\n\n"
            ),
            color=discord.Color.yellow()
        )
        
        msg = await ctx.send(embed=embed)
        await msg.add_reaction("✅")

        # 5. UPDATE PERSISTENT CLOUD DATA STORAGE (SUPABASE)
        try:
            supabase.table("discord_teams").insert({
                "message_id": str(msg.id),
                "guild_id": str(guild_id),
                "team_name": team_role,
                "role_id": role.id,
                "category_id": category.id
            }).execute()
            print(f"✅ Securely backed up team '{team_role}' tracking data to Supabase database.")
        except Exception as e:
            print(f"🚨 CLOUD SAVE FAILURE: Failed to push tracking data to Supabase: {e}")
            await ctx.send(f"⚠️ Warning: Team created but database sync failed: {e}", delete_after=10)


    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.user_id == self.bot.user.id:
            return  # Ignore the bot's own reaction setup marker

        # Query database to check if this message is an active tracking panel
        try:
            response = supabase.table("discord_teams").select("*").eq("message_id", str(payload.message_id)).execute()
            
            # If no data matches, this is just a normal chat message reaction. Ignore it.
            if not response.data:
                return
                
            stored_team = response.data[0]
            guild = self.bot.get_guild(payload.guild_id)
            member = guild.get_member(payload.user_id) or await guild.fetch_member(payload.user_id)

            if str(payload.emoji) == "✅" and not member.bot:
                role = guild.get_role(stored_team["role_id"])
                if role:
                    await member.add_roles(role)
                    print(f"➕ Assigned team role to {member.display_name} via Supabase tracking record.")
        except Exception as e:
            print(f"🚨 ERROR in on_raw_reaction_add db lookup: {e}")


    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        # Query database to check if this message is an active tracking panel
        try:
            response = supabase.table("discord_teams").select("*").eq("message_id", str(payload.message_id)).execute()
            
            if not response.data:
                return
                
            stored_team = response.data[0]
            guild = self.bot.get_guild(payload.guild_id)
            member = guild.get_member(payload.user_id) or await guild.fetch_member(payload.user_id)

            if str(payload.emoji) == "✅" and not member.bot:
                role = guild.get_role(stored_team["role_id"])
                if role and role in member.roles:
                    await member.remove_roles(role)
                    print(f"➖ Removed team role from {member.display_name} via Supabase tracking record.")
        except Exception as e:
            print(f"🚨 ERROR in on_raw_reaction_remove db lookup: {e}")

async def setup(bot):
    await bot.add_cog(BuildTeam(bot))