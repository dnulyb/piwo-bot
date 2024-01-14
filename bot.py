import os

import interactions
from dotenv import load_dotenv

from interactions import (
    slash_command, 
    slash_option, 
    SlashContext,
    SlashCommandChoice,
    OptionType
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
        SlashCommandChoice(name="list", value="list")
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

    match action:

        case "create":
            query = [(db.add_tournament, [name])]
            try:
                db.execute_queries(conn, query)
                await ctx.send("Created tournament: " + name)
            except Exception as e:
                await ctx.send(f"Error occurred while running command: {e}")
            finally:
                conn.close()

        case "delete":
            query = [(db.remove_tournament, [name])]
            try:
                db.execute_queries(conn, query)
                await ctx.send("Deleted tournament: " + name)
            except Exception as e:
                await ctx.send(f"Error occurred while running command: {e}")
            finally:
                conn.close()     

        case "list":
            query = (db.list_tournaments, None)
            try:
                res = db.retrieve_data(conn, query)
                await ctx.send(f"{res}")
            except Exception as e:
                await ctx.send(f"Error occurred while running command: {e}")
            finally:
                conn.close()

        case _:
            await ctx.send("invalid tournament action")





#Commands end



bot.start(TOKEN)