import config.data as data
import config.settings as settings
from src.db.db import *
from src.ubi.authentication import *
from src.ubi.records import *
from src.gsheet import *
from datetime import datetime



#testing sqlite
#db.init()

#after these nine queries we should have 1 testroster
#   and 2 players (1,3)
execute_query(add_roster, ["testroster"])
execute_query(add_roster, ["testroster2"])
execute_query(remove_roster, ["testroster2"])

execute_query(remove_player, ["player one"])
execute_query(remove_player, ["player two"])
execute_query(remove_player, ["player three"])

execute_query(add_player, ("player one", "1", None))
execute_query(add_player, ("player two", "2", "test"))
execute_query(add_player, ("player three", "3", "testroster"))
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
