from interactions import (
    Extension,
    slash_command, 
    slash_option,
    OptionType,
    SlashCommandChoice,
    SlashContext,
    Client,
    Task,
    IntervalTrigger,
    listen
)
from interactions.api.events import Startup

import asyncio
import feedparser as fp
from dateutil import parser
from dotenv import find_dotenv, load_dotenv, set_key, get_key

class Twitter(Extension):

    @Task.create(IntervalTrigger(minutes=30))
    async def check_tweets(bot: Client):

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

    @listen(Startup)
    async def on_startup(self, event: Startup):
        self.check_tweets.start()

def check_for_new_tweets():

    #url = "https://lorem-rss.herokuapp.com/feed" #test url

    dotenv_path = find_dotenv()
    load_dotenv(dotenv_path)

    latest_tweet = parser.parse(get_key(dotenv_path, "LATEST_TWEET_DATE"))

    base_url = get_key(dotenv_path, ("NITTER_BASE_URL"))
    account_url = get_key(dotenv_path, ("NITTER_ACCOUNT_URL"))
    complete_url = base_url + account_url + "/rss"

    feed = fp.parse(complete_url) # Use this to get from url

    """
    # Use this to get from file
    f = open("src/test_rss_feed.txt", "r")
    text = f.read()
    f.close()
    feed = fp.parse(io.BytesIO(bytes(text, 'utf-8')))
    """

    entries = feed.entries

    latest_of_new_tweets = latest_tweet
    # Reverse the entries to process older tweets first,
    #   in case there are multiple new ones
    new_tweets = []
    for entry in reversed(entries):

        link = entry.link

        # Ignore retweets
        if account_url not in link:
            continue

        # Ignore old tweets
        #   Note: When comparing parsed dates, Greater = later.
        time = parser.parse(entry.published)
        if latest_tweet >= time:
            continue

        # Update the latest known tweet
        if time > latest_of_new_tweets:
            set_key(dotenv_path, "LATEST_TWEET_DATE", str(time))
            latest_of_new_tweets = parser.parse(get_key(dotenv_path, "LATEST_TWEET_DATE"))

        replacement_url = get_key(dotenv_path, "FXTWITTER_URL")
        final_link = link.replace(base_url, replacement_url)
        # clean trailing '#m' in links
        final_link = final_link.replace('#m', '')

        new_tweets.append(final_link)
    
    return new_tweets

