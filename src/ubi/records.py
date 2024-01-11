import requests
import config.data as data
from config.settings import user_agent

map_info_url = "https://prod.trackmania.core.nadeo.online/maps/?mapUidList="
map_record_url = "https://prod.trackmania.core.nadeo.online/mapRecords/"

# Get map information from a map uid
def get_map_data(map_uids, token):

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

    
# Get map records for a list of accounts and a list of map ids
def get_map_records(account_ids, map_ids, token):

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

    # Convert ids to readable values, format the data correctly
    records = list(map(get_record_tuple, records))

    return records

# Converts a record time of format "42690" to "42.690"
def format_map_record(record):
    record = str(record)
    return record[:-3] + "." + record[-3:]

# Converts record ids to names, and formats everything nicely.
def get_record_tuple(record):

    time = format_map_record(record[0])
    name = data.player_data[record[1]]
    map = None

    #Get map name
    for m in data.map_data:
        if m[0] == record[2]:
            map = m[2]

    return (time, name, map)

