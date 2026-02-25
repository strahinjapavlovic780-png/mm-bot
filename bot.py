import discord
from discord.ext import commands
from discord import app_commands
import os

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
@bot.command()
async def mmpanel(ctx):
    embed = discord.Embed(
        title="Middleman Service",
        description=(
            "Welcome to our middleman service centre.\n\n"
            "At **Trade Market**, we provide a safe and secure way to exchange "
            "your goods, whether it's in-game items, crypto or digital assets.\n\n"
            "Our trusted middleman team ensures that both parties receive "
            "exactly what they agreed upon with **zero risk of scams**.\n\n"
            "**If you've found a trade and want to ensure your safety, "
            "you can use our FREE middleman service by following the steps below.**\n\n"
            "*Note: Large trades may include a small service fee.*"
        ),
        color=discord.Color.purple()
    )

    embed.add_field(
        name="📌 Usage Conditions",
        value=(
            "• Find someone to trade with.\n"
            "• Agree on the trade terms.\n"
            "• Click the button below to request a middleman.\n"
            "• Wait for a staff member to assist you."
        ),
        inline=False
    )

    embed.set_footer(text="Trade Market • Trusted Middleman Service")

    await ctx.send(embed=embed, view=MMPanel())
class MMSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="In Game Items", description="Trade involving in-game items"),
            discord.SelectOption(label="Crypto", description="Cryptocurrency trade"),
            discord.SelectOption(label="PayPal", description="PayPal transaction"),
            discord.SelectOption(label="Other", description="Other type of trade")
        ]

        super().__init__(
            placeholder="Select trade type...",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        category = discord.utils.get(guild.categories, name="MM Tickets")

        if not category:
            category = await guild.create_category("MM Tickets")

        trade_type = self.values[0]

        channel = await guild.create_text_channel(
            name=f"mm-{interaction.user.name}",
            category=category
        )

        await channel.send(
            f"{interaction.user.mention} requested MM\n\n"
            f"**Trade Type:** {trade_type}\n"
            f"Please wait for a staff member."
        )

        await interaction.response.send_message(
            f"MM ticket created for **{trade_type}**!",
            ephemeral=True
        )


class MMPanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(MMSelect())
class MMModal(discord.ui.Modal, title="MM Trade Information"):

    other_user = discord.ui.TextInput(
        label="Username of other user",
        placeholder="Enter their Discord username",
        required=True,
        max_length=100
    )

    trade_details = discord.ui.TextInput(
        label="What is the trade?",
        placeholder="Describe the trade",
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=500
    )

    agreement = discord.ui.TextInput(
        label="Did you both agree to the trade?",
        placeholder="Yes / No",
        required=True,
        max_length=10
    )

    def __init__(self, trade_type):
        super().__init__()
        self.trade_type = trade_type

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        category = discord.utils.get(guild.categories, name="MM Tickets")

        if not category:
            category = await guild.create_category("MM Tickets")

        channel = await guild.create_text_channel(
            name=f"mm-{interaction.user.name}",
            category=category
        )

        embed = discord.Embed(
            title="New MM Request",
            color=discord.Color.purple()
        )

        embed.add_field(name="Trade Type", value=self.trade_type, inline=False)
        embed.add_field(name="Other User", value=self.other_user.value, inline=False)
        embed.add_field(name="Trade Details", value=self.trade_details.value, inline=False)
        embed.add_field(name="Agreement", value=self.agreement.value, inline=False)

        await channel.send(interaction.user.mention, embed=embed)
        await interaction.response.send_message("MM ticket created!", ephemeral=True)


class MMSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="In Game Items"),
            discord.SelectOption(label="Crypto"),
            discord.SelectOption(label="PayPal"),
            discord.SelectOption(label="Other")
        ]

        super().__init__(
            placeholder="Select trade type...",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(
            MMModal(self.

class MMPanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(MMSelect())

import discord
from discord.ext import commands
import os

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Store claimed tickets
claimed_tickets = {}

# ------------------ BUTTONS ------------------

class ClaimButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="Claim",
            style=discord.ButtonStyle.green,
            custom_id="claim_button"
        )

    async def callback(self, interaction: discord.Interaction):
        channel = interaction.channel
        user = interaction.user

        if channel.id in claimed_tickets:
            await interaction.response.send_message(
                "This ticket is already claimed.",
                ephemeral=True
            )
            return

        claimed_tickets[channel.id] = user.id

        await interaction.response.send_message(
            f"{user.mention} has claimed this ticket.",
            ephemeral=False
        )


class UnclaimButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="Unclaim",
            style=discord.ButtonStyle.red,
            custom_id="unclaim_button"
        )

    async def callback(self, interaction: discord.Interaction):
        channel = interaction.channel
        user = interaction.user

        if channel.id not in claimed_tickets:
            await interaction.response.send_message(
                "This ticket is not claimed.",
                ephemeral=True
            )
            return

        if claimed_tickets[channel.id] != user.id:
            await interaction.response.send_message(
                "You are not the one who claimed this ticket.",
                ephemeral=True
            )
            return

        del claimed_tickets[channel.id]

        await interaction.response.send_message(
            "Ticket has been unclaimed.",
            ephemeral=False
        )

# ------------------ VIEW ------------------

class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(ClaimButton())
        self.add_item(UnclaimButton())

# ------------------ TEST COMMAND ------------------

@bot.command()
async def ticket(ctx):
    await ctx.send(
        "Ticket Controls:",
        view=TicketView()
    )

# ------------------ READY EVENT ------------------

@bot.event
async def on_ready():
    bot.add_view(TicketView())
    print(f"Bot is online as {bot.user}")

bot.run(os.getenv("TOKEN"))
