import os
from datetime import datetime

import interactions
from dotenv import find_dotenv, load_dotenv, set_key

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
from src.ubi.authentication import *



# load bot variables
dotenv_path = find_dotenv()
load_dotenv(dotenv_path)
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = os.getenv("GUILD_ID")


bot = interactions.Client(
    # set debug_scope to not be in global scope
    debug_scope=GUILD_ID, 
)
#bot.interaction_tree.update()

# set up db
db.init()

#TODO: Authenticate

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
    name="player_add",
    description="Add a player to the database."
)
@slash_option(
    name="nickname",
    description="Nickname of the player you want to add.",
    required=True,
    opt_type = OptionType.STRING
)
@slash_option(
    name="account_id",
    description="Account id of the player you want to add.",
    required=True,
    opt_type = OptionType.STRING
)
async def player_add(ctx: SlashContext, nickname: str, account_id: str):

    conn = db.open_conn()

    try:

        query = [(db.add_player, (nickname, account_id))]
        db.execute_queries(conn, query)
        res = "Added player: " + nickname

        # always send reply
        await ctx.send(f"{res}")

    except Exception as e:
        await ctx.send(f"Error occurred while running command: {e}")

    finally:
        conn.close() 

@slash_command(
    name="player_remove",
    description="Remove a player from the database."
)
@slash_option(
    name="nickname",
    description="Nickname of the player you want to remove.",
    required=True,
    opt_type = OptionType.STRING
)

async def player_remove(ctx: SlashContext, nickname: str, account_id: str):

    conn = db.open_conn()

    try:

        query = [(db.remove_player, [nickname])]
        db.execute_queries(conn, query)
        res = "Removed player: " + nickname

        # always send reply
        await ctx.send(f"{res}")

    except Exception as e:
        await ctx.send(f"Error occurred while running command: {e}")

    finally:
        conn.close() 

@slash_command(
    name="player_list",
    description="Lists all players in the database."
)
async def player_list(ctx: SlashContext):

    conn = db.open_conn()

    try:

        query = [db.list_players, None]
        res = db.retrieve_data(conn, query)

        # always send reply
        await ctx.send(f"{res}")

    except Exception as e:
        await ctx.send(f"Error occurred while running command: {e}")

    finally:
        conn.close() 

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
                db.execute_queries(conn, query)
            case "delete":
                query = [(db.remove_tournament, [name])]
                res = "Deleted tournament: " + name
                db.execute_queries(conn, query)
            case "autoon":
                query = [(db.auto_update_tournament, (1, name))]
                res = "Turned ON auto update for tournament: " + name
                db.execute_queries(conn, query)
            case "autooff":
                query = [(db.auto_update_tournament, (0, name))]
                res = "Turned OFF auto update for tournament: " + name
                db.execute_queries(conn, query)
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


#todo make this update a command
def update():

    # Make sure we have a valid nadeo access token
    # TODO: Move this check into a separate function that's on a timer,
    #           so we never have an invalid token
    check_token_refresh()

    # load everything that should be updated from db
    
    # format everything nicely before sending to nadeo
        
    # send request to nadeo with all times & maps
        
    # get data from nadeo and format it nicely
    res = [] #TODO: get nadeo data here
        
    # update db 
    queries = []
    for [time, player_id, map_id] in res:
        queries.append((db.add_time, (player_id, map_id, time)))
    conn = db.open_conn()
    db.execute_queries(conn, queries)



bot.start(TOKEN)
