from interactions import (
    Extension,
    slash_command, 
    SlashContext,
    Embed,
    cooldown,
    Buckets
)

import src.db.db as db

from dotenv import find_dotenv, load_dotenv, get_key
import requests
import json

trophies_url = "https://live-services.trackmania.nadeo.live/api/token/leaderboard/trophy/player"
mm_url = "https://meet.trackmania.nadeo.club/api/matchmaking/2/leaderboard/players?"

class Ranking(Extension):

    @slash_command(
        name="ranking",
        description="Rankings for trophies / mm / etc.",
        sub_cmd_name="trophies",
        sub_cmd_description="Shows the trophy count leaderboard.",
        dm_permission=False
    )
    @cooldown(Buckets.CHANNEL, 1, 3600)
    async def trophies(self, ctx: SlashContext):
        players = get_trophy_counts()
        embed = format_trophy_leaderboard(players)
        await ctx.send(embed=embed)

    @slash_command(
        name="ranking",
        sub_cmd_name="mm",
        sub_cmd_description="Shows the mm leaderboard.",
        dm_permission=False
    )
    @cooldown(Buckets.CHANNEL, 1, 900)
    async def mm(self, ctx: SlashContext):
        players = get_mm_ranks()
        embed = format_mm_leaderboard(players)
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

# Uses club audience
def get_mm_ranks():

    # Load variables from .env
    dotenv_path = find_dotenv()
    load_dotenv(dotenv_path)

    token = get_key(dotenv_path, ("NADEO_CLUBSERVICES_ACCESS_TOKEN"))
    user_agent = get_key(dotenv_path, ("USER_AGENT"))

    # Get player ids from db
    conn = db.open_conn()
    query = (db.get_specific_roster_players, ["cotd"])
    cotd_players = db.retrieve_data(conn, query)
    conn.close()

    player_ids = list(zip(*cotd_players))[1]

    complete_url = mm_url
    first = True
    for player_id in player_ids:
        if(first):
            complete_url += "players[]="
            first = False
        else:
            complete_url += "&players[]="

        complete_url += player_id
        
    headers = {
        'Authorization': "nadeo_v1 t=" + token,
        'User-Agent': user_agent
    }
    res = requests.get(complete_url, headers=headers)
    res = res.json()

    rankings = res["results"]
    players = [(elem["player"], elem["rank"], elem["score"])
            for elem in rankings]

    player_rank_data = []
    for (player_id, player_world_rank, player_mm_score) in players:
        # Ignore players that don't play mm
        if(player_mm_score == 0):
            continue
        for (cotd_player_name, cotd_player_id) in cotd_players:
            if player_id == cotd_player_id:
                player_rank_data.append((cotd_player_name, player_world_rank, player_mm_score))

    sorted_results = sorted(player_rank_data, key=lambda x:x[1])

    return sorted_results


def format_trophy_leaderboard(players):

    embed = Embed()
    embed.title = "Trophy rankings"
    field_name = '\u200b'

    #Format everything nicely inside a code block
    # Pos WorldRank Player Trophies
    header_format = "{:^3s} {:^9s} {:^15s} {:^12s} \n"
    format =        "{:^3s} {:^9s} {:15s} {:^12s} \n"

    value = ""
    value += "```\n"
    value += header_format.format("Pos", "World rank", "Player", "Trophies")
    for i, player in enumerate(players, start=1):
        
        (name, trophies, world_rank) = player
        pos = str(i) + "."
        trophies = str(trophies)
        world_rank = str(world_rank)
        value += format.format(pos, world_rank, name, trophies)

        # Have we almost reached the embed value limit?
        if(len(value) >= 900):
            value += "```"
            embed.add_field(name=field_name, value=value, inline=False)

            # Are there more players?
            if(i < len(players)):
                value = ""
                value += "```\n"
            else:
                #If not, we can just return
                return embed

    value += "```"
    embed.add_field(name=field_name, value=value, inline=False)


    return embed

def format_mm_leaderboard(players):

    embed = Embed()
    embed.title = "MM rankings"
    field_name = '\u200b'

    #Format everything nicely inside a code block
    # Pos WorldRank Player Score
    header_format = "{:^3s} {:^9s} {:^15s} {:^12s} \n"
    format =        "{:^3s} {:^9s} {:15s} {:^12s} \n"

    value = ""
    value += "```\n"
    value += header_format.format("Pos", "World rank", "Player", "Score")
    for i, player in enumerate(players, start=1):
        
        (name, world_rank, score) = player
        pos = str(i) + "."
        score = str(score)
        world_rank = str(world_rank)
        value += format.format(pos, world_rank, name, score)

        # Have we almost reached the embed value limit?
        if(len(value) >= 900):
            value += "```"
            embed.add_field(name=field_name, value=value, inline=False)

            # Are there more players?
            if(i < len(players)):
                value = ""
                value += "```\n"
            else:
                #If not, we can just return
                return embed

    value += "```"
    embed.add_field(name=field_name, value=value, inline=False)


    return embed