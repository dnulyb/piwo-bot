import config.data as data
import config.settings as settings
from src.db.db import *
from src.ubi.authentication import *
from src.ubi.records import *
from src.gsheet import *
from datetime import datetime


#testing sqlite
init()

#after these nine queries we should have 1 testroster
#   and 2 players (1,3)
queries = [
    [add_roster, ["testroster"]],
    [add_roster, ["testroster2"]],
    [remove_roster, ["testroster2"]],
    [remove_player, ["player one"]],
    [remove_player, ["player two"]],
    [remove_player, ["player three"]],
    [add_player, ("player one", "1", None)],
    [add_player, ("player two", "2", "test")],
    [add_player, ("player three", "3", "testroster")]
]

queries2 = [
    [add_map, ("firstmap", "19324-asd234")],
    [add_time, (2,1,"goodtime")],
    [add_time, (2,1,"evenbettertime")],
    [add_tournament, ["wtt"]],
    [add_participant, (1,1)],
    [add_participant, (2,1)],
    [remove_participant, (2,1)]

]

queries3 = [
    add_tournament, ["first tournament"]
]

queries4 = [(add_tournament, ["lol"])]
#print(queries3)

conn = open_conn()
execute_queries(conn, queries4)
res = retrieve_data(conn, (list_tournaments, None))
print(res)

conn.close()

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
