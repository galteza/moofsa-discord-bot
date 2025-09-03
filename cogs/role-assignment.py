import discord
from discord.ext import commands

role_choices = ["Team A", "Team B", "Team C", "Team D"]

class RoleAssigner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def roles(self, ctx):
        """Shows a dropdown for choosing a role."""
        options = [discord.SelectOption(label=role) for role in role_choices]

        view = discord.ui.View()
        select = discord.ui.Select(placeholder="Choose your role!", options=options)

        async def callback(interaction):
            chosen_role = discord.utils.get(ctx.guild.roles, name=interaction.data['values'][0])
            if chosen_role:
                await interaction.user.add_roles(chosen_role)
                await interaction.response.send_message(
                    f"You have been assigned to **{chosen_role.name}** ✅",
                    ephemeral=True
                )

        select.callback = callback
        view.add_item(select)
        await ctx.send("Select your role:", view=view)

def setup(bot):
    bot.add_cog(RoleAssigner(bot))
