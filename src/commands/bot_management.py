from interactions import (
    Extension,
    slash_command, 
    slash_option,
    OptionType,
    SlashCommandChoice,
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
from dotenv import find_dotenv, load_dotenv, get_key, set_key

import src.db.db as db
from src.ubi.authentication import check_token_refresh
from src.rss import check_for_new_tweets
from src.commands.cotd import (
    get_cotd_quali_results, 
    format_cotd_quali_results,
)
from src.commands.twitch import (
    get_streams,
    stream_recently_live,
    twitch_url
)
from src.ubi.cotd_totd_data import (
    get_totd_map_info
)

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
        name="reload_extension",
        description="Reloads a bot extension."
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
            if(extension.name == name):
                self.bot.reload_extension(extension)
                await ctx.send("Reloaded bot extension.", ephemeral=True)
                return


        await ctx.send("Could not reload extension: name not found.", ephemeral=True)

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

    
    @Task.create(IntervalTrigger(minutes=10))
    async def check_recently_started_streams(self, bot: Client):

        print("Checking for recently started streams...")

        dotenv_path = find_dotenv()
        load_dotenv(dotenv_path)

        channel_id = get_key(dotenv_path, ("DISCORD_TWITCH_CHANNEL"))
        channel = bot.get_channel(channel_id)

        streams = get_streams()
        for stream in streams:
            await asyncio.sleep(0.2) # Don't spam the api too hard
            if(stream_recently_live(stream)):
                url = twitch_url + stream
                await channel.send(f"{stream} recently went live! Watch here: {url}")
                # Add some delay between posting streams
                await asyncio.sleep(1)

        print("Finished checking for recently started streams.")
        

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

    @slash_command(
        name="tweets_toggle",
        description="Turn tweets ON or OFF."
    )
    @slash_option(
        name="toggle",
        description="ON/OFF",
        required=True,
        opt_type = OptionType.STRING,
        choices=[
            SlashCommandChoice(name="ON", value="ON"),
            SlashCommandChoice(name="OFF", value="OFF"),
        ]
    )
    async def tweets_toggle(self, ctx: SlashContext, toggle: str):

        if toggle == "ON":
            self.check_tweets.start(ctx.client)
            await ctx.send("Tweets toggled ON.")
        elif toggle == "OFF":
            self.check_tweets.stop()
            await ctx.send("Tweets toggled OFF.")
        else:
            await ctx.send("ERROR: Couldn't toggle tweets.")


    # Time trigger is UTC by default
    #@Task.create(TimeTrigger(hour=18, minute=1)) #cotd start date
    @Task.create(TimeTrigger(hour=18, minute=17))
    async def cotd_trigger(self, bot: Client):

        print("Cotd quali should be over now.")

        dotenv_path = find_dotenv()
        load_dotenv(dotenv_path)

        channel_id = get_key(dotenv_path, ("DISCORD_COTD_CHANNEL"))
        channel = bot.get_channel(channel_id)

        results = get_cotd_quali_results()
        if(results == None):
            await channel.send("Error retrieving cotd quali results: No quali could be found.")
            return

        (_, _, map_name) = get_totd_map_info()
        
        embed = format_cotd_quali_results(map_name, results)

        print("Sending cotd quali results to channel")
        await channel.send(embed=embed)


    @slash_command(
        name="cotd_test",
        description="test for cotd."
    )
    async def cotd_test(self, ctx: SlashContext):

        await ctx.defer()

        dotenv_path = find_dotenv()
        load_dotenv(dotenv_path)

        channel_id = get_key(dotenv_path, ("DISCORD_COTD_CHANNEL"))
        channel = ctx.client.get_channel(channel_id)

        results = get_cotd_quali_results()
        if(results == None):
            await ctx.send("No cotd quali could be found, try again around cotd time.")
            return

        (_, _, map_name) = get_totd_map_info()
        
        embed = format_cotd_quali_results(map_name, results)

        await ctx.send("Posting cotd quali results:")
        await channel.send(embed=embed)

    
    @slash_command(
        name="bot_discord_info_update",
        description="Update discord channels etc. that the bot will use for various purposes."
    )
    @slash_option(
        name="action",
        description="Which bot discord info to update.",
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
    async def bot_discord_info_update(self, ctx: SlashContext, action: str, value: str):

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

        await ctx.send("Updated: " + action +", with: " + value)
        


    @listen(Startup)
    async def on_startup(self, event: Startup):

        # Make sure db is set up
        db.init()

        # Initial checks
        await self.update_nadeo_token()
        await self.check_recently_started_streams(event.client)
        await self.check_tweets(event.client)

        # Start tasks
        self.update_nadeo_token.start()
        self.check_tweets.start(event.client)
        self.cotd_trigger.start(event.client)
        self.check_recently_started_streams.start(event.client)

