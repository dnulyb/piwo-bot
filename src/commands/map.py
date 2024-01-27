from interactions import (
    Extension,
    slash_command, 
    slash_option, 
    SlashContext,
    OptionType,
    Embed
)
import src.db.db as db
from src.commands.tournament import get_tournament_id

import requests
from dotenv import find_dotenv, load_dotenv, get_key

map_record_url = "https://prod.trackmania.core.nadeo.online/mapRecords/"
map_info_url = "https://prod.trackmania.core.nadeo.online/maps/?mapUidList="

class Map(Extension):

    @slash_command(
        name="map",
        sub_cmd_name="add",
        sub_cmd_description="Adds a map to a tournament."
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
            tournament_id = get_tournament_id(conn, tournament)

            if tournament_id == None:
                await ctx.send(f"Error occurred while running command: Tournament '{tournament}' not found")
                conn.close()
                return

            # Add the map to "Map" table
            #TODO: Change "uid" to "id" or something more fitting, in Map table
            db.execute_queries(conn, [(db.add_map, (map_name, map_id))])


            # Add the tournament and map to "Mappack" table
            map_database_id = db.retrieve_data(conn, (db.get_map_id, [map_name]))
            if(len(map_database_id) == 0):
                await ctx.send(f"Error occurred while running command: Map '{map}' not found")
                conn.close()
                return
            map_database_id = map_database_id[0][0]
        
            db.execute_queries(conn, [(db.add_to_mappack, (tournament_id, map_database_id))])

            await ctx.send("Added map to tournament '" + tournament + "': " + map_name)

        except Exception as e:
            await ctx.send(f"Error occurred while running command: {e}")
        finally:
            conn.close() 

    @slash_command(
        name="map",
        sub_cmd_name="delete",
        sub_cmd_description="Delete a map."
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
                await ctx.send(f"Error occurred while running command: Map '{map_name}' not found")
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
            await ctx.send(f"Error occurred while running command: {e}")
        finally:
            conn.close() 

    @slash_command(
        name="list",
        sub_cmd_name="maps",
        sub_cmd_description="Lists all maps."
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
                    await ctx.send("Error while retrieving maps: No maps found.")
                    return
                
                embed = format_map_list(res)
                await ctx.send(embed=embed)
            else:
                tournament_id = get_tournament_id(conn, tournament)

                if tournament_id == None:
                    await ctx.send(f"Error occurred while running command: Tournament '{tournament}' not found")
                    conn.close()
                    return
                query = (db.get_tournament_maps, [tournament_id])
                res = db.retrieve_data(conn, query)
                if(len(res) == 0):
                    await ctx.send("Error while retrieving maps: No maps found.")
                    return
                
                embed = format_tournament_map_list(res)
                await ctx.send(embed=embed)


            
        except Exception as e:
            await ctx.send(f"Error occurred while running command: {e}")
        finally:
            conn.close() 


# Get map records for a list of accounts and a list of map ids
def get_map_records(account_ids, map_ids, token):

    # Load variables from .env
    dotenv_path = find_dotenv()
    load_dotenv(dotenv_path)

    token = get_key(dotenv_path, ("NADEO_ACCESS_TOKEN"))
    user_agent = get_key(dotenv_path, ("USER_AGENT"))

    # Build url
    account_id_str = ','.join(account_ids)
    map_id_str = ','.join(map_ids)

    complete_url = map_record_url + \
                    "?accountIdList=" + account_id_str + \
                    "&mapIdList=" + map_id_str
    
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
    
    # Format time correctly
    for record in records:
        record[0] = format_map_record(record[0])

    return records

# Converts a record time of format "42690" to "42.690"
def format_map_record(record):
    record = str(record)
    return record[:-3] + "." + record[-3:]



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


