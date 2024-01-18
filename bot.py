import os
import pkgutil

import interactions
from dotenv import find_dotenv, load_dotenv, set_key

import src.db.db as db
from src.ubi.authentication import *



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

#TODO: Authenticate



#todo make this update a command
def update():

    # Make sure we have a valid nadeo access token
    # TODO: Move this check into a separate function that's on a timer,
    #           so we never have an invalid token
    check_token_refresh()

    # load everything that should be updated from db
    
    # format everything nicely before sending to nadeo
        
    # send request to nadeo with all times & maps
        
    # get data from nadeo and format it nicely
    res = [] #TODO: get nadeo data here
        
    # update db 
    queries = []
    for [time, player_id, map_id] in res:
        queries.append((db.add_time, (player_id, map_id, time)))
    conn = db.open_conn()
    db.execute_queries(conn, queries)

# Load all extensions
extensions = [m.name for m in pkgutil.iter_modules(["src/commands"], prefix="src.commands.")]
for extension in extensions:
    bot.load_extension(extension)

bot.start(TOKEN)
