from typing import Any

import discord
from discord import app_commands
import dotenv
import os

partied_members: list[discord.Member] = []

# Env setup ------------------------------------------------------------------------------------------------------------
dotenv.load_dotenv()
TOKEN = str(os.getenv("TOKEN"))
GUILD = int(os.getenv("GUILD"))
ROLE_NAME = str(os.getenv("ROLE_NAME"))

# Client setup ---------------------------------------------------------------------------------------------------------
class TaskClient(discord.Client):
    def __init__(self, *, intents: discord.Intents, **options: Any) -> None:
        super().__init__(intents=intents, **options)

    async def setup_hook(self) -> None:
        pass

intents = discord.Intents.default()
client = TaskClient(intents=intents)
tree = app_commands.CommandTree(client)

# Commands -------------------------------------------------------------------------------------------------------------
@tree.command(name="online", description="Check if bot is responding", guild=discord.Object(id=GUILD))
async def online(interaction):
    await interaction.response.send_message("I'm online!")

@tree.command(name="party", description="Add a user to current session", guild=discord.Object(id=GUILD))
async def party(interaction, target: discord.Member):
    global partied_members
    role = discord.utils.get(target.guild.roles, name=ROLE_NAME)
    partied_members.append(target)
    await target.add_roles(role)
    await interaction.response.send_message(f"**[✓]** User *{target.display_name}* added to session")

@tree.command(name="endsession", description="Add a user to current session", guild=discord.Object(id=GUILD))
async def endsession(interaction):
    global partied_members
    role = discord.utils.get(interaction.guild.roles, name=ROLE_NAME)
    members = len(partied_members)
    fails = 0
    for member in partied_members:
        try:
            await member.remove_roles(role)
        except Exception as ex:
            fails += 1
            print(ex)

    if fails > 0:
        await interaction.response.send_message(f"**[!]** Session ended! ({members - fails}/{members})")
    else:
        await interaction.response.send_message(f"**[✓]** Session ended! ({members - fails}/{members})")
    partied_members = []

@tree.command(name="partykick", description="Kick a user from session", guild=discord.Object(id=GUILD))
async def kickparty(interaction, target: discord.Member):
    global partied_members
    role = discord.utils.get(interaction.guild.roles, name=ROLE_NAME)
    if target in partied_members:
        await target.remove_roles(role)
        del partied_members[partied_members.index(target)]
        await interaction.response.send_message(f"**[✓]** User {target.display_name} removed from session!")
    else:
        await interaction.response.send_message(f"**[🗙]** User {target.display_name} not in session!")

@tree.command(name="list", description="List party members", guild=discord.Object(id=GUILD))
async def listparty(interaction):
    global partied_members
    names = []
    for user in partied_members:
        names.append(user.display_name)
    await interaction.response.send_message(f"**[✓]** Listing party members: {names}")


# Events ---------------------------------------------------------------------------------------------------------------

@client.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=GUILD))
    print("Ready!")

# Tasks ----------------------------------------------------------------------------------------------------------------



client.run(TOKEN)
