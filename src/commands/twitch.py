from interactions import (
    Extension,
    slash_command, 
    slash_option, 
    SlashContext,
    OptionType,
    Task,
    IntervalTrigger,
    listen,
    Embed
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
        name="twitch",
        description="Manage Twitch channels to follow for updates when they go live.",
        sub_cmd_name="add",
        sub_cmd_description="Add a twitch channel to track for live notifications.",
        dm_permission=False
    )
    @slash_option(
        name="channel_name",
        description="Name of the channel you want to add. Example: 'spammiej'",
        required=True,
        opt_type = OptionType.STRING
    )
    async def add(self, ctx: SlashContext, channel_name: str):

        conn = db.open_conn()

        try:

            query = [(db.add_twitch_channel, [channel_name])]
            db.execute_queries(conn, query)
            res = "Added twitch channel: " + channel_name

            # always send reply
            await ctx.send(f"{res}")

        except Exception as e:
            await ctx.send(f"Error occurred while running command: {e}", ephemeral=True)

        finally:
            conn.close() 

    @slash_command(
        name="twitch",
        sub_cmd_name="remove",
        sub_cmd_description="Remove a twitch channel from live notifications tracking.",
        dm_permission=False
    )
    @slash_option(
        name="channel_name",
        description="Name of the channel you want to remove. Example: 'spammiej'",
        required=True,
        opt_type = OptionType.STRING
    )
    async def remove(self, ctx: SlashContext, channel_name: str):

        conn = db.open_conn()

        try:

            query = [(db.remove_twitch_channel, [channel_name])]
            db.execute_queries(conn, query)
            res = "Removed twitch channel: " + channel_name

            # always send reply
            await ctx.send(f"{res}")

        except Exception as e:
            await ctx.send(f"Error occurred while running command: {e}", ephemeral=True)

        finally:
            conn.close() 

    @slash_command(
        name="list",
        sub_cmd_name="twitch",
        sub_cmd_description="Lists all twitch channels in the database.",
        dm_permission=False
    )
    async def list(self, ctx: SlashContext):

        conn = db.open_conn()

        try:

            res = get_streams()
            if(len(res) == 0):
                await ctx.send("Error: No streams in database.", ephemeral=True)
                return
            
            embed = format_channel_list(res)
            await ctx.send(embed=embed, ephemeral=True)

        except Exception as e:
            await ctx.send(f"Error occurred while running command: {e}", ephemeral=True)

        finally:
            conn.close() 


    @Task.create(IntervalTrigger(minutes=10))
    async def check_recently_started_streams(self):

        print("Checking for recently started streams...")

        dotenv_path = find_dotenv()
        load_dotenv(dotenv_path)

        channel_id = get_key(dotenv_path, ("DISCORD_TWITCH_CHANNEL"))
        channel = self.bot.get_channel(channel_id)

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
    async def on_startup(self):
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

    time = requests.get(twitch_uptime_url + stream).content.decode('utf-8')

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
    

def format_channel_list(channels):

    embed = Embed()
    embed.title = "Twitch channels"
    embed.description = "A message will be sent when these twitch channels go live."

    value = ""

    for channel in channels:
        value += channel + "\n"

    embed.add_field(name="Channels", value=value, inline=False)

    return embed
