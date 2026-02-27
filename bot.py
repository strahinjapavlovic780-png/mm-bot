import discord
from discord.ext import commands
import os


intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

CATEGORY_NAME = "MM TICKETS"

MEMBER_ROLE_ID = 1477044929317437574
MM_ROLE_ID = 1477044901995872296
MERCY_ROLE_ID = 1477052539445837974

# ================= STAFF CHECK =================

def is_staff(member):
    return MM_ROLE_ID in [role.id for role in member.roles]

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
            interaction.user: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True
            ),
        }

        # Dodavanje drugog usera po ID-u
        try:
            other_member = await guild.fetch_member(int(self.other_user.value))
            overwrites[other_member] = discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True
            )
        except:
            other_member = None

        if mm_role:
            overwrites[mm_role] = discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True
            )

        channel = await guild.create_text_channel(
            name=f"mm-{interaction.user.id}",
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

        await interaction.channel.set_permissions(
            self.creator,
            send_messages=False
        )

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

        await interaction.channel.set_permissions(
            self.creator,
            send_messages=True
        )

        await interaction.response.edit_message(view=self)
        await interaction.channel.send(f"{interaction.user.mention} unclaimed and unlocked the ticket.")


# ================= COMMANDS =================

@bot.command()
async def add(ctx, member: discord.Member):
    if MM_ROLE_ID not in [role.id for role in ctx.author.roles]:
        await ctx.send("Only MM team can add users.")
        return

    await ctx.channel.set_permissions(member, view_channel=True, send_messages=True)
    await ctx.send(f"{member.mention} added to ticket.")


@bot.command()
async def remove(ctx, member: discord.Member):
    if MM_ROLE_ID not in [role.id for role in ctx.author.roles]:
        await ctx.send("Only MM team can remove users.")
        return

    await ctx.channel.set_permissions(member, overwrite=None)
    await ctx.send(f"{member.mention} removed from ticket.")


@bot.command()
async def close(ctx):
    if MM_ROLE_ID not in [role.id for role in ctx.author.roles]:
        await ctx.send("Only MM team can close tickets.")
        return

    await ctx.send("Closing ticket...")
    await ctx.channel.delete()


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
            "• Click the dropdown below.\n"
            "• Wait for a staff member.\n\n"
            "**Trade Market • Trusted Middleman Service**"
        ),
        color=discord.Color.purple()
    )

    await ctx.send(embed=embed, view=MMView())


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
            "• Both traders will receive full compensation equal to their losses.\n"
            "• Compensation is provided by the Executive Team.\n"
            "• The middleman will be terminated, blacklisted, and permanently banned."
        ),
        inline=False
    )

    embed.add_field(
        name="3. Compensation Requirements",
        value=(
            "• Trade must occur inside our official Discord server.\n"
            "• The middleman must have had the MM role at the time.\n"
            "• Valid proof (screenshots/recordings) must be provided.\n\n"
            "**All official trades are fully protected under this policy.**"
        ),
        inline=False
    )

    embed.set_footer(text="TradeMarket | Protection Guaranteed")

    await ctx.send(embed=embed)




# ================= NEW CLAIM COMMAND =================

@bot.command()
async def claim(ctx):
    if MM_ROLE_ID not in [role.id for role in ctx.author.roles]:
        await ctx.send("Only MM team can claim tickets.")
        return

    await ctx.send(f"🔒 {ctx.author.mention} has claimed this ticket and is now handling this trade.")

# ================= FEE SYSTEM =================

class CustomFeeModal(discord.ui.Modal, title="Custom Fee Split"):

    split = discord.ui.TextInput(
        label="Enter split (example: 60-40)",
        placeholder="Example: 70-30",
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):

        try:
            parts = self.split.value.replace(" ", "").split("-")
            p1 = int(parts[0])
            p2 = int(parts[1])

            if p1 + p2 != 100:
                await interaction.response.send_message(
                    "Percentages must equal 100.",
                    ephemeral=True
                )
                return

        except:
            await interaction.response.send_message(
                "Invalid format. Use example: 60-40",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title=f"Middleman Fee Agreement – {p1}/{p2} Split",
            description=(
                "Both traders have agreed to split the middleman fee equally.\n\n"
                f"**User 1 will pay {p1}% of the fee.**\n"
                f"**User 2 will pay {p2}% of the fee.**\n\n"
                "This ensures fairness and equal responsibility between both parties.\n\n"
                "Once payment is completed, the middleman will proceed with the secured transaction."
            ),
            color=discord.Color.gold()
        )

        await interaction.response.send_message(embed=embed)


class FeeView(discord.ui.View):
    def __init__(self, requester):
        super().__init__(timeout=None)
        self.requester = requester

    @discord.ui.button(label="50% / 50%", style=discord.ButtonStyle.primary)
    async def split_fee(self, interaction: discord.Interaction, button: discord.ui.Button):

        embed = discord.Embed(
            title="Middleman Fee Agreement – 50/50 Split",
            description=(
                "Both traders have agreed to split the middleman fee equally.\n\n"
                "**Both users will pay 50% of the fee each.**\n\n"
                "This ensures fairness and equal responsibility between both parties.\n\n"
                "Once payment is completed, the middleman will proceed with the secured transaction."
            ),
            color=discord.Color.gold()
        )

        await interaction.response.send_message(embed=embed)

    @discord.ui.button(label="100% One User Pays", style=discord.ButtonStyle.red)
    async def full_fee(self, interaction: discord.Interaction, button: discord.ui.Button):

        embed = discord.Embed(
            title="Middleman Fee Agreement – Full Payment",
            description=(
                f"{interaction.user.mention} has agreed to cover the full middleman fee.\n\n"
                f"**{interaction.user.mention} will pay 100% of the fees to the middleman.**\n\n"
                "The second trader is not responsible for any service fee in this transaction.\n\n"
                "Once the fee is confirmed, the trade will proceed under full protection."
            ),
            color=discord.Color.red()
        )

        await interaction.response.send_message(embed=embed)

    @discord.ui.button(label="Custom Split", style=discord.ButtonStyle.secondary)
    async def custom_fee(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(CustomFeeModal())


@bot.command()
async def fee(ctx):
    embed = discord.Embed(
        title="Middleman Service Fee Confirmation",
        description=(
            "To ensure transparency and fairness, all middleman transactions may include a service fee.\n\n"
            "Please choose how the fee will be handled for this trade:\n\n"
            "🔹 **50% / 50% Split** – Both users share the fee equally.\n"
            "🔹 **100% One User Pays** – One trader covers the entire fee.\n"
            "🔹 **Custom Split** – Choose your own percentage distribution.\n\n"
            "Click one of the buttons below to confirm how the fee will be paid."
        ),
        color=discord.Color.purple()
    )

    await ctx.send(embed=embed, view=FeeView(ctx.author))


# ================= CONFIRM SYSTEM =================

@bot.command()
async def confirm(ctx, user1: discord.Member, user2: discord.Member):
    embed = discord.Embed(
        title="Official Trade Confirmation",
        description=(
            "This trade has been officially confirmed under the supervision of our Middleman Team.\n\n"
            "Both parties listed below have agreed to the full trade terms, conditions, "
            "and fee structure associated with this transaction.\n\n"
            "By confirming this trade, both users acknowledge that:\n"
            "• The trade terms are final and mutually accepted.\n"
            "• The middleman will securely hold and transfer assets.\n"
            "• Any attempt of scam or chargeback will result in permanent ban.\n\n"
            "The transaction is now protected and logged under our official policy system.\n\n"
            "**Trade Protection Status: ACTIVE ✅**"
        ),
        color=discord.Color.green()
    )

    embed.add_field(name="Trader 1", value=user1.mention, inline=False)
    embed.add_field(name="Trader 2", value=user2.mention, inline=False)
    embed.set_footer(text="TradeMarket | Secure Middleman Protection System")

    await ctx.send(embed=embed)

@bot.command()
async def help(ctx):
    embed = discord.Embed(
        title="📘 TradeMarket Bot Commands",
        description="Here is a list of all available commands:",
        color=discord.Color.purple()
    )

    embed.add_field(
        name="🎟 Ticket System",
        value=(
            "`!panel` – Sends the Middleman ticket panel\n"
            "`!close` – Closes the current ticket (MM only)\n"
            "`!add @user` – Add user to ticket (MM only)\n"
            "`!remove @user` – Remove user from ticket (MM only)"
        ),
        inline=False
    )

    embed.add_field(
        name="🔒 Claim System",
        value=(
            "`Claim Button` – Claims ticket (MM role required)\n"
            "`Unclaim Button` – Unclaims ticket"
        ),
        inline=False
    )

    embed.add_field(
        name="💰 Fee System",
        value=(
            "`!fee` – Sends fee agreement buttons\n"
            "`50/50 Button` – Split fee equally\n"
            "`100% Button` – One user pays full fee"
        ),
        inline=False
    )

    embed.add_field(
        name="✅ Trade Confirmation",
        value="`!confirm @user1 @user2` – Official trade confirmation embed",
        inline=False
    )

    embed.add_field(
        name="ℹ Information",
        value=(
            "`!howmmworks` – Explains how middleman works\n"
            "`!policy` – Shows compensation & scam policy"
        ),
        inline=False
    )

    embed.set_footer(text="TradeMarket | Official Middleman System")

    await ctx.send(embed=embed)

class MercyView(discord.ui.View):
    def __init__(self, target):
        super().__init__(timeout=None)
        self.target = target

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.green)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):

        if interaction.user != self.target:
            await interaction.response.send_message("This is not for you.", ephemeral=True)
            return

        role = interaction.guild.get_role(MERCY_ROLE_ID)
        if role:
            await interaction.user.add_roles(role)

        embed = discord.Embed(
            description=(
                f"{interaction.user.mention} has accepted the offer!\n\n"
                "**What now?**\n"
                "– Check out and read all the staff channels carefully.\n"
                "– Ask other staff for help or additional information if needed.\n\n"
                "**Welcome to the team.**"
            ),
            color=discord.Color.green()
        )

        await interaction.response.send_message(embed=embed)

    @discord.ui.button(label="Decline", style=discord.ButtonStyle.red)
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):

        if interaction.user != self.target:
            await interaction.response.send_message("This is not for you.", ephemeral=True)
            return

        embed = discord.Embed(
            description=(
                f"{interaction.user.mention} has declined the offer!\n\n"
                "**What now?**\n"
                "– Staff will determine your punishment soon.\n"
                "– You will never be able to earn back what you lost.\n\n"
                "**Bad luck, you are never going to earn anything back.**"
            ),
            color=discord.Color.red()
        )

        await interaction.response.send_message(embed=embed)

@bot.command()
async def mercy(ctx, member: discord.Member):

    if not is_staff(ctx.author):
        await ctx.send("Only Mercy Team can use this command.")
        return

    # 🔹 Manji embed (gornji)
    small_embed = discord.Embed(
        description=f"{member.mention} has received a staff offer!",
        color=discord.Color.blue()
    )

    # 🔹 Veći embed (glavni)
    big_embed = discord.Embed(
        title="Staff Offer",
        description=(
            "You have been offered a position.\n\n"
            "**What now?**\n"
            "– Accept if you agree to join.\n"
            "– Decline if you are not interested.\n\n"
            "Please choose below."
        ),
        color=discord.Color.purple()
    )

    await ctx.send(embed=small_embed)
    await ctx.send(embed=big_embed, view=MercyView(member))
                
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

    # Persistent views (da dugmad rade i posle restarta)
    bot.add_view(MMView())
    bot.add_view(TicketButtons(None))
    bot.add_view(FeeView(None))

token = os.getenv("TOKEN")

if not token:
    raise ValueError("TOKEN environment variable is not set.")

bot.run(token)