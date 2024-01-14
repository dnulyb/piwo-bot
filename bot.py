import os

import interactions
from dotenv import load_dotenv

from interactions import (
    slash_command, 
    slash_option, 
    SlashContext,
    SlashCommandChoice,
    OptionType,
    check, 
    is_owner,
    BaseContext
)

import src.db.db as db



# load bot variables
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = os.getenv("GUILD_ID")

bot = interactions.Client(
    # set debug_scope to not be in global scope
    debug_scope=GUILD_ID, 
)
#bot.interaction_tree.update()

# set up db
db.init()

#Commands start

"""
#custom check example
async def my_check(ctx: BaseContext):
    return ctx.author.username.startswith("a")

@slash_command(name="my_command")
@check(my_check)
async def command(ctx: SlashContext):
    await ctx.send("Your username starts with an 'a'!", ephemeral=True)
"""

@slash_command(
    name="shutdown",
    description="Shuts down the bot."
)
@check(is_owner())
async def shutdown(ctx: SlashContext):
    await ctx.send("Shutting down the bot.", ephemeral=True)
    await bot.stop()

@slash_command(
    name="ping",
    description="Replies to pings",
)
async def ping(ctx: SlashContext):
    await ctx.send("pong")

@slash_command(
    name="tournament",
    description="Tournament management"
)
@slash_option(
    name="action",
    description="Tournament management action",
    required=True,
    opt_type = OptionType.STRING,
    choices=[
        SlashCommandChoice(name="create", value="create"),
        SlashCommandChoice(name="delete", value="delete"),
        SlashCommandChoice(name="list", value="list"),
        SlashCommandChoice(name="auto update ON", value="autoon"),
        SlashCommandChoice(name="auto update OFF", value="autooff")
    ]
)
@slash_option(
    name="name",
    description="Name of the tournament you want to manage",
    required=False,
    opt_type = OptionType.STRING
)
async def tournament(ctx: SlashContext, action: str, name: str = ""):

    conn = db.open_conn()

    try:
        match action:
            case "create":
                query = [(db.add_tournament, [name])]
                res = "Created tournament: " + name
            case "delete":
                query = [(db.remove_tournament, [name])]
                res = "Deleted tournament: " + name
            case "autoon":
                query = [(db.auto_update_tournament, (1, name))]
                res = "Turned ON auto update for tournament: " + name
            case "autooff":
                query = [(db.auto_update_tournament, (0, name))]
                res = "Turned OFF auto update for tournament: " + name
            case "list":
                query = (db.list_tournaments, None)
                res = db.retrieve_data(conn, query)
            case _:
                res = "invalid tournament action"

        # always send reply
        await ctx.send(f"{res}")

    except Exception as e:
        await ctx.send(f"Error occurred while running command: {e}")

    finally:
        conn.close() 

    
#Commands end



bot.start(TOKEN)
