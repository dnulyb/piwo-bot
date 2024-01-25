from interactions import (
    Extension,
    slash_command, 
    slash_option, 
    SlashContext,
    OptionType,
    Task,
    IntervalTrigger,
    Client,
    listen
)
from interactions.api.events import Startup

import src.db.db as db
import requests
from dotenv import find_dotenv, load_dotenv, get_key
import asyncio


twitch_url = "https://www.twitch.tv/"
twitch_uptime_url = "https://decapi.me/twitch/uptime/"

class Twitch(Extension):

    @slash_command(
    name="twitch_add",
    description="Add a twitch channel to track for live notifications."
    )
    @slash_option(
        name="channel_name",
        description="Name of the channel you want to add. Example: 'spammiej'",
        required=True,
        opt_type = OptionType.STRING
    )
    async def twitch_add(self, ctx: SlashContext, channel_name: str):

        conn = db.open_conn()

        try:

            query = [(db.add_twitch_channel, [channel_name])]
            db.execute_queries(conn, query)
            res = "Added twitch channel: " + channel_name

            # always send reply
            await ctx.send(f"{res}")

        except Exception as e:
            await ctx.send(f"Error occurred while running command: {e}")

        finally:
            conn.close() 

    @slash_command(
        name="twitch_remove",
        description="Remove a twitch channel from live notifications tracking."
    )
    @slash_option(
        name="channel_name",
        description="Name of the channel you want to remove. Example: 'spammiej'",
        required=True,
        opt_type = OptionType.STRING
    )
    async def twitch_remove(self, ctx: SlashContext, channel_name: str):

        conn = db.open_conn()

        try:

            query = [(db.remove_twitch_channel, [channel_name])]
            db.execute_queries(conn, query)
            res = "Removed twitch channel: " + channel_name

            # always send reply
            await ctx.send(f"{res}")

        except Exception as e:
            await ctx.send(f"Error occurred while running command: {e}")

        finally:
            conn.close() 

    @slash_command(
        name="twitch_list",
        description="Lists all twitch channels in the database."
    )
    async def player_list(self, ctx: SlashContext):

        conn = db.open_conn()

        try:

            query = [db.get_twitch_list, None]
            res = db.retrieve_data(conn, query)

            # always send reply
            await ctx.send(f"{res}")

        except Exception as e:
            await ctx.send(f"Error occurred while running command: {e}")

        finally:
            conn.close() 


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

    @listen(Startup)
    async def on_startup(self, event: Startup):
        self.check_recently_started_streams.start()



def get_streams():

    conn = db.open_conn()
    query = [db.get_twitch_list, None]
    res = db.retrieve_data(conn, query)
    conn.close() 

    streams = []
    for stream_name in res:
        streams.append(stream_name[0])
    
    return streams



def stream_recently_live(stream):

    time = requests.get('https://decapi.me/twitch/uptime/' + stream).content.decode('utf-8')

    try:

        time = time.split(', ')

        (value, type) = time[0].split(" ")
        if(type == "second" or type == "seconds"): 
            return True
        if(type == "minute"):
            return True
        if(type == "minutes"):
            if(int(value) < 11):
                return True
        
        return False
    
    except:
        return False
