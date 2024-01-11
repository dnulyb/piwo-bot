import config.data as data
import config.settings as settings
import src.db.db as db
from src.ubi.authentication import *
from src.ubi.records import *
from src.gsheet import *
from datetime import datetime



#testing sqlite
db.init()
quit()

# Get access token
#token = authenticate()
#print(token)
token = settings.token

#map_data = get_map_data(data.maps, token)
#print(map_data)
#quit()

# Get map records for each map and player 
player_ids = list(data.player_data.keys())
# records is an array of tuples: [(time, name, map_name), ...]
map_ids = [maps[0] for maps in data.map_data]
records = get_map_records(player_ids, map_ids, token)

print(records)

# Get player and map names
#player_names = list(data.player_data.values())
#map_names = [maps[2] for maps in data.map_data]
