import requests
from dotenv import find_dotenv, load_dotenv
import os

map_record_url = "https://prod.trackmania.core.nadeo.online/mapRecords/"
    
# Get map records for a list of accounts and a list of map ids
def get_map_records(account_ids, map_ids, token):

    # Load variables from .env
    dotenv_path = find_dotenv()
    load_dotenv(dotenv_path)

    token = os.getenv("NADEO_ACCESS_TOKEN")
    user_agent = os.getenv("USER_AGENT")

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
    
    for record in records:
        record[0] = format_map_record(record[0])

    # Convert ids to readable values, format the data correctly
    # not working atm
    #records = list(map(get_record_tuple, records))

    return records

# Converts a record time of format "42690" to "42.690"
def format_map_record(record):
    record = str(record)
    return record[:-3] + "." + record[-3:]

# Converts record ids to names, and formats everything nicely.
"""
def get_record_tuple(record, players, maps):

    #record is of the form (time, account_id, map_id)

    time = format_map_record(record[0])
    name = players[record[1]]
    map = None

    #Get map name
    for m in maps:
        if m[0] == record[2]:
            map = m[3] #m[2]

    return (time, name, map)
"""

