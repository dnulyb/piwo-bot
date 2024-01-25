from interactions import (
    Extension,
    slash_command, 
    slash_option, 
    SlashContext,
    OptionType,
    Embed,
    cooldown,
    Buckets
)

import src.db.db as db
from src.ubi.cotd_totd_data import get_all_cotd_players
import math
from dotenv import find_dotenv, load_dotenv, get_key
from src.ubi.authentication import get_nadeo_access_token
from src.ubi.records import get_map_records



class Cotd(Extension):

    #Get updated totd leaderboard
    @slash_command(
        name="totd",
        description="Updates TOTD times, and shows the current leaderboard."
    )
    @cooldown(Buckets.GUILD, 1, 60)
    async def totd_leaderboard(self, ctx: SlashContext):

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
                    totd_results.append((cotd_player_name, player_time))

        sorted_results = sorted(totd_results, key=lambda x:x[1])

        embed = format_totd_leaderboard(totd_name, sorted_results)

        await ctx.send(embed=embed)



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
    header_format = "{:^3s} {:^5s} {:^15s} {:^10s} \n"
    format =        "{:^3s} {:^5s} {:15s} {:^10s} \n"

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
    header_format = "{:^3s} {:^15s} {:^10s} \n"
    format =        "{:^3s} {:15s} {:^10s} \n"

    everything = "```\n"
    everything += header_format.format("Pos", "Player", "Time")

    for i, player in enumerate(players, start=1):
        (name, time) = player
        pos = str(i) + "."
        everything += format.format(pos, name, time)
        
    everything += "```"

    field_name = '\u200b'
    embed.add_field(name=field_name, value=everything, inline=True)

    return embed
