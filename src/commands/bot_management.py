from interactions import (
    Extension,
    slash_command, 
    SlashContext,
    check, 
    is_owner,
    Client,
    listen,
    Task,
    IntervalTrigger,
    TimeTrigger,
    cooldown,
    Buckets
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
    @cooldown(Buckets.GUILD, 1, 60)
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

    # Time trigger is UTC by default
    @Task.create(TimeTrigger(hour=18, minute=1))
    async def cotd_trigger(self):
        print("It's cotd time right now.")

        """
        conn = db.open_conn()
        query = (db.get_specific_roster_players, ["cotd"])
        cotd_players = db.retrieve_data(conn, query)
        conn.close()

        cotd_player_ids = [player[1] for player in cotd_players]
        players = get_all_cotd_players()

        cotd_players_today = []
        # Might be slow since players has length of 320
        for (player_id, player_rank, player_score) in players:
            for (cotd_player_name, cotd_player_id) in cotd_players:
                if player_id == cotd_player_id:
                    cotd_players_today.append((cotd_player_name, player_rank, player_score))

        # Now we have info about cotd performance for players that are registered
        #   to cotd roster, in cotd_players_today

        # So just make a pretty leaderboard style discord embed
        #   and send it in the main channel

        """

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
        self.cotd_trigger.start()