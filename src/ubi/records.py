import requests
from dotenv import find_dotenv, load_dotenv, get_key

map_record_url = "https://prod.trackmania.core.nadeo.online/mapRecords/"
map_info_url = "https://prod.trackmania.core.nadeo.online/maps/?mapUidList="
    
# Get map records for a list of accounts and a list of map ids
def get_map_records(account_ids, map_ids, token):

    # Load variables from .env
    dotenv_path = find_dotenv()
    load_dotenv(dotenv_path)

    token = get_key(dotenv_path, ("NADEO_ACCESS_TOKEN"))
    user_agent = get_key(dotenv_path, ("USER_AGENT"))

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
    
    # Format time correctly
    for record in records:
        record[0] = format_map_record(record[0])

    return records

# Converts a record time of format "42690" to "42.690"
def format_map_record(record):
    record = str(record)
    return record[:-3] + "." + record[-3:]



# Get map information from a map uid
def get_map_data(map_uids):

    # Load variables from .env
    dotenv_path = find_dotenv()
    load_dotenv(dotenv_path)

    token = get_key(dotenv_path, ("NADEO_ACCESS_TOKEN"))
    user_agent = get_key(dotenv_path, ("USER_AGENT"))

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
