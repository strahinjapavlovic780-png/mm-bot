import discord
from discord.ext import commands
from discord import app_commands
import os

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

class MMPanel(discord.ui.View):
    @discord.ui.button(label="Request MM", style=discord.ButtonStyle.green)
    async def request_mm(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        
        category = discord.utils.get(guild.categories, name="MM Tickets")
        if not category:
            category = await guild.create_category("MM Tickets")

        channel = await guild.create_text_channel(
            name=f"mm-{interaction.user.name}",
            category=category
        )

        await channel.send(f"{interaction.user.mention} MM request created.")
        await interaction.response.send_message("MM ticket created!", ephemeral=True)

@bot.command()
async def mmpanel(ctx):
    embed = discord.Embed(
        title="MM Request Panel",
        description="Click the button below to request a middleman."
    )
    await ctx.send(embed=embed, view=MMPanel())

@bot.event
async def on_ready():
    print(f"Bot is online as {bot.user}")

bot.run(os.getenv("TOKEN"))
