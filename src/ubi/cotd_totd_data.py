
import requests
from dotenv import find_dotenv, load_dotenv, get_key, set_key
import re
import time

from src.ubi.records import get_map_data, format_map_record

totd_url = "https://live-services.trackmania.nadeo.live/api/token/campaign/month?length=1&offset=0"
cotd_url = "https://meet.trackmania.nadeo.club/api/cup-of-the-day/current"
challenge_url = "https://meet.trackmania.nadeo.club/api/challenges/"

map_name_regex = r"(?i)(?<!\$)((?P<d>\$+)(?P=d))?((?<=\$)(?!\$)|(\$([a-f\d]{1,3}|[ionmwsztg<>]|[lhp](\[[^\]]+\])?)))"


# This function can be quite slow due to sleeps
def get_all_cotd_players():

    # Let's say div5 or better, so 320 players
    # We need 4 requests, 100 + 100 + 100 + 20
    # Adding some sleeps in between requests.

    id = get_cotd_challenge_id()
    if(id == None):
        return None
    #id = 7169 # main cotd 2024-01-23 

    top100 = get_cotd_players(id, 100, 0)
    time.sleep(1)
    top101_200 = get_cotd_players(id, 100, 100)
    time.sleep(1)
    top201_300 = get_cotd_players(id, 100, 200)
    time.sleep(1)
    top301_320 = get_cotd_players(id, 20, 300)

    return top100 + top101_200 + top201_300 + top301_320


#length = how many players
#offset = where to start retrieving players
def get_cotd_players(challenge_id, length, offset):

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
def get_cotd_challenge_id():

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
        print("get_cotd_challenge_id did not receive valid json, returning None. Exception: ",e)
        return None

    challenge_id = res['challenge']['id']
    return challenge_id


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

    return (map_id, map_uid, clean_map_name(map_name))


def clean_map_name(map_name):
    return re.sub(map_name_regex, "", map_name)
