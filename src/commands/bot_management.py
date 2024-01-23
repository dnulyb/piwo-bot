from interactions import (
    Extension,
    slash_command, 
    SlashContext,
    check, 
    is_owner,
    Client,
    listen,
    Task,
    IntervalTrigger
)
from interactions.api.events import Startup

import pkgutil
import asyncio
from dotenv import find_dotenv, load_dotenv, get_key

import src.db.db as db
from src.ubi.authentication import check_token_refresh
from src.rss import check_for_new_tweets

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
        name="shutdown",
        description="Shuts down the bot."
    )
    @check(is_owner())
    async def shutdown(self, ctx: SlashContext):
        await ctx.send("Shutting down the bot.", ephemeral=True)
        await self.bot.stop()

    @slash_command(
        name="reload_extensions",
        description="Reloads all bot extensions."
    )
    @check(is_owner())
    async def reload_extensions(self, ctx: SlashContext):
        extensions = [m.name for m in pkgutil.iter_modules(["src/commands"], prefix="src.commands.")]
        for extension in extensions:
            self.bot.reload_extension(extension)

        await ctx.send("Reloaded bot extensions.", ephemeral=True)

    @slash_command(
        name="ping",
        description="Replies to pings",
    )
    async def ping(self, ctx: SlashContext):
        await ctx.send("pong")

    # Tasks
    @Task.create(IntervalTrigger(minutes=30))
    async def update_nadeo_token(self):
        print("Checking if Nadeo access token needs an update...")
        check_token_refresh()

    @Task.create(IntervalTrigger(minutes=30))
    async def check_tweets(self, bot: Client):

        dotenv_path = find_dotenv()
        load_dotenv(dotenv_path)

        channel_id = get_key(dotenv_path, ("DISCORD_TWITTER_CHANNEL"))
        channel = bot.get_channel(channel_id)

        print("Checking for new tweets...")
        tweets = check_for_new_tweets()

        if(len(tweets) == 0):
            # No new tweets
            print("No new tweets found.")
            return
        else:
            print(len(tweets), " tweets found! Posting...")

        for tweet in tweets:

            await channel.send(tweet)

            # It's best to have at least some delay between posting new tweets
            await asyncio.sleep(10)

        print("Finished checking for new tweets.")

    @listen(Startup)
    async def on_startup(self, event: Startup):

        # Make sure db is set up
        db.init()

        # Initial checks
        await self.update_nadeo_token()
        await self.check_tweets(event.client)

        # Start tasks
        self.update_nadeo_token.start()
        self.check_tweets.start(event.client)