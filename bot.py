import discord
from discord.ext import commands
import os

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

CATEGORY_NAME = "MM TICKETS"
STAFF_ROLE_NAME = "Staff"  # promeni ako ti se role zove drugačije


# ================= PANEL VIEW =================

class MMSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="In Game Items"),
            discord.SelectOption(label="Crypto"),
            discord.SelectOption(label="Paypal"),
        ]

        super().__init__(
            placeholder="Select trade type",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(MMModal(self.values[0]))


class MMView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(MMSelect())


# ================= MODAL =================

class MMModal(discord.ui.Modal):
    def __init__(self, trade_type):
        super().__init__(title="Middleman Request")
        self.trade_type = trade_type

        self.other_user = discord.ui.TextInput(label="Other User")
        self.trade_details = discord.ui.TextInput(
            label="Trade Details",
            style=discord.TextStyle.paragraph
        )
        self.agreement = discord.ui.TextInput(label="Did both agree?")

        self.add_item(self.other_user)
        self.add_item(self.trade_details)
        self.add_item(self.agreement)

    async def on_submit(self, interaction: discord.Interaction):

        guild = interaction.guild

        # CREATE / GET CATEGORY
        category = discord.utils.get(guild.categories, name=CATEGORY_NAME)
        if category is None:
            category = await guild.create_category(CATEGORY_NAME)

        staff_role = discord.utils.get(guild.roles, name=STAFF_ROLE_NAME)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }

        if staff_role:
            overwrites[staff_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

        # CREATE CHANNEL
        channel = await guild.create_text_channel(
            name=f"mm-{interaction.user.name}",
            category=category,
            overwrites=overwrites
        )

        embed = discord.Embed(
            title="New Middleman Ticket",
            color=discord.Color.purple()
        )

        embed.add_field(name="Trade Type", value=self.trade_type, inline=False)
        embed.add_field(name="Other User", value=self.other_user.value, inline=False)
        embed.add_field(name="Trade Details", value=self.trade_details.value, inline=False)
        embed.add_field(name="Agreement", value=self.agreement.value, inline=False)

        embed.set_footer(text="Trade Market • Trusted MM Service")

        await channel.send(
            content=f"{interaction.user.mention}",
            embed=embed,
            view=TicketButtons()
        )

        await interaction.response.send_message(
            f"Your ticket has been created: {channel.mention}",
            ephemeral=True
        )


# ================= CLAIM SYSTEM =================

class TicketButtons(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.claimer = None

    @discord.ui.button(label="Claim", style=discord.ButtonStyle.green)
    async def claim(self, interaction: discord.Interaction, button: discord.ui.Button):

        if self.claimer:
            await interaction.response.send_message("Already claimed.", ephemeral=True)
            return

        self.claimer = interaction.user
        button.disabled = True

        await interaction.response.edit_message(view=self)
        await interaction.channel.send(f"{interaction.user.mention} claimed this ticket.")

    @discord.ui.button(label="Unclaim", style=discord.ButtonStyle.red)
    async def unclaim(self, interaction: discord.Interaction, button: discord.ui.Button):

        if interaction.user != self.claimer:
            await interaction.response.send_message("You didn't claim this.", ephemeral=True)
            return

        self.claimer = None

        for item in self.children:
            if item.label == "Claim":
                item.disabled = False

        await interaction.response.edit_message(view=self)
        await interaction.channel.send(f"{interaction.user.mention} unclaimed this ticket.")


# ================= PANEL COMMAND =================

@bot.command()
async def panel(ctx):

    embed = discord.Embed(
        title="Middleman Service",
        description=(
            "Welcome to our middleman service centre.\n\n"
            "At **Trade Market**, we provide a safe and secure way to exchange your goods, "
            "whether it's in-game items, crypto or digital assets.\n\n"
            "Our trusted middleman team ensures that both parties receive exactly what they agreed upon "
            "with **zero risk of scams**.\n\n"
            "**If you've found a trade and want to ensure your safety, "
            "you can use our FREE middleman service by following the steps below.**\n\n"
            "*Note: Large trades may include a small service fee.*\n\n"
            "📌 **Usage Conditions**\n"
            "• Find someone to trade with.\n"
            "• Agree on the trade terms.\n"
            "• Select trade type below.\n"
            "• Wait for a staff member to assist you.\n\n"
            "**Trade Market • Trusted Middleman Service**"
        ),
        color=discord.Color.purple()
    )

    await ctx.send(embed=embed, view=MMView())


# ================= RUN =================

bot.run(os.environ["TOKEN"])