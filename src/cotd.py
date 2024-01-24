from interactions import(
    Embed
)

import src.db.db as db
from src.ubi.cotd_totd_data import get_all_cotd_players
import math

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
