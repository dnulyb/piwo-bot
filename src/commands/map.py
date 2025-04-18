from interactions import (
    Extension,
    slash_command, 
    slash_option, 
    SlashContext,
    OptionType,
    Embed
)
import src.db.db as db
from src.db.db import get_tournament_db_id

import requests
import asyncio
import re
from dotenv import find_dotenv, load_dotenv, get_key
from math import floor

map_record_url = "https://prod.trackmania.core.nadeo.online/v2/mapRecords/"
map_info_url = "https://prod.trackmania.core.nadeo.online/maps/?mapUidList="

map_name_regex = r"(?i)(?<!\$)((?P<d>\$+)(?P=d))?((?<=\$)(?!\$)|(\$([a-f\d]{1,3}|[ionmwsztg<>]|[lhp](\[[^\]]+\])?)))"

class Map(Extension):

    @slash_command(
        name="map",
        description="Map management commands.",
        sub_cmd_name="add",
        sub_cmd_description="Adds a map to a tournament.",
        dm_permission=False
    )
    @slash_option(
        name="tournament",
        description="Name of the tournament you want to add maps to",
        required=True,
        opt_type = OptionType.STRING
    )
    @slash_option(
        name="map_name",
        description="name of the map you want to add.",
        required=True,
        opt_type = OptionType.STRING
    )
    @slash_option(
        name="map_id",
        description="id of the map you want to add.",
        required=True,
        opt_type = OptionType.STRING
    )
    async def add(self, ctx: SlashContext, tournament: str, map_name: str, map_id: str):

        conn = db.open_conn()

        try:
            # Get tournament id
            tournament_id = get_tournament_db_id(conn, tournament)

            if tournament_id == None:
                await ctx.send(f"Error occurred while running command: Tournament '{tournament}' not found", ephemeral=True)
                conn.close()
                return

            # Add the map to "Map" table
            #TODO: Change "uid" to "id" or something more fitting, in Map table
            db.execute_queries(conn, [(db.add_map, (map_name, map_id))])


            # Add the tournament and map to "Mappack" table
            map_database_id = db.retrieve_data(conn, (db.get_map_id, [map_name]))
            if(len(map_database_id) == 0):
                await ctx.send(f"Error occurred while running command: Map '{map}' not found", ephemeral=True)
                conn.close()
                return
            map_database_id = map_database_id[0][0]
        
            db.execute_queries(conn, [(db.add_to_mappack, (tournament_id, map_database_id))])

            await ctx.send("Added map to tournament '" + tournament + "': " + map_name)

        except Exception as e:
            await ctx.send(f"Error occurred while running command: {e}", ephemeral=True)
        finally:
            conn.close() 

    @slash_command(
        name="map",
        description="Map management commands.",
        sub_cmd_name="add_existing",
        sub_cmd_description="Adds a map that already exists in the database, to a tournament.",
        dm_permission=False
    )
    @slash_option(
        name="tournament",
        description="Name of the tournament you want to add the map to",
        required=True,
        opt_type = OptionType.STRING
    )
    @slash_option(
        name="map_name",
        description="Name of the map you want to add.",
        required=True,
        opt_type = OptionType.STRING
    )
    async def add_existing(self, ctx: SlashContext, tournament: str, map_name: str):

        conn = db.open_conn()

        try:
            # Get tournament id
            tournament_id = get_tournament_db_id(conn, tournament)

            if tournament_id == None:
                await ctx.send(f"Error occurred while running command: Tournament '{tournament}' not found", ephemeral=True)
                conn.close()
                return

            # Add the tournament and map to "Mappack" table
            map_database_id = db.retrieve_data(conn, (db.get_map_id, [map_name]))
            if(len(map_database_id) == 0):
                await ctx.send(f"Error occurred while running command: Map '{map}' not found", ephemeral=True)
                conn.close()
                return
            map_database_id = map_database_id[0][0]
        
            db.execute_queries(conn, [(db.add_to_mappack, (tournament_id, map_database_id))])

            await ctx.send("Added map to tournament '" + tournament + "': " + map_name)

        except Exception as e:
            await ctx.send(f"Error occurred while running command: {e}", ephemeral=True)
        finally:
            conn.close() 

    @slash_command(
        name="map",
        sub_cmd_name="delete",
        sub_cmd_description="Delete a map.",
        dm_permission=False
    )
    @slash_option(
        name="map_name",
        description="Name of the map you want to delete",
        required=True,
        opt_type = OptionType.STRING
    )
    async def delete(self, ctx: SlashContext, map_name: str):

        conn = db.open_conn()
        try:

            map_database_id = db.retrieve_data(conn, (db.get_map_id, [map_name]))
            if(len(map_database_id) == 0):
                await ctx.send(f"Error occurred while running command: Map '{map_name}' not found", ephemeral=True)
                conn.close()
                return
            map_database_id = map_database_id[0][0]

            #Delete from Mappack
            query = [(db.remove_from_mappack, [map_database_id])]
            db.execute_queries(conn, query)

            #Delete from Map
            query = [(db.remove_map, [map_name])]
            db.execute_queries(conn, query)
            await ctx.send("Deleted map: " + map_name)
        except Exception as e:
            await ctx.send(f"Error occurred while running command: {e}", ephemeral=True)
        finally:
            conn.close() 

    @slash_command(
        name="map",
        sub_cmd_name="update_id",
        sub_cmd_description="Update id for a map.",
        dm_permission=False
    )
    @slash_option(
        name="name",
        description="Name of the map.",
        required=True,
        opt_type = OptionType.STRING
    )
    @slash_option(
        name="id",
        description="The new id.",
        required=True,
        opt_type = OptionType.STRING
    )
    async def update_id(self, ctx: SlashContext, name: str, id: str):

        conn = db.open_conn()
        query = [(db.update_map_id, (id, name))]
        db.execute_queries(conn, query)
        res = "Updated id for map: " + name + "," + id
        conn.close()

        await ctx.send(f"{res}")

    @slash_command(
        name="list",
        sub_cmd_name="maps",
        sub_cmd_description="Lists all maps.",
        dm_permission=False
    )
    @slash_option(
        name="tournament",
        description="Name of the tournament you want to see maps for",
        required=False,
        opt_type = OptionType.STRING
    )
    async def list(self, ctx: SlashContext, tournament: str = None):
        
        conn = db.open_conn()
        try:
            if(tournament == None):
                query = (db.get_maps, None)
                res = db.retrieve_data(conn, query)
                if(len(res) == 0):
                    await ctx.send("Error while retrieving maps: No maps found.", ephemeral=True)
                    return
                
                embed = format_map_list(res)
                await ctx.send(embed=embed)
            else:
                tournament_id = get_tournament_db_id(conn, tournament)

                if tournament_id == None:
                    await ctx.send(f"Error occurred while running command: Tournament '{tournament}' not found", ephemeral=True)
                    conn.close()
                    return
                query = (db.get_tournament_maps, [tournament_id])
                res = db.retrieve_data(conn, query)
                if(len(res) == 0):
                    await ctx.send("Error while retrieving maps: No maps found.", ephemeral=True)
                    return
                
                embed = format_tournament_map_list(res)
                await ctx.send(embed=embed, ephemeral=True)


            
        except Exception as e:
            await ctx.send(f"Error occurred while running command: {e}", ephemeral=True)
        finally:
            conn.close() 

    @slash_command(
        name="lb",
        description="leaderboard commands",
        sub_cmd_name="team_leaderboard",
        sub_cmd_description="Shows the leaderboard ranks of players in the team. (times in top250 only)",
        dm_permission=False
    )
    @slash_option(
        name="map_uid",
        description="uid of the map you want to see the team leaderboard for.",
        required=True,
        opt_type = OptionType.STRING
    )
    async def team_leaderboard(self, ctx: SlashContext, map_uid: str):

        await ctx.defer()

        infos = await get_all_team_map_records(map_uid)
        if(infos == None):
            await ctx.send("No leaderboard could be found.")
            return
        
        [[_, _, map_name]] = get_map_data([map_uid])
        map_name = clean_map_name(map_name)

        embed = format_map_records_embed(map_name, infos)

        await ctx.send(embed=embed)



async def get_all_map_records(account_ids, map_ids, token):

    all_records = []
    for map_id in map_ids:

        map_records = get_map_records(account_ids, map_id, token)
        all_records = all_records + map_records
        await asyncio.sleep(0.5)

    return all_records


# Get map records for a list of accounts and a single map id
def get_map_records(account_ids, map_id, token):

    # Load variables from .env
    dotenv_path = find_dotenv()
    load_dotenv(dotenv_path)

    user_agent = get_key(dotenv_path, ("USER_AGENT"))

    # Build url
    account_id_str = ','.join(account_ids)
    complete_url = map_record_url + \
                    "?accountIdList=" + account_id_str + \
                    "&mapId=" + map_id
    
    # Send get request

    headers = {
        'Authorization': "nadeo_v1 t=" + token,
        'User-Agent': user_agent
    }

    res = requests.get(complete_url, headers=headers)
    res = res.json()

    # Return relevant data

    # Record format: time, accountId, mapId
    records = [[elem["recordScore"]["time"],
                    elem["accountId"],
                    elem["mapId"]]
                for elem in res]
    
    return records


# Get map records for everyone in the team (aka everyone in "cotd" roster)
# Only times in the top250 are retrieved 
async def get_all_team_map_records(map_uid):

    # Get team roster players from db
    conn = db.open_conn()
    query = (db.get_specific_roster_players, ["cotd"])
    team_players = db.retrieve_data(conn, query)
    conn.close()

    # Get map records from nadeo
    top100 = get_map_records_from_uid(map_uid, 100, 0)
    await asyncio.sleep(1)
    top101_200 = get_map_records_from_uid(map_uid, 100, 100)
    await asyncio.sleep(1)
    top201_250 = get_map_records_from_uid(map_uid, 50, 200)

    all_records = top100 + top101_200 + top201_250

    team_records = []
    # Filter out all non-team players
    for (id, pos, score) in all_records:
        for (team_player_name, team_player_id) in team_players:
            if id == team_player_id:
                team_records.append((pos, team_player_name, score))


    return team_records


# Retrieves leaderboard infos (accountid, position, score) from a map uid
def get_map_records_from_uid(map_uid, length, offset):

    leaderboard_url = "https://live-services.trackmania.nadeo.live/api/token/leaderboard/group/"
    groupUid = "Personal_Best"
    onlyWorld = "true"

    if(length > 100):
        length = 100

    dotenv_path = find_dotenv()
    load_dotenv(dotenv_path)

    # Using the NadeoLiveServices audience
    token = get_key(dotenv_path, ("NADEO_LIVESERVICES_ACCESS_TOKEN"))
    user_agent = get_key(dotenv_path, ("USER_AGENT"))

    # Build url
    complete_url = leaderboard_url + \
                    groupUid + \
                    "/map/" + \
                    map_uid + \
                    "/top?length=" + \
                    str(length) + \
                    "&onlyWorld=" + \
                    onlyWorld + \
                    "&offset=" + \
                    str(offset)
    
    # Send get request
    headers = {
        'Authorization': "nadeo_v1 t=" + token,
        'User-Agent': user_agent
    }

    res = requests.get(complete_url, headers=headers)
    res = res.json()

    #Extract the relevant info
    scores = res["tops"][0]["top"]
    scores = [[score["accountId"],
              score["position"],
              format_map_record(score["score"])]
              for score in scores]
    
    return scores


# Converts a record time of format "42690" to "42.690", or "62690" to "01:02.690"
#   mins: Bool, if there should be minutes in formatting or not. Default: True
def format_map_record(record, mins=True):

    #Check if time is formatted with minutes (ex. 01:01.110)
    #   If so, format as seconds
    record_string = str(record)
    minutes = record_string.split(":")[0]
    if(minutes != record_string):
        seconds = float(record_string.split(":")[1])
        minutes = int(minutes)
        record_string = str(seconds + 60 * minutes)
        record = int(record_string)

    else:
        record = int(record)

    if(mins):

        minutes = floor(record / 60000)
        seconds = record - (minutes * 60000)

        if(minutes == 0):
            minutes = ""
        elif(minutes < 10):
            minutes = "0" + str(minutes) + ":"
        else:
            minutes = str(minutes) + ":"

        
        if(seconds < 100):
            seconds = str(seconds)
            # Adding an extra '0' in front if the seconds are only 2 digits
            seconds = "00" + ".0" + seconds[-3:]
        elif(seconds < 1000):
            seconds = str(seconds)
            seconds = "00" + "." + seconds[-3:]
        elif(seconds < 10000):
            seconds = str(seconds)
            seconds = "0" + seconds[:-3] + "." + seconds[-3:]
        else:
            seconds = str(seconds)
            seconds = seconds[:-3] + "." + seconds[-3:]

        res = minutes + str(seconds)

        return res
    
    seconds = record
    if(seconds < 100):
        seconds = str(seconds)
        # Adding an extra '0' in front if the seconds are only 2 digits
        seconds = "00" + ".0" + seconds[-3:]
    elif(seconds < 1000):
        seconds = str(seconds)
        seconds = "00" + "." + seconds[-3:]
    elif(seconds < 10000):
        seconds = str(seconds)
        seconds = "0" + seconds[:-3] + "." + seconds[-3:]
    else:
        seconds = str(seconds)
        seconds = seconds[:-3] + "." + seconds[-3:]

    return seconds




# Get map information from a map uid
def get_map_data(map_uids):

    # Load variables from .env
    dotenv_path = find_dotenv()
    load_dotenv(dotenv_path)

    token = get_key(dotenv_path, ("NADEO_ACCESS_TOKEN"))
    user_agent = get_key(dotenv_path, ("USER_AGENT"))

    # Build url
    uid_str = ','.join(map_uids)
    complete_url = map_info_url + uid_str

    # Send get request

    headers = {
        'Authorization': "nadeo_v1 t=" + token,
        'User-Agent': user_agent
    }

    res = requests.get(complete_url, headers=headers)
    res = res.json()
    
    # Return the relevant data
    map_data = [[elem["mapId"],
                    elem["mapUid"],
                    elem["name"]]
                for elem in res]

    return map_data


def get_map_uid_from_db(conn, map_name):

    return db.retrieve_data(conn, (db.get_map_uid, [map_name]))[0][0]


def format_map_list(maps):

    embed = Embed()
    embed.title = "All maps in the database"

    names = ""
    ids = ""
    for (map, id) in maps:
        names += map + "\n"
        ids += id + "\n"
    
    embed.add_field(name="Map", value=names, inline=True)
    embed.add_field(name="id", value=ids, inline=True)
    return embed

def format_tournament_map_list(maps):

    embed = Embed()
    embed.title = "Tournament maps:"

    res = {}
    for (map, tournament) in maps:
        if map in res:
            res[tournament].append(map)
        else:
            res[tournament] = [map]

    for key in res:
        value = ""
        for val in res[key]:
            value += val + "\n"
        embed.add_field(name=key, value=value, inline=False)

    return embed


#infos: [(pos, name, score)]
#   where the first entry is the best time
def format_map_records_embed(map_name, infos):

    embed = Embed()
    embed.title = "Leaderboard for map: " + map_name

    #Format everything nicely inside a code block
    header_format = "{:^3s} {:^15s} {:^16s} \n"
    format =        "{:^3s} {:15s} {:^16s} \n"

    everything = "```\n"
    everything += header_format.format("Pos", "Player", "Time")

    for info in infos:

        (pos, name, score) = info
        everything += format.format(str(pos), name, score)

        if(len(everything) >= 900):
            everything += "```"
            field_name = '\u200b'
            embed.add_field(name=field_name, value=everything, inline=False)

            everything = "```\n"
            everything += header_format.format("Pos", "Player", "Time")

    everything += "```"

    field_name = '\u200b'
    embed.add_field(name=field_name, value=everything, inline=True)

    return embed

def clean_map_name(map_name):
    return re.sub(map_name_regex, "", map_name)
