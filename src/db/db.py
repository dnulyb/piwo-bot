import sqlite3
import os.path

db_file = os.path.join(os.path.dirname(__file__), "team.sqlite")
db_init_sql = os.path.join(os.path.dirname(__file__), "team.sql")

add_roster =            """ INSERT INTO Roster(name, tournament)
                            VALUES(?,?) """

remove_roster =         """ DELETE FROM Roster
                            WHERE name=? """

list_rosters =          """ SELECT name, tournament
                            FROM Roster 
                            ORDER BY tournament, name """

add_player =            """ INSERT INTO Player(nickname, account_id)
                            VALUES(?,?) """

remove_player =         """ DELETE FROM Player
                            WHERE nickname=? """

list_players =          """ SELECT nickname
                            FROM Player 
                            ORDER BY (nickname) """

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


add_map =               """ INSERT INTO Map(name, uid)
                            VALUES(?,?) """

remove_map =            """ DELETE FROM Map(name)
                            WHERE name=? """

add_participant =       """ INSERT INTO Participant(player_id, tournament_id)
                            VALUES(?,?) """

remove_participant =    """ DELETE FROM Participant
                            WHERE player_id=? AND tournament_id=? """

add_time =              """ INSERT INTO Time(player_id, map_id, time)
                            VALUES(?,?,?) 
                                ON CONFLICT (player_id, map_id) DO
                                UPDATE SET time=excluded.time"""

tournament_mappack_add =    """ INSERT INTO Mappack(tournament_id, map_id)
                            VALUES(?,?) """

tournament_mappack_remove = """ DELETE FROM Mappack
                                WHERE tournament_id=? AND map_id=? """


def open_conn():
    conn = sqlite3.connect(db_file)
    conn.execute("PRAGMA foreign_keys = 1")
    return conn

# Creates the initial database structure
def init():

    try:
        f = open(db_file, "x")
    except FileExistsError:
        print("db file already exists, no new file created")

    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    init_query = open(db_init_sql, "r").read()
    cursor.executescript(init_query)

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




