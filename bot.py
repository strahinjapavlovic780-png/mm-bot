# ============================================================
#                    FULL ADVANCED MM BOT
#                  550+ LINES PROFESSIONAL
# ============================================================

import discord
from discord.ext import commands
import os
import json
from flask import Flask
from threading import Thread
from datetime import datetime

# ============================================================
#                         CONFIG
# ============================================================

TOKEN = os.getenv("TOKEN")

CATEGORY_NAME = "MM TICKETS"
LOG_CHANNEL_NAME = "mm-logs"

MEMBER_ROLE_ID = 1476607658323607553
MM_ROLE_ID = 1476607505365864488

DATABASE_FILE = "database.json"

# ============================================================
#                       DATABASE SYSTEM
# ============================================================

def load_data():
    if not os.path.exists(DATABASE_FILE):
        with open(DATABASE_FILE, "w") as f:
            json.dump({
                "blacklist": [],
                "mm_stats": {},
                "ticket_count": 0
            }, f)
    with open(DATABASE_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATABASE_FILE, "w") as f:
        json.dump(data, f, indent=4)

data = load_data()

# ============================================================
#                      BOT INITIALIZATION
# ============================================================

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# ============================================================
#                        READY EVENT
# ============================================================

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    bot.add_view(TicketButtons())
    bot.add_view(FeeView())
    bot.add_view(CloseConfirmView())
    print("Persistent views loaded.")

# ============================================================
#                        ERROR HANDLER
# ============================================================

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You do not have permission to use this command.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ Missing required argument.")
    else:
        await ctx.send("❌ An error occurred.")
        raise error

# ============================================================
#                       TICKET PANEL
# ============================================================

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

        if interaction.user.id in data["blacklist"]:
            await interaction.response.send_message(
                "❌ You are blacklisted from using this service.",
                ephemeral=True
            )
            return

        await interaction.response.send_modal(MMModal(self.values[0]))

class MMView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(MMSelect())

# ============================================================
#                          MODAL
# ============================================================

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

        data["ticket_count"] += 1
        save_data(data)

        channel = await guild.create_text_channel(
            name=f"mm-{data['ticket_count']}",
            category=category
        )

        embed = discord.Embed(
            title="New Middleman Ticket",
            color=discord.Color.purple()
        )

        embed.add_field(name="Trade Type", value=self.trade_type, inline=False)
        embed.add_field(name="Other User", value=self.other_user.value, inline=False)
        embed.add_field(name="Trade Details", value=self.trade_details.value, inline=False)
        embed.add_field(name="Agreement", value=self.agreement.value, inline=False)
        embed.timestamp = datetime.utcnow()

        await channel.send(
            content=f"{interaction.user.mention} <@&{MM_ROLE_ID}>",
            embed=embed,
            view=TicketButtons()
        )

        await interaction.response.send_message(
            f"✅ Your ticket has been created: {channel.mention}",
            ephemeral=True
        )

# ============================================================
#                       CLAIM SYSTEM
# ============================================================

class TicketButtons(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.claimer = None

    @discord.ui.button(label="Claim", style=discord.ButtonStyle.green)
    async def claim(self, interaction: discord.Interaction, button: discord.ui.Button):

        if MM_ROLE_ID not in [role.id for role in interaction.user.roles]:
            await interaction.response.send_message("❌ Only MM team can claim.", ephemeral=True)
            return

        if self.claimer:
            await interaction.response.send_message("❌ Already claimed.", ephemeral=True)
            return

        self.claimer = interaction.user
        button.disabled = True

        stats = data["mm_stats"]
        stats[str(interaction.user.id)] = stats.get(str(interaction.user.id), 0) + 1
        save_data(data)

        await interaction.response.edit_message(view=self)
        await interaction.channel.send(f"🔒 **{interaction.user.mention} claimed this ticket.**")

    @discord.ui.button(label="Unclaim", style=discord.ButtonStyle.red)
    async def unclaim(self, interaction: discord.Interaction, button: discord.ui.Button):

        if interaction.user != self.claimer:
            await interaction.response.send_message("❌ You didn't claim this.", ephemeral=True)
            return

        self.claimer = None

        for item in self.children:
            if item.label == "Claim":
                item.disabled = False

        await interaction.response.edit_message(view=self)
        await interaction.channel.send("🔓 **Ticket unlocked.**")

# ============================================================
#                       CLOSE SYSTEM
# ============================================================

class CloseConfirmView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)

    @discord.ui.button(label="Confirm Close", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):

        log_channel = discord.utils.get(interaction.guild.text_channels, name=LOG_CHANNEL_NAME)
        if log_channel:
            await log_channel.send(f"🗑 Ticket {interaction.channel.name} closed by {interaction.user.mention}")

        await interaction.channel.delete()

@bot.command()
async def close(ctx):
    await ctx.send(
        "**Are you sure you want to close this ticket?**",
        view=CloseConfirmView()
    )

# ============================================================
#                       BLACKLIST SYSTEM
# ============================================================

@bot.command()
@commands.has_permissions(administrator=True)
async def blacklist(ctx, member: discord.Member):
    if member.id in data["blacklist"]:
        await ctx.send("User already blacklisted.")
        return
    data["blacklist"].append(member.id)
    save_data(data)
    await ctx.send(f"🚫 **{member.mention} has been blacklisted.**")

@bot.command()
@commands.has_permissions(administrator=True)
async def unblacklist(ctx, member: discord.Member):
    if member.id not in data["blacklist"]:
        await ctx.send("User not blacklisted.")
        return
    data["blacklist"].remove(member.id)
    save_data(data)
    await ctx.send(f"✅ **{member.mention} removed from blacklist.**")

# ============================================================
#                       MM STATS
# ============================================================

@bot.command()
async def mmstats(ctx):

    if not data["mm_stats"]:
        await ctx.send("No stats yet.")
        return

    embed = discord.Embed(
        title="MM Claim Statistics",
        color=discord.Color.gold()
    )

    sorted_stats = sorted(data["mm_stats"].items(), key=lambda x: x[1], reverse=True)

    for user_id, count in sorted_stats:
        user = await bot.fetch_user(int(user_id))
        embed.add_field(name=user.name, value=f"Claims: **{count}**", inline=False)

    await ctx.send(embed=embed)

# ============================================================
#                   ORIGINAL TEXT COMMANDS
# ============================================================

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

# ============================================================
#                     FEE SYSTEM
# ============================================================

class FeeView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="50% / 50%", style=discord.ButtonStyle.blurple)
    async def split(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Both users will split the fee.", ephemeral=True)

    @discord.ui.button(label="One Pays 100%", style=discord.ButtonStyle.red)
    async def full(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("One user will pay full fee.", ephemeral=True)

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

# ============================================================
#                  RENDER KEEP ALIVE
# ============================================================

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running"

def run():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

Thread(target=run).start()

# ============================================================
#                        START BOT
# ============================================================

bot.run(TOKEN)