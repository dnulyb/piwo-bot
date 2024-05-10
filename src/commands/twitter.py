from interactions import (
    Extension,
    slash_command, 
    slash_option,
    OptionType,
    SlashCommandChoice,
    SlashContext,
    Task,
    IntervalTrigger
)
#from interactions.api.events import Startup

import asyncio
import feedparser as fp
from dateutil import parser
from dotenv import find_dotenv, load_dotenv, set_key, get_key

fxtwitter_url="https://fxtwitter.com/"

class Twitter(Extension):

    @Task.create(IntervalTrigger(minutes=30))
    async def check_tweets(self):

        dotenv_path = find_dotenv()
        load_dotenv(dotenv_path)

        channel_id = get_key(dotenv_path, ("DISCORD_TWITTER_CHANNEL"))
        channel = self.bot.get_channel(channel_id)

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
        name="twitter",
        description="Set a Twitter account to get tweets posted in Discord.",
        sub_cmd_name="toggle",
        sub_cmd_description="Toggle automatic tweets ON or OFF.",
        dm_permission=False
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
    async def toggle(self, ctx: SlashContext, toggle: str):

        if toggle == "ON":
            self.check_tweets.start()
            await ctx.send("Tweets toggled ON.")
        elif toggle == "OFF":
            self.check_tweets.stop()
            await ctx.send("Tweets toggled OFF.")
        else:
            await ctx.send("ERROR: Couldn't toggle tweets.", ephemeral=True)

    # Nitter shut down, so no point of checking
    """
    @listen(Startup)
    async def on_startup(self):
        await self.check_tweets()
        self.check_tweets.start()
    """


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

        # Replace twitter link with fxtwitter link, to get discord embeds working
        final_link = link.replace(base_url, fxtwitter_url)
        # clean trailing '#m' in links
        final_link = final_link.replace('#m', '')

        new_tweets.append(final_link)
    
    return new_tweets

