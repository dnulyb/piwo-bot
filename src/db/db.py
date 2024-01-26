import sqlite3
import os.path

db_file = os.path.join(os.path.dirname(__file__), "team.sqlite")
db_init_sql = os.path.join(os.path.dirname(__file__), "team.sql")

#TODO: Figure out a better way to do this
add_roster =            """ INSERT INTO Roster(name, tournament_id)
                            VALUES(?,?) """

remove_roster =         """ DELETE FROM Roster
                            WHERE name=? """

list_rosters =          """ SELECT Roster.name, Tournament.name
                            FROM Roster
                            JOIN Tournament ON Roster.tournament_id = Tournament.id 
                            ORDER BY Tournament.name, Roster.name """

get_specific_roster_players = """   SELECT Player.nickname, Player.account_id
                                    FROM Participant
                                    JOIN Player ON Participant.player_id = Player.id
                                    JOIN Roster ON Participant.roster_id = Roster.id
                                    WHERE Roster.name=?
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

get_roster_id =         """ SELECT id
                            FROM Roster
                            WHERE name=? """

add_player =            """ INSERT INTO Player(nickname, account_id, country, official_roster, extra)
                            VALUES(?,?,?,?,?) """

remove_player =         """ DELETE FROM Player
                            WHERE nickname=? """

list_players =          """ SELECT nickname, country, official_roster
                            FROM Player 
                            ORDER BY (Player.id) """

update_player_name= """ UPDATE Player
                            SET nickname=?
                            WHERE nickname=? """

update_player_account_id= """ UPDATE Player
                            SET account_id=?
                            WHERE nickname=? """

update_player_country = """ UPDATE Player
                            SET country=?
                            WHERE nickname=? """

update_player_official_roster = """ UPDATE Player
                                    SET official_roster=?
                                    WHERE nickname=? """

update_player_extra =           """ UPDATE Player
                                    SET extra=?
                                    WHERE nickname=? """
                            

get_player_id =         """ SELECT id
                            FROM Player
                            WHERE nickname=? """

get_player_id_by_account_id = """ SELECT id
                            FROM Player
                            WHERE account_id=? """

get_players_by_official_roster = """ SELECT nickname, country, extra
                                     FROM Player
                                     WHERE official_roster=?
                                     ORDER BY (Player.id)
                                 """

add_tournament =        """ INSERT INTO Tournament(name)
                            VALUES(?) """

remove_tournament =     """ DELETE FROM Tournament
                            WHERE name=? """

list_tournaments =      """ SELECT name, auto_update
                            FROM Tournament 
                            ORDER BY (name) """

auto_update_tournament = """ UPDATE Tournament
                             SET auto_update=?
                             WHERE name=? """

get_tournament_id =     """ SELECT id
                            FROM Tournament
                            WHERE name=? """


add_map =               """ INSERT INTO Map(name, uid)
                            VALUES(?,?) """

remove_map =            """ DELETE FROM Map
                            WHERE name=? """

get_map_id =            """ SELECT id
                            FROM Map
                            WHERE name=? """

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
                            WHERE Map.name=?
                            ORDER BY CAST (Time.time AS DECIMAL) ASC
                            LIMIT ?
                        """


add_to_mappack =        """ INSERT INTO Mappack(tournament_id, map_id)
                            VALUES(?,?) """

#only map_id needed
remove_from_mappack =   """ DELETE FROM Mappack
                            WHERE map_id=? """

get_maps =              """ SELECT Map.name, Tournament.name
                            FROM Mappack
                            JOIN Map ON Mappack.map_id = Map.id
                            JOIN Tournament ON Mappack.tournament_id = Tournament.id
                            ORDER BY Tournament.name, Map.name
                        """

get_tournament_maps =   """ SELECT Map.name, Map.uid
                            FROM Mappack
                            JOIN Map ON Mappack.map_id = Map.id
                            JOIN Tournament ON Mappack.tournament_id = Tournament.id
                            WHERE Tournament.id=?
                            ORDER BY Map.name
                        """

add_to_teaminfo =       """ INSERT INTO TeamInfo(name, info)
                            VALUES(?,?) 
                                ON CONFLICT (name) DO
                                UPDATE SET info=excluded.info """

remove_teaminfo =       """ DELETE FROM TeamInfo
                            WHERE name=? """

get_teaminfo =          """ SELECT info
                            FROM TeamInfo
                            WHERE name=? """

get_teaminfo_list =     """ SELECT name, info
                            FROM TeamInfo
                        """

add_twitch_channel =    """ INSERT INTO TwitchChannel(name)
                            VALUES(?)
                        """

remove_twitch_channel = """ DELETE FROM TwitchChannel
                            WHERE name=? """

get_twitch_list =       """ SELECT name
                            FROM TwitchChannel
                        """


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




