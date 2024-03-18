import requests
from dotenv import find_dotenv, load_dotenv, get_key
import time
import re

from src.gsheet import google_sheet_write, google_sheet_write_batch
from src.ubi.authentication import authenticate, check_token_refresh, get_nadeo_access_token
from src.commands.map import get_map_records, format_map_record

#import src.other.data as data

map_name_regex = r"(?i)(?<!\$)((?P<d>\$+)(?P=d))?((?<=\$)(?!\$)|(\$([a-f\d]{1,3}|[ionmwsztg<>]|[lhp](\[[^\]]+\])?)))"

def clean_map_name(map_name):
    return re.sub(map_name_regex, "", map_name)

#map information
def get_map_infos(map_id_list):


    check_token_refresh()

    map_info_url = "https://prod.trackmania.core.nadeo.online/maps/"

    # Load variables from .env
    dotenv_path = find_dotenv()
    load_dotenv(dotenv_path)

    token = get_key(dotenv_path, ("NADEO_ACCESS_TOKEN"))
    user_agent = get_key(dotenv_path, ("USER_AGENT"))

    # Build url
    map_id_str = ','.join(map_id_list)

    complete_url = map_info_url + \
                    "?mapIdList=" + map_id_str

    # Send get request

    headers = {
        'Authorization': "nadeo_v1 t=" + token,
        'User-Agent': user_agent
    }

    res = requests.get(complete_url, headers=headers)
    res = res.json()

    map_info = [[elem["name"],
                elem["mapId"],
                elem["mapUid"]]
                for elem in res]

    return map_info


#return: (wr, top10, top50, top100)
def get_map_leaderboard_info(map_uid):

    leaderboard_url = "https://live-services.trackmania.nadeo.live/api/token/leaderboard/group/"
    groupUid = "Personal_Best"
    length = "100"
    onlyWorld = "true"
    offset = "0"

    # Load variables from .env
    dotenv_path = find_dotenv()
    load_dotenv(dotenv_path)

    token = get_key(dotenv_path, ("NADEO_LIVESERVICES_ACCESS_TOKEN"))
    user_agent = get_key(dotenv_path, ("USER_AGENT"))

    # Build url
    complete_url = leaderboard_url + \
                    groupUid + \
                    "/map/" + \
                    map_uid + \
                    "/top?length=" + \
                    length + \
                    "&onlyWorld=" + \
                    onlyWorld + \
                    "&offset=" + \
                    offset

    # Send get request

    headers = {
        'Authorization': "nadeo_v1 t=" + token,
        'User-Agent': user_agent
    }

    res = requests.get(complete_url, headers=headers)
    res = res.json()

    #Extract the relevant scores
    scores = res["tops"][0]["top"]
    scores = [score["score"] for score in scores]
    wr = scores[0]
    top10 = scores[9]
    top50 = scores[49]
    top100 = scores[99]

    return(wr, top10, top50, top100)


def get_map_playercount(map_uid):


    leaderboard_url = "https://live-services.trackmania.nadeo.live/api/token/leaderboard/group/"
    groupUid = "Personal_Best"
    lower = "1"
    upper = "1"
    score = "1000000"

    # Load variables from .env
    dotenv_path = find_dotenv()
    load_dotenv(dotenv_path)

    token = get_key(dotenv_path, ("NADEO_LIVESERVICES_ACCESS_TOKEN"))
    user_agent = get_key(dotenv_path, ("USER_AGENT"))
    
    # Build url
    complete_url = leaderboard_url + \
                    groupUid + \
                    "/map/" + \
                    map_uid + \
                    "/surround/" + \
                    lower + \
                    "/" + \
                    upper + \
                    "?score=" + \
                    score
    
    # Send get request

    headers = {
        'Authorization': "nadeo_v1 t=" + token,
        'User-Agent': user_agent
    }

    res = requests.get(complete_url, headers=headers)
    res = res.json()

    scores = res["tops"][0]["top"]
    #last score on leaderboard has playercount position
    playercount = scores[0]["position"]

    return playercount

#print(get_map_leaderboard_info("HxqgQkvRDW0_z83PrrzQfoRvZp"))
#print(get_map_playercount("HxqgQkvRDW0_z83PrrzQfoRvZp"))



#Get all the info printed out
#print(res)
"""
check_token_refresh()
sorted_map_info = []
for map_id in data.map_id_list:
    for map_info in data.map_info_list:

        if(map_id is map_info[1]):
            sorted_map_info.append(map_info)
"""
"""
map_leaderboard_infos = []
count = 0
for (_, _, map_uid) in sorted_map_info:

    (wr, top10, top50, top100) = get_map_leaderboard_info(map_uid)
    playercount = get_map_playercount(map_uid)
    map_leaderboard_infos.append((wr, top10, top50, top100, playercount))

    time.sleep(0.5)

    count = count + 1
    print(count)


print(map_leaderboard_infos)


#player info
players = list(zip(data.player_name_list, data.player_id_list))
#print(players)

#check_token_refresh()
#token = get_nadeo_access_token()
#res = get_map_records(data.player_id_list, data.map_id_list, token)
res = data.times


all_players = []
for (player_name, player_id) in players:

    player_times = []

    for map in data.map_id_list:

        played = False
        for (res_record, res_player_id, res_map_id) in res:

            if (player_id == res_player_id and
                map == res_map_id):

                played = True
                record = format_map_record(res_record, False)
                player_times.append(record)
                #print(player_name, res_record, res_map_id)

        #Add empty record if the map has not been played
        if(not played):
            player_times.append("")

    all_players.append((player_name, player_times))

#print(all_players)

#map info
sorted_map_info = []
for map_id in data.map_id_list:
    for map_info in data.map_info_list:

        if(map_id is map_info[1]):
            sorted_map_info.append(map_info)

#Each element in res is a tuple of 
#    ( [mapname, mapid, mapuid], (wr, top10, top50, top100, playercount) )
all_mapinfo = list(zip(sorted_map_info, data.map_leaderboard_info_list))


#Write player times to google sheet

"""
"""
ranges = []
start_col = "A"
start_row = 11
final_items = []
for (name, times) in all_players:
    range = range = start_col + str(start_row) + ":AZ" + str(start_row)
    ranges.append(range)
    start_row += 1

    times.insert(0, name)
    final_items.append([times])


sheet_name = "emc s6 analysis"
sheet_number = 1

dotenv_path = find_dotenv()
load_dotenv(dotenv_path)
credentials = get_key(dotenv_path, "CREDENTIALS_FILE")

google_sheet_write_batch(ranges, final_items, True, sheet_name, sheet_number, credentials)
"""

#Write map info to google sheet
"""
final_infos = []
for ([mapname, mapid, mapuid], (wr, top10, top50, top100, playercount)) in all_mapinfo:
    mapname = clean_map_name(mapname)
    wr = format_map_record(wr, False)
    top10 = format_map_record(top10, False)
    top50 = format_map_record(top50, False)
    top100 = format_map_record(top100, False)
    final_infos.append((mapname, mapid, mapuid, wr, top10, top50, top100, playercount))

#print(final_infos)
ranges = []
start_col = "B"
start_row = 1
final_items = []
i = 0
for item in final_infos[0]:
    range = range = start_col + str(start_row) + ":AZ" + str(start_row)
    ranges.append(range)
    start_row += 1
    final_items.append([[elem[i] for elem in final_infos]])
    i += 1

sheet_name = "emc s6 analysis"
sheet_number = 1

dotenv_path = find_dotenv()
load_dotenv(dotenv_path)
credentials = get_key(dotenv_path, "CREDENTIALS_FILE")

google_sheet_write_batch(ranges, final_items, True, sheet_name, sheet_number, credentials)
"""

#print(res[0])

#for (map_name, map_id, map_uid) in sorted_map_info:
#    map_name = clean_map_name(map_name)
#    #print(map_name, map_id, map_uid)


#mapinfo url
#name
#id
#uid


#wr
#10
#50
#playercount


        
