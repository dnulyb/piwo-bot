from interactions import(
    Embed
)

import src.db.db as db
from src.ubi.cotd_totd_data import get_all_cotd_players
import math


def get_cotd_quali_results():

    conn = db.open_conn()
    query = (db.get_specific_roster_players, ["cotd"])
    cotd_players = db.retrieve_data(conn, query)
    conn.close()

    players = get_all_cotd_players()

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
    embed.title = map_name

    all_positions = ""
    all_players = ""
    all_times = ""
    all_divs = ""

    for result in results:
        (name, rank, time) = result
        division = div(rank)
        all_positions += str(rank) + "\n"
        all_players += name + "\n"
        all_times += time + "\n"
        all_divs += str(division) + "\n"

    embed.add_field(name="Rank", value=all_positions, inline=True)
    embed.add_field(name="Player", value=all_players, inline=True)
    embed.add_field(name="Time", value=all_times, inline=True)
    embed.add_field(name="Division", value=all_divs, inline=True)


def div(pos):
    return math.ceil(pos/64)