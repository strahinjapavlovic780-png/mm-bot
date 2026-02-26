import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


# ================= SELECT =================

class MMSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="In Game Items"),
            discord.SelectOption(label="Crypto"),
            discord.SelectOption(label="Paypal")
        ]

        super().__init__(
            placeholder="Select trade type",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        selected = self.values[0]
        await interaction.response.send_modal(MMModal(selected))


class MMView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(MMSelect())


# ================= MODAL =================

class MMModal(discord.ui.Modal):
    def __init__(self, trade_type):
        super().__init__(title="Middleman Request")
        self.trade_type = trade_type

        self.username = discord.ui.TextInput(
            label="Username of other person",
            placeholder="Enter their username",
            required=True
        )

        self.trade = discord.ui.TextInput(
            label="What is the trade?",
            placeholder="Describe the trade",
            required=True,
            style=discord.TextStyle.paragraph
        )

        self.agree = discord.ui.TextInput(
            label="Did both parties agree?",
            placeholder="Yes / No",
            required=True
        )

        self.add_item(self.username)
        self.add_item(self.trade)
        self.add_item(self.agree)

    async def on_submit(self, interaction: discord.Interaction):

        embed = discord.Embed(
            title="New Middleman Ticket",
            color=discord.Color.purple()
        )

        embed.add_field(name="Trade Type", value=self.trade_type, inline=False)
        embed.add_field(name="Other User", value=self.username.value, inline=False)
        embed.add_field(name="Trade Details", value=self.trade.value, inline=False)
        embed.add_field(name="Agreement", value=self.agree.value, inline=False)

        embed.set_footer(text="Trade Market • Trusted MM Service")

        await interaction.response.send_message(
            embed=embed,
            view=TicketButtons()
        )


# ================= CLAIM SYSTEM =================

class TicketButtons(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.claimer = None

    @discord.ui.button(label="Claim", style=discord.ButtonStyle.green)
    async def claim(self, interaction: discord.Interaction, button: discord.ui.Button):

        if self.claimer is not None:
            await interaction.response.send_message(
                "This ticket is already claimed.",
                ephemeral=True
            )
            return

        self.claimer = interaction.user
        button.disabled = True

        await interaction.response.edit_message(view=self)
        await interaction.followup.send(
            f"{interaction.user.mention} claimed this ticket."
        )

    @discord.ui.button(label="Unclaim", style=discord.ButtonStyle.red)
    async def unclaim(self, interaction: discord.Interaction, button: discord.ui.Button):

        if self.claimer != interaction.user:
            await interaction.response.send_message(
                "You didn't claim this ticket.",
                ephemeral=True
            )
            return

        self.claimer = None

        for item in self.children:
            if item.label == "Claim":
                item.disabled = False

        await interaction.response.edit_message(view=self)
        await interaction.followup.send(
            f"{interaction.user.mention} unclaimed this ticket."
        )


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


# ================= RUN BOT =================

import os
bot.run(os.environ["TOKEN"])