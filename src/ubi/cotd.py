"""
get cotd info: https://webservices.openplanet.dev/meet/cup-of-the-day/current

get the cotd challenge info: https://webservices.openplanet.dev/meet/competitions/rounds
                             https://webservices.openplanet.dev/meet/challenges/leaderboard


What we want: 

    1. Get cotd map info when cotd starts
    2. See result of cotd quali for registered players

"""

import requests
from dotenv import find_dotenv, load_dotenv, get_key
import re

from src.ubi.records import get_map_data

totd_url = "https://live-services.trackmania.nadeo.live/api/token/campaign/month?length=1&offset=0"
cotd_url = "https://meet.trackmania.nadeo.club/api/cup-of-the-day/current"

map_name_regex = r"(?i)(?<!\$)((?P<d>\$+)(?P=d))?((?<=\$)(?!\$)|(\$([a-f\d]{1,3}|[ionmwsztg<>]|[lhp](\[[^\]]+\])?)))"


def get_cotd_info():

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
    res = res.json()

    print(res)


# Return: (map_id, map_uid, map_name)
def get_totd_map_info():

    dotenv_path = find_dotenv()
    load_dotenv(dotenv_path)

    # Using the NadeoClubServices audience
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

    return (map_id, map_uid, map_name)


def clean_map_name(map_name):
    return re.sub(map_name_regex, "", map_name)
