import discord
from discord.ext import commands
import os

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
            interaction.user: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True
            ),
        }

        if mm_role:
            overwrites[mm_role] = discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True
            )

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

# ================= CLAIM / UNCLAIM =================

@bot.command()
async def claim(ctx):
    if MM_ROLE_ID not in [role.id for role in ctx.author.roles]:
        await ctx.send("Only MM team can claim tickets.")
        return
    await ctx.send(f"🔒 {ctx.author.mention} claimed this ticket.")


@bot.command()
async def unclaim(ctx):
    if MM_ROLE_ID not in [role.id for role in ctx.author.roles]:
        await ctx.send("Only MM team can unclaim tickets.")
        return
    await ctx.send(f"{ctx.author.mention} unclaimed this ticket.")


# ================= HOW MM WORKS =================

@bot.command()
async def howmmworks(ctx):

    embed = discord.Embed(
        title="How a Middleman Works",
        description="A middleman is a trusted third party member who helps ensure both sides of a trade goes as smoothly as possible.",
        color=discord.Color.blue()
    )

    embed.add_field(
        name="Step 1",
        value="Seller gives the item to the middleman.",
        inline=False
    )

    embed.add_field(
        name="Step 2",
        value="Buyer sends the payment.",
        inline=False
    )

    embed.add_field(
        name="Step 3",
        value="Middleman releases the item to the buyer.",
        inline=False
    )

    file = discord.File("mm.png", filename="mm.png")
    embed.set_image(url="attachment://mm.png")

    await ctx.send(embed=embed, file=file)


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
            "• Sufficient proof (screenshots or recordings) must be submitted.\n\n"
            "**This policy ensures that all trades conducted through our official system are fully protected.**"
        ),
        inline=False
    )

    embed.set_footer(text="TradeMarket | Middleman Service")

    await ctx.send(embed=embed)


# ================= CONFIRM SYSTEM =================

class ConfirmView(discord.ui.View):
    def __init__(self, user1, user2):
        super().__init__(timeout=None)
        self.user1 = user1
        self.user2 = user2
        self.confirmed = []

    @discord.ui.button(label="Confirm Trade", style=discord.ButtonStyle.green)
    async def confirm_button(self, interaction: discord.Interaction, button: discord.ui.Button):

        if interaction.user not in [self.user1, self.user2]:
            await interaction.response.send_message("You are not part of this trade.", ephemeral=True)
            return

        if interaction.user in self.confirmed:
            await interaction.response.send_message("You already confirmed.", ephemeral=True)
            return

        self.confirmed.append(interaction.user)
        await interaction.response.send_message("You confirmed the trade.", ephemeral=True)

        if len(self.confirmed) == 2:
            await interaction.channel.send(
                f"✅ {self.user1.mention} {self.user2.mention} have confirmed the trade!"
            )


@bot.command()
async def confirm(ctx, user1: discord.Member, user2: discord.Member):
    await ctx.send(
        "Both users must click to confirm the trade.",
        view=ConfirmView(user1, user2)
    )

# ================= FEE SYSTEM (UPGRADED) =================

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
        await interaction.response.send_message("You selected to pay 50%.", ephemeral=True)

        if len(self.split_users) == 2:
            user1 = self.split_users[0]
            user2 = self.split_users[1]

            await interaction.channel.send(
                f"💰 {user1.mention} {user2.mention} will pay 50% of the fee each."
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

        await interaction.response.send_message("You selected to pay 100%.", ephemeral=True)

        await interaction.channel.send(
            f"💰 {interaction.user.mention} will pay 100% of the fees."
        )

        for item in self.children:
            item.disabled = True
        await interaction.message.edit(view=self)


@bot.command()
async def fee(ctx):

    embed = discord.Embed(
        title="Trade Fee Agreement",
        description=(
            "To proceed with the middleman service, both parties must agree on how the service fee will be handled.\n\n"
            "**Fee Options:**\n"
            "• 50% / 50% – Both users split the fee equally.\n"
            "• One Pays 100% – One user covers the full service fee.\n\n"
            "⚠ The trade will not proceed until a fee option is selected.\n"
            "⚠ Once selected, the decision cannot be changed.\n\n"
            "This ensures transparency and prevents disputes during the trade."
        ),
        color=discord.Color.gold()
    )

    embed.add_field(
        name="Why is there a fee?",
        value=(
            "The fee ensures the safety of both traders and compensates the middleman "
            "for handling assets securely and professionally."
        ),
        inline=False
    )

    embed.set_footer(text="TradeMarket | Official Middleman System")

    file = discord.File("fee.png", filename="fee.png")
    embed.set_image(url="attachment://fee.png")

    await ctx.send(embed=embed, file=file, view=FeeView())


bot.run(os.environ["TOKEN"])