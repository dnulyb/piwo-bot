from interactions import (
    Extension,
    slash_command, 
    SlashContext,
    Embed,
    cooldown,
    Buckets,
    check,
    is_owner,
    Task,
    TimeTrigger,
    listen
)
from interactions.api.events import Startup

import src.db.db as db
from src.ubi.authentication import get_nadeo_access_token
from src.commands.map import get_map_records, get_map_data, format_map_record

from dotenv import find_dotenv, load_dotenv, get_key, set_key
import requests
import re
import time
import math


totd_url = "https://live-services.trackmania.nadeo.live/api/token/campaign/month?length=1&offset=0"
cotd_url = "https://meet.trackmania.nadeo.club/api/cup-of-the-day/current"
challenge_url = "https://meet.trackmania.nadeo.club/api/challenges/"
competition_rounds_url = "https://meet.trackmania.nadeo.club/api/competitions/"
competition_matches_url = "https://meet.trackmania.nadeo.club/api/rounds/"
competition_match_results_url = "https://meet.trackmania.nadeo.club/api/matches/"

map_name_regex = r"(?i)(?<!\$)((?P<d>\$+)(?P=d))?((?<=\$)(?!\$)|(\$([a-f\d]{1,3}|[ionmwsztg<>]|[lhp](\[[^\]]+\])?)))"

class Cotd(Extension):

    #Get updated totd leaderboard
    @slash_command(
        name="totd",
        description="TOTD info.",
        sub_cmd_name="leaderboard",
        sub_cmd_description="Updates TOTD times, and shows the current leaderboard.",
        dm_permission=False
    )
    @cooldown(Buckets.GUILD, 1, 60)
    async def leaderboard(self, ctx: SlashContext):

        await ctx.defer()

        dotenv_path = find_dotenv()
        load_dotenv(dotenv_path)

        totd_id = get_key(dotenv_path, ("TOTD_MAP_ID"))
        totd_name = get_key(dotenv_path, ("TOTD_MAP_NAME"))

        print("Updating TOTD: " + totd_name)
        print("with id: " + totd_id)

        conn = db.open_conn()
        query = (db.get_specific_roster_players, ["cotd"])
        cotd_players = db.retrieve_data(conn, query)
        conn.close()

        player_ids = []
        #name, id
        for (_, id) in cotd_players:
            player_ids.append(id)

        map_ids = [totd_id]

        # get data from nadeo and format it nicely
        print("Retrieving nadeo TOTD data")

        token = get_nadeo_access_token()
        totd_data = get_map_records(player_ids, map_ids, token)

        totd_results = []
        for (player_time, player_id, _) in totd_data:
            for (cotd_player_name, cotd_player_id) in cotd_players:
                if player_id == cotd_player_id:
                    player_time = format_map_record(player_time)
                    totd_results.append((cotd_player_name, player_time))
        
        #Sort so that minutes come after seconds
        sorted_results = sorted(totd_results, key=lambda x:(len(x[1]), x[1]))

        embed = format_totd_leaderboard(totd_name, sorted_results)

        await ctx.send(embed=embed)

    @slash_command(
        name="totd",
        sub_cmd_name="map_info",
        sub_cmd_description="Retrieves and stores info about todays TOTD in the bot.",
        dm_permission=False
    )
    @cooldown(Buckets.GUILD, 1, 1800)
    async def map_info(self, ctx: SlashContext):

        await ctx.defer()

        dotenv_path = find_dotenv()
        load_dotenv(dotenv_path)

        get_totd_map_info()
        totd_id = get_key(dotenv_path, ("TOTD_MAP_ID"))
        totd_name = get_key(dotenv_path, ("TOTD_MAP_NAME"))

        await ctx.send("Today's TOTD: \nMap name: " + totd_name + "\nMap ID: " + totd_id)
    

    @check(is_owner())
    @cooldown(Buckets.GUILD, 1, 30)
    @slash_command(
        name="cotd",
        description="COTD info.",
        sub_cmd_name="quali_results",
        sub_cmd_description="Shows results for today's COTD qualification.",
        dm_permission=False
    )
    async def quali_results(self, ctx: SlashContext):

        await ctx.defer()

        dotenv_path = find_dotenv()
        load_dotenv(dotenv_path)

        results = get_cotd_quali_results()
        if(results == None):
            await ctx.send("No cotd quali could be found, try again around cotd time.")
            return

        (_, _, map_name) = get_totd_map_info()
        
        embed = format_cotd_quali_results(map_name, results)

        #await ctx.send("Posting cotd quali results:")
        print("Sending cotd quali results to channel")
        await ctx.send(embed=embed)

    @check(is_owner())
    @cooldown(Buckets.GUILD, 1, 30)
    @slash_command(
        name="cotd",
        description="COTD info.",
        sub_cmd_name="ko_results",
        sub_cmd_description="Shows results for today's COTD KO.",
        dm_permission=False
    )
    async def ko_results(self, ctx: SlashContext):

        await ctx.defer()

        dotenv_path = find_dotenv()
        load_dotenv(dotenv_path)

        results = get_cotd_ko_results(False)
        if(results == None):
            await ctx.send("No cotd ko could be found, try again around cotd time.")
            return

        (_, _, map_name) = get_totd_map_info()
        
        embed = format_cotd_ko_results(map_name, results)

        #await ctx.send("Posting cotd quali results:")
        print("Sending cotd KO results to channel")
        await ctx.send(embed=embed)

    # Time trigger is UTC by default
    #@Task.create(TimeTrigger(hour=18, minute=1)) #cotd start time
    @Task.create(TimeTrigger(hour=17, minute=17)) #cotd quali end time
    async def cotd_trigger(self):

        print("Cotd quali should be over now.")

        dotenv_path = find_dotenv()
        load_dotenv(dotenv_path)

        channel_id = get_key(dotenv_path, ("DISCORD_COTD_CHANNEL"))
        channel = self.bot.get_channel(channel_id)

        results = get_cotd_quali_results()
        if(results == None):
            await channel.send("Error retrieving cotd quali results: No quali could be found.", ephemeral=True)
            return

        (_, _, map_name) = get_totd_map_info()
        
        embed = format_cotd_quali_results(map_name, results)

        print("Sending cotd quali results to channel")
        await channel.send(embed=embed)

    @listen(Startup)
    async def on_startup(self):
        self.cotd_trigger.start()
        self.cotd_ko_trigger.start()

    @Task.create(TimeTrigger(hour=17, minute=45)) #approximate cotd ko end time
    async def cotd_ko_trigger(self):

        print("Cotd ko should be over now.")

        dotenv_path = find_dotenv()
        load_dotenv(dotenv_path)

        channel_id = get_key(dotenv_path, ("DISCORD_COTD_CHANNEL"))
        channel = self.bot.get_channel(channel_id)

        results = get_cotd_ko_results()
        if(results == None):
            await channel.send("Error retrieving cotd ko results: No ko could be found.", ephemeral=True)
            return

        (_, _, map_name) = get_totd_map_info()
        
        embed = format_cotd_ko_results(map_name, results)

        print("Sending cotd KO results to channel")
        await channel.send(embed=embed)

def get_cotd_ko_results(tryagain=True):

    # Get cotd matches from the competition id
    (_, competition_id) = get_cotd_ids()
    time.sleep(1)
    rounds_id = get_cotd_rounds(competition_id)
    time.sleep(1)

    finished = False
    if(tryagain):
        attempts = 0
    else:
        attempts = 30
    while(1):

        finished = True
        attempts += 1
        print("get_cotd_ko_results attempt: " + str(attempts))

        cotd_matches = get_cotd_matches(rounds_id)
        
        match_ids = []
        for match in cotd_matches['matches']:

            match_id = match['id']
            match_complete = match['isCompleted'] #bool

            match_ids.append(match_id)
            if(not match_complete):
                print("attempt: " + str(attempts)+ ", cotd match: " + str(match_id) + " is not complete, trying again later")
                match_ids.clear()
                finished = False
                break


        if(finished):

            print("Finished getting cotd matches, in " + str(attempts) + " attempts")

            # Get cotd players
            conn = db.open_conn()
            query = (db.get_specific_roster_players, ["cotd"])
            cotd_players = db.retrieve_data(conn, query)
            conn.close()

            # Get match results for each div 
            results = []
            for (div, match_id) in enumerate(match_ids, start=1):

                match_results = get_cotd_match_result(match_id)
                players = match_results['results']
                for player in players:

                    player_id = player['participant']
                    player_rank = player['rank']

                    for (cotd_player_name, cotd_player_id) in cotd_players:
                        if player_id == cotd_player_id:

                            #print("PIWO COTD PLAYER TODAY: " + cotd_player_name + ", RANK: " + str(player_rank))
                            results.append((div, player_rank, cotd_player_name))
                            
            # Return results     
            return results

        if(attempts >= 30):
            print("Failed to get todays cotd: not finished in time")
            return None

        # Not finished yet, waiting 1 minute until next attempt
        time.sleep(60)



def format_cotd_ko_results(map_name, results):

    embed = Embed()
    embed.title = "COTD KO results:"
    embed.description = "Map: " + map_name

    #Format everything nicely inside a code block
    header_format = "{:^3s} {:^5s} {:^15s} \n"
    format =        "{:^3s} {:^5s} {:15s} \n"

    everything = "```\n"
    everything += header_format.format("Div", "Rank", "Player")

    for result in results:
        (div, rank, player) = result
        everything += format.format(str(div), str(rank), player)
        
    everything += "```"

    field_name = '\u200b'
    embed.add_field(name=field_name, value=everything, inline=True)

    return embed


# Players have to be in the roster "cotd" to be included in results
def get_cotd_quali_results():

    conn = db.open_conn()
    query = (db.get_specific_roster_players, ["cotd"])
    cotd_players = db.retrieve_data(conn, query)
    conn.close()

    players = get_all_cotd_players()
    if(players == None):
        return None

    cotd_quali_results = []
    # Might be slow since players has length of 320
    for (player_id, player_rank, player_score) in players:
        for (cotd_player_name, cotd_player_id) in cotd_players:
            if player_id == cotd_player_id:
                cotd_quali_results.append((cotd_player_name, player_rank, player_score))

    #TODO: Save cotd performance in db

    # Now we have info about cotd performance for players that are registered
    #   to cotd roster, in cotd_quali_result
    #   which is a [(name, rank, score)], sorted best rank first

    # So just make a pretty leaderboard style discord embed
    #   and send it in the main channel
                
    return cotd_quali_results
                

def format_cotd_quali_results(map_name, results):

    embed = Embed()
    embed.title = "COTD Qualification results:"
    embed.description = "Map: " + map_name

    #Format everything nicely inside a code block
    header_format = "{:^3s} {:^5s} {:^15s} {:^16s} \n"
    format =        "{:^3s} {:^5s} {:15s} {:^16s} \n"

    everything = "```\n"
    everything += header_format.format("Div", "Rank", "Player", "Time")

    for result in results:
        (name, rank, time) = result
        division = div(rank)
        everything += format.format(str(division), str(rank), name, time)
        
    everything += "```"

    field_name = '\u200b'
    embed.add_field(name=field_name, value=everything, inline=True)

    return embed





def div(pos):
    return math.ceil(pos/64)


def format_totd_leaderboard(map_name, players):


    embed = Embed()
    embed.title = "TOTD internal leaderboard:"
    embed.description = "Map: " + map_name

    #Format everything nicely inside a code block
    header_format = "{:^3s} {:^15s} {:^16s} \n"
    format =        "{:^3s} {:15s} {:^16s} \n"

    everything = "```\n"
    everything += header_format.format("Pos", "Player", "Time")

    for i, player in enumerate(players, start=1):
        (name, time) = player
        pos = str(i) + "."
        everything += format.format(pos, name, time)

        if(len(everything) >= 900):
            everything += "```"
            field_name = '\u200b'
            embed.add_field(name=field_name, value=everything, inline=False)

            everything = "```\n"
            everything += header_format.format("Pos", "Player", "Time")
        
    everything += "```"

    field_name = '\u200b'
    embed.add_field(name=field_name, value=everything, inline=False)

    return embed


# Retrieves all cotd players that got div5 or better in quali
#   (div5 or better is 64*5=320 people)
# This function can be quite slow due to sleeps
def get_all_cotd_players():

    # Let's say div5 or better, so 320 players
    # We need 4 requests, 100 + 100 + 100 + 20
    # Adding some sleeps in between requests.

    (challenge_id, _) = get_cotd_ids()
    if(challenge_id == None):
        return None
    #challenge_id = 7169 # main cotd 2024-01-23 

    top100 = get_cotd_players(challenge_id, 100, 0)
    time.sleep(1)
    top101_200 = get_cotd_players(challenge_id, 100, 100)
    time.sleep(1)
    top201_300 = get_cotd_players(challenge_id, 100, 200)
    time.sleep(1)
    top301_320 = get_cotd_players(challenge_id, 20, 300)

    return top100 + top101_200 + top201_300 + top301_320


# Gets 'length' cotd players from the Nadeo leaderboards.
#   Nadeo has a limit of max 100 players at once
# length = how many players, maximum 100
# offset = where to start retrieving players
def get_cotd_players(challenge_id, length, offset):

    if(length > 100):
        length = 100

    dotenv_path = find_dotenv()
    load_dotenv(dotenv_path)

    # Using the NadeoClubServices audience
    token = get_key(dotenv_path, ("NADEO_CLUBSERVICES_ACCESS_TOKEN"))
    user_agent = get_key(dotenv_path, ("USER_AGENT"))

    complete_challenge_url = challenge_url + str(challenge_id) + \
                            "/leaderboard?length=" + str(length) + \
                            "&offset=" + str(offset)
    
    # Send get request
    headers = {
        'Authorization': "nadeo_v1 t=" + token,
        'User-Agent': user_agent
    }

    res = requests.get(complete_challenge_url, headers=headers)
    res = res.json()

    results = res['results']
    players = [[elem["player"],
                elem["rank"],
                format_map_record(elem["score"])]
                for elem in results]
    
    return players



# Cotd challenge is the qualification.
# This switches to the next cotd quali when the last one 
#   has finished a while ago, maybe 3-4 hours after.
# Beware that it will get response 204 - no content, if there's no recent quali.
def get_cotd_ids():

    dotenv_path = find_dotenv()
    load_dotenv(dotenv_path)

    # Using the NadeoClubServices audience
    token = get_key(dotenv_path, ("NADEO_CLUBSERVICES_ACCESS_TOKEN"))
    user_agent = get_key(dotenv_path, ("USER_AGENT"))

    # Send get request
    headers = {
        'Authorization': "nadeo_v1 t=" + token,
        'User-Agent': user_agent
    }

    res = requests.get(cotd_url, headers=headers)
    try:
        res = res.json()
    except Exception as e:
        print("get_cotd_ids did not receive valid json, returning None. Exception: ",e)
        return None

    challenge_id = res['challenge']['id']
    competition_id = res['competition']['id']
    return (challenge_id, competition_id)


def get_cotd_rounds(competition_id):

    complete_url = competition_rounds_url + \
                    str(competition_id) + \
                    "/rounds"
    
    dotenv_path = find_dotenv()
    load_dotenv(dotenv_path)

    # Using the NadeoLiveServices audience
    token = get_key(dotenv_path, ("NADEO_LIVESERVICES_ACCESS_TOKEN"))
    user_agent = get_key(dotenv_path, ("USER_AGENT"))

    # Send get request
    headers = {
        'Authorization': "nadeo_v1 t=" + token,
        'User-Agent': user_agent
    }

    res = requests.get(complete_url, headers=headers)
    try:
        res = res.json()
    except Exception as e:
        print("get_cotd_rounds did not receive valid json, returning None. Exception: ",e)
        return None
    
    rounds_id = res[0]['id']
    return rounds_id

def get_cotd_matches(rounds_id):

    complete_url = competition_matches_url + \
                    str(rounds_id) + \
                    "/matches?length=5&offset=0"
    
    dotenv_path = find_dotenv()
    load_dotenv(dotenv_path)

    # Using the NadeoLiveServices audience
    token = get_key(dotenv_path, ("NADEO_LIVESERVICES_ACCESS_TOKEN"))
    user_agent = get_key(dotenv_path, ("USER_AGENT"))

    # Send get request
    headers = {
        'Authorization': "nadeo_v1 t=" + token,
        'User-Agent': user_agent
    }

    res = requests.get(complete_url, headers=headers)
    try:
        res = res.json()
    except Exception as e:
        print("get_cotd_rounds did not receive valid json, returning None. Exception: ",e)
        return None
    
    return res #returns the full match json


def get_cotd_match_result(match_id):

    complete_url = competition_match_results_url + \
                    str(match_id) + \
                    "/results?length=64&offset=0"
    
    dotenv_path = find_dotenv()
    load_dotenv(dotenv_path)

    # Using the NadeoLiveServices audience
    token = get_key(dotenv_path, ("NADEO_LIVESERVICES_ACCESS_TOKEN"))
    user_agent = get_key(dotenv_path, ("USER_AGENT"))

    # Send get request
    headers = {
        'Authorization': "nadeo_v1 t=" + token,
        'User-Agent': user_agent
    }

    res = requests.get(complete_url, headers=headers)
    try:
        res = res.json()
    except Exception as e:
        print("get_cotd_rounds did not receive valid json, returning None. Exception: ",e)
        return None
    
    return res #returns the full match json

# Return: (map_id, map_uid, map_name)
def get_totd_map_info():

    dotenv_path = find_dotenv()
    load_dotenv(dotenv_path)

    # Using the NadeoLiveServices audience
    token = get_key(dotenv_path, ("NADEO_LIVESERVICES_ACCESS_TOKEN"))
    user_agent = get_key(dotenv_path, ("USER_AGENT"))

    # Send get request
    headers = {
        'Authorization': "nadeo_v1 t=" + token,
        'User-Agent': user_agent
    }

    res = requests.get(totd_url, headers=headers)
    res = res.json()

    # Get the map uid
    days = res['monthList'][0]['days']
    filtered_days = [day for day in days if day['mapUid'] != ""]

    totd = []
    for day in reversed(filtered_days):
        totd = day
        break

    totd_mapUid = totd['mapUid']

    # Use map uid to get the map id from nadeo
    res = get_map_data([totd_mapUid])
    [[map_id, map_uid, map_name]] = res
    map_name = clean_map_name(map_name)

    set_key(dotenv_path, "TOTD_MAP_ID", map_id)
    set_key(dotenv_path, "TOTD_MAP_NAME", map_name)

    return (map_id, map_uid, map_name)


def clean_map_name(map_name):
    return re.sub(map_name_regex, "", map_name)