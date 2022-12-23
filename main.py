from typing import Any

import discord
from discord import app_commands
import dotenv
import os
import datetime

from discord.ext import tasks

import externals
import subprocess

partied_members: list[discord.Member] = []
VERSION = 6

# Env setup ------------------------------------------------------------------------------------------------------------
dotenv.load_dotenv()
TOKEN = str(os.getenv("TOKEN"))
GUILD = int(os.getenv("GUILD"))
ROLE_NAME = str(os.getenv("ROLE_NAME"))
QUEUE_CHANNEL = int(os.getenv("QUEUE_CHANNEL"))
MAIN_CHANNEL = int(os.getenv("MAIN_CHANNEL"))
DEVELOPMENT = int(os.getenv("DEVELOPMENT"))

# Client setup ---------------------------------------------------------------------------------------------------------
class TaskClient(discord.Client):
    def __init__(self, *, intents: discord.Intents, **options: Any) -> None:
        super().__init__(intents=intents, **options)

    async def setup_hook(self) -> None:
        task_refreshvc.start()

intents = discord.Intents.default()
client = TaskClient(intents=intents)
tree = app_commands.CommandTree(client)

# Commands -------------------------------------------------------------------------------------------------------------
@tree.command(name="online", description="Check if bot is responding", guild=discord.Object(id=GUILD))
async def online(interaction):
    await interaction.response.send_message("I'm online!")

@tree.command(name="party", description="Add a user to current session", guild=discord.Object(id=GUILD))
async def party(interaction: discord.Interaction, target: discord.Member):
    global partied_members
    role = discord.utils.get(target.guild.roles, name=ROLE_NAME)
    channel = interaction.guild.get_channel(QUEUE_CHANNEL)
    partied_members.append(target)
    if target.voice is not None:
        if target.voice.channel.name == channel.name:
            await target.move_to(interaction.guild.get_channel(MAIN_CHANNEL))
    await target.add_roles(role)
    await interaction.response.send_message(f"**[✓]** User *{target.display_name}* added to session")

@tree.command(name="endsession", description="Add a user to current session", guild=discord.Object(id=GUILD))
async def endsession(interaction):
    global partied_members
    role = discord.utils.get(interaction.guild.roles, name=ROLE_NAME)
    members = len(partied_members)
    channel = interaction.guild.get_channel(MAIN_CHANNEL)
    fails = 0
    for member in partied_members:
        try:
            await member.remove_roles(role)
            if member.voice is not None:
                if member.voice.channel.name == channel.name:
                    await member.move_to(interaction.guild.get_channel(QUEUE_CHANNEL))
        except Exception as ex:
            fails += 1
            print(ex)

    if fails > 0:
        await interaction.response.send_message(f"**[!]** Session ended! ({members - fails}/{members})")
    else:
        await interaction.response.send_message(f"**[✓]** Session ended! ({members - fails}/{members})")
    partied_members = []

@tree.command(name="refreshvc", description="Moves users to their proper VC", guild=discord.Object(id=GUILD))
async def refreshvc(interaction):
    channel = interaction.guild.get_channel(QUEUE_CHANNEL)
    for member in partied_members:
        try:
            if member.voice is not None:
                if member.voice.channel.name == channel.name:
                    await member.move_to(interaction.guild.get_channel(MAIN_CHANNEL))
        except Exception as ex:
            pass

@tree.command(name="partykick", description="Kick a user from session", guild=discord.Object(id=GUILD))
async def kickparty(interaction, target: discord.Member):
    global partied_members
    role = discord.utils.get(interaction.guild.roles, name=ROLE_NAME)
    channel = interaction.guild.get_channel(MAIN_CHANNEL)
    if target in partied_members:
        if target.voice is not None:
            if target.voice.channel.name == channel.name:
                await target.move_to(interaction.guild.get_channel(QUEUE_CHANNEL))
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

@tree.command(name="predict2023", description="Predicts a players stats by the end of 2023", guild=discord.Object(id=GUILD))
async def predict2023(interaction, player: str, days_back: int, fkills: int, fdeaths: int, stars: float,
                      current_fkills: int, current_fdeaths: int, current_stars: int):
    fkdr_current = round(current_fkills / current_fdeaths, 2)
    predicted_stars, predicted_finals, predicted_fdeaths, predicted_fkdr = externals.predict_stats(days_back, fkills, fdeaths, stars, current_fkills, current_fdeaths, current_stars)
    fkdr_change = round(predicted_fkdr - fkdr_current, 2)

    await interaction.response.send_message(f"**[✓]** **{player}** is predicted to have the following stats by 2023/12/30 based on the last **{days_back}** days:\n"
                                            f"Stars: **[{predicted_stars}✫]**"
                                            f" ({externals.change_character(current_stars, after=predicted_stars)}"
                                            f"{round(predicted_stars-current_stars, 2)}✫)\n"
                                            f"FKDR: **{predicted_fkdr}** ({externals.change_character(change=fkdr_change)}{fkdr_change} fkdr)")

@tree.command(name="predictstats", description="Predicts a players stats by a specific date", guild=discord.Object(id=GUILD))
async def predict_by_date(interaction, player: str, days_back: int, fkills: int, fdeaths: int, stars: float,
                          current_fkills: int, current_fdeaths: int, current_stars: int, predict_by_days: int):
    fkdr_current = round(current_fkills / current_fdeaths, 2)

    today = datetime.date.today()
    prediction_day = today + datetime.timedelta(days=predict_by_days)

    predicted_stars, predicted_finals, predicted_fdeaths, predicted_fkdr = externals.predict_stats(days_back, fkills, fdeaths, stars, current_fkills, current_fdeaths, current_stars, prediction_day)
    fkdr_change = round(predicted_fkdr - fkdr_current, 2)

    await interaction.response.send_message(f"**[✓]** **{player}** is predicted to have the following stats in"
                                            f" **{predict_by_days}** days ({prediction_day.year}/{prediction_day.month}/"
                                            f"{prediction_day.day}) based on the last **{days_back}** days:\n"
                                            f"Stars: **[{predicted_stars}✫]**"
                                            f" ({externals.change_character(current_stars, after=predicted_stars)}"
                                            f"{round(predicted_stars-current_stars, 2)}✫)\n"
                                            f"FKDR: **{predicted_fkdr}** ({externals.change_character(change=fkdr_change)}{fkdr_change} fkdr)")

@tree.command(name="predictprestiges", description="Predicts when a player will prestige", guild=discord.Object(id=GUILD))
async def predictprestiges(interaction, player: str, days_back: int, stars: float, current_stars: int):
    await interaction.response.send_message("**[!]** Feature not working yet:(")
    if "a" == "WIP":
        stars_daily = days_back / stars
        prestiges_calculated = 0
        existing_pres_count = 1
        string = f"**[✓]** **{player}** is predicted to prestige on the following days:\n"
        while prestiges_calculated < 5:
            if current_stars > existing_pres_count * 100:
                existing_pres_count += 1
            else:
                existing_pres_count += 1

                days_per_prestige = round(stars_daily * 100)

                if prestiges_calculated == 0:
                    days_until_prestige = round(stars_daily * (100 - current_stars % 100))
                else:
                    days_until_prestige = round((days_per_prestige * (prestiges_calculated+1)) + (stars_daily * (100 - current_stars % 100)))

                today = datetime.date.today()
                prestige_date = today + datetime.timedelta(days=days_per_prestige*(prestiges_calculated+1))

                string += f"**[{existing_pres_count*100-100}✫]** in **{days_per_prestige*prestiges_calculated}** days at " \
                          f"**{prestige_date.year}/{prestige_date.month}/{prestige_date.day}**\n"
                prestiges_calculated += 1

# Self update commands -------------------------------------------------------------------------------------------------

@tree.command(name="selfupdate", description="Attempts to update the bot. If unsure, don't run this command.", guild=discord.Object(id=GUILD))
async def selfupdate(interaction: discord.Interaction):
    is_failed = False
    is_updated = False
    text = f"**Starting self update - Requested by: {interaction.user.mention}**"
    await interaction.response.send_message(text)
    if DEVELOPMENT == 1:
        text += "\n**[x]** Bot is running in a development environment, unable to update"
        await interaction.edit_original_response(content=text)
        is_failed = True
    else:
        text += "\n**[✓]** Bot is running in a production environment, continuing update"
        await interaction.edit_original_response(content=text)
        text += f"\n**[✓]** Current version is: {VERSION}"
        await interaction.edit_original_response(content=text)

    if not is_failed:
        text += f"\n**[✓]** Running: `git pull`..."
        await interaction.edit_original_response(content=text)
        output = subprocess.getoutput("git pull")
        text += f"\n```{output}```"
        await interaction.edit_original_response(content=text)

        if "Already up to date." in output:
            text += f"**[✓]** Nothing to update, bot is already up to date."
            await interaction.edit_original_response(content=text)
            is_failed = True

    if not is_failed:
        text += f"**[✓]** Local files updated. Restarting bot."
        await interaction.edit_original_response(content=text)
    else:
        text += f"\n**Update aborted.**"
        await interaction.edit_original_response(content=text)


# Events ---------------------------------------------------------------------------------------------------------------

@client.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=GUILD))
    print("Ready!")

# Tasks ----------------------------------------------------------------------------------------------------------------

@tasks.loop(seconds=5)
async def task_refreshvc():  # Function to shut down the bot if its experiencing too many errors
    await client.wait_until_ready()
    guild = client.get_guild(GUILD)
    channel = guild.get_channel(QUEUE_CHANNEL)
    for member in partied_members:
        try:
            if member.voice is not None:
                if member.voice.channel.name == channel.name:
                    await member.move_to(guild.get_channel(MAIN_CHANNEL))
        except Exception as ex:
            pass

client.run(TOKEN)
