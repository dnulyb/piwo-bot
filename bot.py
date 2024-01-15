import os
import base64
import json
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

    current_time = int(datetime.now().timestamp())
    #expiration = load from .env
    expiration = 0 #todo implement loading from dotenv

    if(current_time > expiration):
        #nadeo token has expired, we need to refresh

        # first before starting the bot: (token, refreshtoken) = authenticate()
        # then store token & refreshtoken in .env file
        #refreshtoken = load from dotenv
        refreshtoken = "not.implemented.justyet"
        [prefix, payload, signature] = refreshtoken.split(".")

        # payload might need padding to be able to be decoded
        if len(payload) % 4:
            payload += '=' * (4 - len(payload) % 4) 

        decodedPayload = base64.b64decode(payload)
        jsonPayload = json.loads(decodedPayload)
        #curr_nadeo_time = jsonPayload['iat'] # this is basically datetime.now() from nadeo
        expiration = jsonPayload['exp']
        # then do this: set_key(dotenv_path, "NADEO_TOKEN_EXP", expiration)



bot.start(TOKEN)
