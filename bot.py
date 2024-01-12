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

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = os.getenv("GUILD_ID")

bot = interactions.Client(
    debug_scope=GUILD_ID,
)
#bot.interaction_tree.update()
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
    name="option",
    description="Tournament management option",
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
    required=True,
    opt_type = OptionType.STRING
)
async def tournament(ctx: SlashContext, option: str, name: str):
    await ctx.send(name)

#Commands end



bot.start(TOKEN)