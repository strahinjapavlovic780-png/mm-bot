import discord
from discord.ext import commands
import os
from flask import Flask
from threading import Thread

# ================= DISCORD SETUP =================

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

CATEGORY_NAME = "MM TICKETS"

MEMBER_ROLE_ID = 1476607658323607553
MM_ROLE_ID = 1476607505365864488

# ================= PANEL SELECT =================

class MMSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="In Game Items"),
            discord.SelectOption(label="Crypto"),
            discord.SelectOption(label="Paypal"),
        ]

        super().__init__(
            placeholder="Select trade type below",
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

        category = discord.utils.get(guild.categories, name=CATEGORY_NAME)
        if category is None:
            category = await guild.create_category(CATEGORY_NAME)

        mm_role = guild.get_role(MM_ROLE_ID)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
        }

        if mm_role:
            overwrites[mm_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

        channel = await guild.create_text_channel(
            name=f"mm-{interaction.user.name}",
            category=category,
            overwrites=overwrites
        )

        ticket_embed = discord.Embed(
            title="New Middleman Ticket",
            color=discord.Color.purple()
        )

        ticket_embed.add_field(name="Trade Type", value=self.trade_type, inline=False)
        ticket_embed.add_field(name="Other User", value=self.other_user.value, inline=False)
        ticket_embed.add_field(name="Trade Details", value=self.trade_details.value, inline=False)
        ticket_embed.add_field(name="Agreement", value=self.agreement.value, inline=False)

        await channel.send(
            content=f"{interaction.user.mention}",
            embed=ticket_embed,
            view=TicketButtons(interaction.user)
        )

        await interaction.response.send_message(
            f"Your ticket has been created: {channel.mention}",
            ephemeral=True
        )

# ================= CLAIM SYSTEM =================

class TicketButtons(discord.ui.View):
    def __init__(self, creator):
        super().__init__(timeout=None)
        self.claimer = None
        self.creator = creator

    @discord.ui.button(label="Claim", style=discord.ButtonStyle.green)
    async def claim(self, interaction: discord.Interaction, button: discord.ui.Button):

        if MM_ROLE_ID not in [role.id for role in interaction.user.roles]:
            await interaction.response.send_message("Only MM team can claim.", ephemeral=True)
            return

        if self.claimer:
            await interaction.response.send_message("Already claimed.", ephemeral=True)
            return

        self.claimer = interaction.user
        button.disabled = True

        await interaction.channel.set_permissions(self.creator, send_messages=False)

        await interaction.response.edit_message(view=self)
        await interaction.channel.send(f"🔒 {interaction.user.mention} claimed and locked this ticket.")

    @discord.ui.button(label="Unclaim", style=discord.ButtonStyle.red)
    async def unclaim(self, interaction: discord.Interaction, button: discord.ui.Button):

        if MM_ROLE_ID not in [role.id for role in interaction.user.roles]:
            await interaction.response.send_message("Only MM team can unclaim.", ephemeral=True)
            return

        if interaction.user != self.claimer:
            await interaction.response.send_message("You didn't claim this.", ephemeral=True)
            return

        self.claimer = None

        for item in self.children:
            if item.label == "Claim":
                item.disabled = False

        await interaction.channel.set_permissions(self.creator, send_messages=True)

        await interaction.response.edit_message(view=self)
        await interaction.channel.send(f"{interaction.user.mention} unclaimed and unlocked the ticket.")

# ================= MMPANEL =================

@bot.command()
async def mmpanel(ctx):

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
            "• Click the dropdown below.\n"
            "• Wait for a staff member.\n\n"
            "**Trade Market • Trusted Middleman Service**"
        ),
        color=discord.Color.purple()
    )

    await ctx.send(embed=embed, view=MMView())

# ================= POLICY =================

@bot.command()
async def policy(ctx):

    embed = discord.Embed(
        title="Middleman Accountability & Compensation Policy",
        color=discord.Color.blue()
    )

    embed.add_field(
        name="1. Middleman Responsibility",
        value=(
            "Official middlemen must remain neutral and handle all assets fairly. "
            "Any misuse of authority or failure to return items is considered internal fraud."
        ),
        inline=False
    )

    embed.add_field(
        name="2. If a Middleman Scams",
        value=(
            "• Both traders involved will receive full compensation equal to their losses.\n"
            "• Compensation will be provided by the Executive Team.\n"
            "• The middleman will be terminated from our MM team, blacklisted, and banned."
        ),
        inline=False
    )

    embed.add_field(
        name="3. Compensation Requirements",
        value=(
            "• Trade must have taken place within our Official Discord MM Server.\n"
            "• The middleman must have held the MM role at the time.\n"
            "• Sufficient proof (screenshots or recordings) must be submitted."
        ),
        inline=False
    )

    embed.set_footer(text="TradeMarket | Middleman Service")

    await ctx.send(embed=embed)

# ================= HOW MM WORKS =================

@bot.command()
async def howmmworks(ctx):

    embed = discord.Embed(
        title="How a Middleman Works",
        description=(
            "A middleman is a trusted third party who ensures both sides of a trade "
            "are protected and that the transaction is completed safely.\n\n"
            "**Step 1:** Seller gives the item to the middleman.\n"
            "**Step 2:** Buyer sends the payment.\n"
            "**Step 3:** Middleman verifies payment and releases the item.\n\n"
            "This process protects both parties from scams and fraud."
        ),
        color=discord.Color.blue()
    )

    embed.set_footer(text="TradeMarket | Official Middleman System")

    await ctx.send(embed=embed)

# ================= FEE =================

class FeeView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.split_users = []
        self.full_paid = False

    @discord.ui.button(label="50% / 50%", style=discord.ButtonStyle.blurple)
    async def split_fee(self, interaction: discord.Interaction, button: discord.ui.Button):

        if interaction.user in self.split_users:
            await interaction.response.send_message("You already selected 50%.", ephemeral=True)
            return

        if self.full_paid:
            await interaction.response.send_message("100% option already selected.", ephemeral=True)
            return

        self.split_users.append(interaction.user)
        await interaction.response.send_message("You selected to split the fee (50%).", ephemeral=True)

        if len(self.split_users) == 2:
            user1 = self.split_users[0]
            user2 = self.split_users[1]

            await interaction.channel.send(
                f"💰 {user1.mention} and {user2.mention} will each pay 50% of the service fee."
            )

            for item in self.children:
                item.disabled = True
            await interaction.message.edit(view=self)

    @discord.ui.button(label="One Pays 100%", style=discord.ButtonStyle.red)
    async def full_fee(self, interaction: discord.Interaction, button: discord.ui.Button):

        if self.full_paid:
            await interaction.response.send_message("Fee option already selected.", ephemeral=True)
            return

        self.full_paid = True

        await interaction.response.send_message("You selected to pay 100% of the fee.", ephemeral=True)

        await interaction.channel.send(
            f"💰 {interaction.user.mention} will pay 100% of the service fee."
        )

        for item in self.children:
            item.disabled = True
        await interaction.message.edit(view=self)


@bot.command()
async def fee(ctx):

    embed = discord.Embed(
        title="Trade Fee Agreement",
        description=(
            "Before the trade proceeds, both parties must agree on how the service fee will be handled.\n\n"
            "**Available Options:**\n"
            "• 50% / 50% — Both users split the fee equally.\n"
            "• One Pays 100% — One user covers the full service fee.\n\n"
            "⚠ The trade cannot proceed until a fee option is selected.\n"
            "⚠ Once selected, the decision is final.\n\n"
            "This ensures transparency and prevents disputes."
        ),
        color=discord.Color.gold()
    )

    embed.add_field(
        name="Why do we charge a fee?",
        value=(
            "The service fee compensates the middleman for securely holding assets, "
            "verifying payments, and protecting both traders from scams."
        ),
        inline=False
    )

    embed.set_footer(text="TradeMarket | Secure & Professional")

    await ctx.send(embed=embed, view=FeeView())

# ================= RENDER KEEP ALIVE =================

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

def keep_alive():
    thread = Thread(target=run_web)
    thread.daemon = True
    thread.start()

token = os.getenv("TOKEN")

if not token:
    raise ValueError("TOKEN environment variable is not set.")

keep_alive()
bot.run(token)