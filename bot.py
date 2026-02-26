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


bot.run(os.environ["TOKEN"])