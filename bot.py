import pkgutil

import interactions
from interactions import listen, Task, IntervalTrigger
from interactions.api.events import Startup
from dotenv import find_dotenv, load_dotenv, get_key

import src.db.db as db
from src.ubi.authentication import *

from src.ubi.authentication import check_token_refresh
from src.rss import check_for_new_tweets
import asyncio



# load bot variables
dotenv_path = find_dotenv()
load_dotenv(dotenv_path)
TOKEN = get_key(dotenv_path, "DISCORD_TOKEN")
GUILD_ID = get_key(dotenv_path, "GUILD_ID")


bot = interactions.Client(
    # set debug_scope to not be in global scope
    debug_scope=GUILD_ID, 
)
#bot.interaction_tree.update()

# set up db
db.init()

# Load all extensions
extensions = [m.name for m in pkgutil.iter_modules(["src/commands"], prefix="src.commands.")]
for extension in extensions:
    bot.load_extension(extension)

# Tasks
@Task.create(IntervalTrigger(minutes=30))
async def update_nadeo_token():
    return
    print("Checking if Nadeo access token needs an update...")
    check_token_refresh()

@Task.create(IntervalTrigger(minutes=1))
async def check_tweets(self, ctx):

    #await ctx.send("I'm supposed to check for new tweets, but it's disabled atm.")
    print("I'm supposed to check for new tweets, but it's disabled atm.")
    return

    print("Checking for new tweets...")
    tweets = check_for_new_tweets()

    for tweet in tweets:

        await ctx.send(tweet)

        # It's best to have at least some delay between posting new tweets
        asyncio.sleep(10)

@listen(Startup)
async def on_startup():
    update_nadeo_token.start()
    check_tweets.start()


bot.start(TOKEN)
