from interactions import (
    Extension,
    slash_command, 
    slash_option,
    OptionType,
    SlashCommandChoice,
    SlashContext,
    check, 
    is_owner,
    listen,
    Task,
    IntervalTrigger,
    cooldown,
    Buckets
)
from interactions.api.events import Startup

import src.db.db as db
from src.ubi.authentication import check_token_refresh

import pkgutil
from dotenv import find_dotenv, load_dotenv, set_key

"""
#custom check example
async def my_check(ctx: BaseContext):
    return ctx.author.username.startswith("a")

@slash_command(name="my_command")
@check(my_check)
async def command(ctx: SlashContext):
    await ctx.send("Your username starts with an 'a'!", ephemeral=True)
"""


class BotManagement(Extension):

    @slash_command(
        name="bot",
        description="Bot management commands.",
        sub_cmd_name="shutdown",
        sub_cmd_description="Shuts down the bot.",
        dm_permission=False
    )
    @check(is_owner())
    async def shutdown(self, ctx: SlashContext):
        await ctx.send("Shutting down the bot.", ephemeral=True)
        await self.bot.stop()

    @slash_command(
        name="bot",
        description="Bot management commands.",
        sub_cmd_name="send_message_reply",
        sub_cmd_description="Replies to the given message",
        dm_permission=False
    )
    @slash_option(
        name="channel_id",
        description="ID of the channel the message is in.",
        required=True,
        opt_type = OptionType.STRING
    )
    @slash_option(
        name="message_id",
        description="ID of the message to reply to.",
        required=True,
        opt_type = OptionType.STRING
    )
    @slash_option(
        name="content",
        description="Content to send.",
        required=True,
        opt_type = OptionType.STRING
    )
    @check(is_owner())
    async def send_message_reply(self, ctx: SlashContext, channel_id, message_id, content):
        channel = self.bot.get_channel(channel_id)
        message = await channel.fetch_message(message_id)
        await message.reply(content=content)
        await ctx.send("message sent as reply.")


    @slash_command(
        name="bot",
        sub_cmd_name="reload_extension",
        sub_cmd_description="Reloads a bot extension.",
        dm_permission=False
    )
    @slash_option(
        name="name",
        description="Name of the extension to reload.",
        required=True,
        opt_type = OptionType.STRING
    )
    @check(is_owner())
    async def reload_extension(self, ctx: SlashContext, name: str):
        extensions = [m.name for m in pkgutil.iter_modules(["src/commands"], prefix="src.commands.")]
        for extension in extensions:
            if(extension == "src.commands." + name):
                self.bot.reload_extension(extension)
                await ctx.send("Reloaded bot extension.", ephemeral=True)
                return

        await ctx.send("Could not reload extension: name not found.", ephemeral=True)

    @slash_command(
        name="bot",
        sub_cmd_name="ping",
        sub_cmd_description="Replies to pings.",
        dm_permission=False
    )
    @cooldown(Buckets.GUILD, 1, 60)
    async def ping(self, ctx: SlashContext):
        await ctx.send("pong")

    @Task.create(IntervalTrigger(minutes=30))
    async def update_nadeo_token(self):
        print("Checking if Nadeo access token needs an update...")
        check_token_refresh()

    @slash_command(
        name="bot",
        sub_cmd_name="discord_channel_id_update",
        sub_cmd_description="Update discord channels etc. that the bot will use for various purposes.",
        dm_permission=False
    )
    @slash_option(
        name="action",
        description="Which bot discord channel id to update.",
        required=True,
        opt_type = OptionType.STRING,
        choices=[
            SlashCommandChoice(name="twitter_channel_id", value="twitter_channel_id"),
            SlashCommandChoice(name="twitch_channel_id", value="twitch_channel_id"),
            SlashCommandChoice(name="cotd_channel_id", value="cotd_channel_id"),
            SlashCommandChoice(name="roster_channel_id", value="roster_channel_id"),
            SlashCommandChoice(name="roster_message_id", value="roster_message_id")
        ]
    )
    @slash_option(
        name="value",
        description="The info to update",
        required=True,
        opt_type = OptionType.STRING
    )
    async def discord_channel_id_update(self, ctx: SlashContext, action: str, value: str):

        dotenv_path = find_dotenv()
        load_dotenv(dotenv_path)

        match action:
            case "twitter_channel_id":
                set_key(dotenv_path, "DISCORD_TWITTER_CHANNEL", value)
            case "twitch_channel_id":
                set_key(dotenv_path, "DISCORD_TWITCH_CHANNEL", value)
            case "cotd_channel_id":
                set_key(dotenv_path, "DISCORD_COTD_CHANNEL", value)
            case "roster_channel_id":
                set_key(dotenv_path, "DISCORD_ROSTER_CHANNEL", value)
            case "roster_message_id":
                set_key(dotenv_path, "DISCORD_ROSTER_MESSAGE", value)
            case _:
                await ctx.send("Invalid info name")

        await ctx.send("Updated: " + action + ", with: " + value)

    @listen(Startup)
    async def on_startup(self):

        # Make sure db is set up
        db.init()

        # Nadeo token updates
        await self.update_nadeo_token()
        self.update_nadeo_token.start()


