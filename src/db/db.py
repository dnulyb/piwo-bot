import sqlite3
import os.path
from dotenv import find_dotenv, load_dotenv, get_key

# Create db file path
dotenv_path = find_dotenv()
load_dotenv(dotenv_path)
db_filename = get_key(dotenv_path, "DB_FILE")
db_file = os.path.join(os.path.dirname(__file__), db_filename)
db_init_sql = os.path.join(os.path.dirname(__file__), "team.sql")

#TODO: Figure out a better way to do this
add_roster =            """ INSERT INTO Roster(name, tournament_id)
                            VALUES(?,?) """

remove_roster =         """ DELETE FROM Roster
                            WHERE name=? COLLATE NOCASE"""

list_rosters =          """ SELECT Roster.name, Tournament.name
                            FROM Roster
                            JOIN Tournament ON Roster.tournament_id = Tournament.id 
                            ORDER BY Tournament.name, Roster.name """

get_specific_roster_players = """   SELECT Player.nickname, Player.account_id
                                    FROM Participant
                                    JOIN Player ON Participant.player_id = Player.id
                                    JOIN Roster ON Participant.roster_id = Roster.id
                                    WHERE Roster.name=? COLLATE NOCASE
                                    ORDER BY Player.nickname
                                """

get_roster_players =    """ SELECT Player.nickname, Player.account_id, Roster.name
                            FROM Participant
                            JOIN Player ON Participant.player_id = Player.id
                            JOIN Roster ON Participant.roster_id = Roster.id
                            ORDER BY Roster.name, Player.nickname
                        """

get_tournament_roster_players = """ 
                                SELECT Player.nickname, Player.account_id, Roster.name
                                FROM Participant
                                JOIN Player ON Participant.player_id = Player.id
                                JOIN Roster ON Participant.roster_id = Roster.id
                                WHERE Roster.tournament_id=?
                                ORDER BY Roster.name, Player.nickname
                                """

get_tournament_rosters =    """
                            SELECT name
                            FROM Roster
                            WHERE Roster.tournament_id=?
                            """

get_roster_id =         """ SELECT id
                            FROM Roster
                            WHERE name=? COLLATE NOCASE"""

add_player =            """ INSERT INTO Player(nickname, account_id, country, official_roster, extra)
                            VALUES(?,?,?,?,?) """

remove_player =         """ DELETE FROM Player
                            WHERE nickname=? COLLATE NOCASE"""

list_players =          """ SELECT nickname, country, official_roster
                            FROM Player 
                            ORDER BY (Player.id) """

update_player_name= """ UPDATE Player
                            SET nickname=?
                            WHERE nickname=? COLLATE NOCASE"""

update_player_account_id= """ UPDATE Player
                            SET account_id=?
                            WHERE nickname=? COLLATE NOCASE"""

update_player_country = """ UPDATE Player
                            SET country=?
                            WHERE nickname=? COLLATE NOCASE"""

update_player_official_roster = """ UPDATE Player
                                    SET official_roster=?
                                    WHERE nickname=? COLLATE NOCASE"""

update_player_extra =           """ UPDATE Player
                                    SET extra=?
                                    WHERE nickname=? COLLATE NOCASE"""

get_player_info =           """ SELECT nickname, account_id, country, official_roster
                                FROM Player
                                WHERE nickname=? COLLATE NOCASE
                            """
                            

get_player_id =         """ SELECT id
                            FROM Player
                            WHERE nickname=? COLLATE NOCASE"""

get_player_id_by_account_id = """ SELECT id
                            FROM Player
                            WHERE account_id=? """

get_players_by_official_roster = """ SELECT nickname, country, extra
                                     FROM Player
                                     WHERE official_roster=? COLLATE NOCASE
                                     ORDER BY (Player.id)
                                 """

add_tournament =        """ INSERT INTO Tournament(name)
                            VALUES(?) """

remove_tournament =     """ DELETE FROM Tournament
                            WHERE name=? COLLATE NOCASE"""

list_tournaments =      """ SELECT name, auto_update
                            FROM Tournament 
                            ORDER BY (name) """

auto_update_tournament = """ UPDATE Tournament
                             SET auto_update=?
                             WHERE name=? COLLATE NOCASE"""

get_tournament_id =     """ SELECT id
                            FROM Tournament
                            WHERE name=? COLLATE NOCASE"""

get_tournament_name =   """ SELECT name
                            FROM Tournament
                            WHERE id=? """


add_map =               """ INSERT INTO Map(name, uid)
                            VALUES(?,?) """

remove_map =            """ DELETE FROM Map
                            WHERE name=? COLLATE NOCASE"""

update_map_id=          """ UPDATE Map
                            SET uid=?
                            WHERE name=? COLLATE NOCASE"""

get_map_id =            """ SELECT id
                            FROM Map
                            WHERE name=? COLLATE NOCASE"""

get_map_uid =            """ SELECT uid
                            FROM Map
                            WHERE name=? COLLATE NOCASE"""

get_map_db_id_by_map_id = """ SELECT id
                            FROM Map
                            WHERE uid=? """

add_participant =       """ INSERT INTO Participant(player_id, roster_id)
                            VALUES(?,?) """

remove_participant =    """ DELETE FROM Participant
                            WHERE player_id=? AND roster_id=? """

add_time =              """ INSERT INTO Time(player_id, map_id, time)
                            VALUES(?,?,?) 
                                ON CONFLICT (player_id, map_id) DO
                                UPDATE SET time=excluded.time"""

get_n_map_times =       """ SELECT Player.nickname, Time.time  
                            FROM Map
                            JOIN Time ON Time.map_id = Map.id
                            JOIN Player ON Player.id = Time.player_id
                            WHERE Map.name=? COLLATE NOCASE
                            ORDER BY LENGTH(Time.time) ASC, CAST (Time.time AS DECIMAL) ASC
                            LIMIT ?
                        """

get_n_map_times_from_roster = """
                                SELECT Player.nickname, Time.time  
                                FROM Map
                                JOIN Time ON Time.map_id = Map.id
                                JOIN Player ON Player.id = Time.player_id
                                JOIN Participant ON Player.id = Participant.player_id
                                WHERE Map.name=? COLLATE NOCASE
                                AND Participant.roster_id=?
                                ORDER BY LENGTH(Time.time) ASC, CAST (Time.time AS DECIMAL) ASC
                                LIMIT ?
                                """

add_to_mappack =        """ INSERT INTO Mappack(tournament_id, map_id)
                            VALUES(?,?) """

remove_from_mappack =   """ DELETE FROM Mappack
                            WHERE map_id=? """

get_tournament_from_map =   """
                                SELECT Tournament.id
                                FROM Map
                                JOIN Mappack ON Map.id = Mappack.map_id
                                JOIN Tournament ON Mappack.tournament_id = Tournament.id
                                WHERE Map.name=? COLLATE NOCASE
                                """

get_maps =              """ SELECT name, uid
                            FROM Map
                            ORDER BY name
                        """

get_tournament_maps =   """ SELECT Map.name, Map.uid
                            FROM Mappack
                            JOIN Map ON Mappack.map_id = Map.id
                            JOIN Tournament ON Mappack.tournament_id = Tournament.id
                            WHERE Tournament.id=?
                            ORDER BY Map.name
                        """

get_player_tournament_times =   """
                                SELECT player_id, map_id, time
                                FROM Time
                                WHERE map_id IN
                                    (SELECT map_id
                                        FROM Mappack
                                        WHERE tournament_id = ?
                                    )
                                AND player_id = ?
                                """

get_player_time =   """
                    SELECT time
                    FROM Time
                    WHERE map_id = ?
                    AND player_id = ?
                    """

add_to_teaminfo =       """ INSERT INTO TeamInfo(name, info)
                            VALUES(?,?) 
                                ON CONFLICT (name) DO
                                UPDATE SET info=excluded.info """

remove_teaminfo =       """ DELETE FROM TeamInfo
                            WHERE name=? COLLATE NOCASE"""

get_teaminfo =          """ SELECT info
                            FROM TeamInfo
                            WHERE name=? COLLATE NOCASE"""

get_teaminfo_list =     """ SELECT name, info
                            FROM TeamInfo
                        """

add_twitch_channel =    """ INSERT INTO TwitchChannel(name)
                            VALUES(?)
                        """

remove_twitch_channel = """ DELETE FROM TwitchChannel
                            WHERE name=? COLLATE NOCASE"""

get_twitch_list =       """ SELECT name
                            FROM TwitchChannel
                        """

add_gsheet =            """INSERT INTO GoogleSheet(sheet_name, sheet_number, tournament_id)
                           VALUES(?,?,?)
                        """
remove_gsheet =         """ DELETE FROM GoogleSheet
                            WHERE sheet_name=? COLLATE NOCASE"""

get_gsheet =            """ SELECT sheet_name, sheet_number
                            FROM GoogleSheet
                            WHERE tournament_id=?"""

def open_conn():
    conn = sqlite3.connect(db_file)
    conn.execute("PRAGMA foreign_keys = 1")
    return conn

# Creates the initial database structure
def init():

    try:
        f = open(db_file, "x")
        print("db file created")
    except FileExistsError:
        print("db file already exists, no new file created")

    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    init_query = open(db_init_sql, "r").read()
    cursor.executescript(init_query)

    cursor.close()
    conn.close()

def run_script(script):

    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    cursor.executescript(script)

    cursor.close()
    conn.close()


# Executes all queries provided, queries is a list of (sql, params)
#   Single param has to be in the form [a]
#   Multiple params has to be in the form (a,b,c) (for 3 parameters a, b and c) 
def execute_queries(conn, queries):

    cursor = conn.cursor()

    for (sql, param) in queries:
            
        try:
            # Check if there are parameters
            if param == None:
                print("none param")
                cursor.execute(sql)
            else:
                cursor.execute(sql, param)
        except sqlite3.IntegrityError as e:
            raise Exception(e)
        except sqlite3.Error as e:
            print(e, end="")
            print(" : ", end="")
            print(param)

    conn.commit()
    cursor.close()

def retrieve_data(conn, query):

    cursor = conn.cursor()
    (sql, param) = query

    try:
        # Check if there are parameters
        if param == None:
            cursor.execute(sql)
        else:
            cursor.execute(sql, param)
    except sqlite3.Error as e:
        print(e, end="")
        print(" : ", end="")
        print(param)

    conn.commit()

    res = cursor.fetchall()
    cursor.close()

    return res


# Returns None if the tournament cannot be found
def get_tournament_db_id(conn, tournament):

    tournament_id = retrieve_data(conn, (get_tournament_id, [tournament]))
    if(len(tournament_id) == 0):
        return None
    
    return tournament_id[0][0]




