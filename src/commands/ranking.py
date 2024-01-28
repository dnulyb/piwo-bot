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
import json

trophies_url = "https://live-services.trackmania.nadeo.live/api/token/leaderboard/trophy/player"
mm_url = ""

class Ranking(Extension):

    @slash_command(
        name="ranking",
        description="Rankings for trophies / mm / etc.",
        sub_cmd_name="trophies",
        sub_cmd_description="Shows the trophy count leaderboard."
    )
    @cooldown(Buckets.CHANNEL, 1, 3600)
    async def trophies(self, ctx: SlashContext):
        players = get_trophy_counts()
        embed = format_trophy_leaderboard(players)
        await ctx.send(embed=embed)


# Uses the live audience
def get_trophy_counts():

    # Load variables from .env
    dotenv_path = find_dotenv()
    load_dotenv(dotenv_path)

    token = get_key(dotenv_path, ("NADEO_LIVESERVICES_ACCESS_TOKEN"))
    user_agent = get_key(dotenv_path, ("USER_AGENT"))

    # Get player ids from db
    conn = db.open_conn()
    query = (db.get_specific_roster_players, ["cotd"])
    cotd_players = db.retrieve_data(conn, query)
    conn.close()

    player_ids = list(zip(*cotd_players))[1]

    player_list = []
    for player_id in player_ids:
        entry = {}
        entry['accountId'] = player_id
        player_list.append(entry)

    body = {'listPlayer': player_list}
    body = json.dumps(body)    

    headers = {
        'Authorization': "nadeo_v1 t=" + token,
        'User-Agent': user_agent
    }

    # json=body did not work, data=body works
    res = requests.post(trophies_url, headers=headers, data=body)
    res = res.json()

    rankings = res["rankings"]
    players = [(elem["accountId"], elem["countPoint"], elem["zones"][0]["ranking"]["position"])
            for elem in rankings]

    player_trophy_data = []
    for (player_id, player_trophies, player_world_rank) in players:
        for (cotd_player_name, cotd_player_id) in cotd_players:
            if player_id == cotd_player_id:
                player_trophy_data.append((cotd_player_name, player_trophies, player_world_rank))

    sorted_results = sorted(player_trophy_data, key=lambda x:x[2])

    return sorted_results


def format_trophy_leaderboard(players):


    embed = Embed()
    embed.title = "Trophy rankings"
    field_name = '\u200b'

    #Format everything nicely inside a code block
    # Pos WorldRank Player Trophies
    header_format = "{:^3s} {:^10s} {:^15s} {:^12s} \n"
    format =        "{:^3s} {:^10s} {:15s} {:^12s} \n"

    i = 1

    for player in players:
        value = "```\n"
        value += header_format.format("Pos", "World rank", "Player", "Trophies")

        (name, trophies, world_rank) = player
        pos = str(i) + "."
        trophies = str(trophies)
        world_rank = str(world_rank)
        value += format.format(pos, world_rank, name, trophies)
        i += 1

        value += "```"

        if(len(value) >= 900):
            embed.add_field(name=field_name, value=value, inline=False)
            value = ""

    return embed