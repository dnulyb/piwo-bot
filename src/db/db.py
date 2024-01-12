import sqlite3
import os.path

db_file = os.path.join(os.path.dirname(__file__), "team.sqlite")
db_init_sql = os.path.join(os.path.dirname(__file__), "team.sql")

add_roster =        """ INSERT INTO Roster(name)
                        VALUES(?) """

remove_roster =     """ DELETE FROM Roster
                        WHERE name=? """

add_player =        """ INSERT INTO Player(nickname, account_id, roster)
                        VALUES(?,?,?) """

remove_player =     """ DELETE FROM Player
                        WHERE nickname=? """

add_tournament =    """ INSERT INTO Tournament(name)
                        VALUES(?) """

remove_tournament = """ DELETE FROM Tournament
                        WHERE name=? """

def open_conn():
    conn = sqlite3.connect(db_file)
    conn.execute("PRAGMA foreign_keys = 1")
    return conn

# Creates the initial database structure
def init():

    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    init_query = open(db_init_sql, "r").read()
    cursor.executescript(init_query)

    cursor.close()
    conn.close()

def execute_queries(conn, queries):

    cursor = conn.cursor()

    for [sql, param] in queries:
            
        try:
            cursor.execute(sql, param)
        except sqlite3.Error as e:
            print(e, end="")
            print(" : ", end="")
            print(param)

    conn.commit()
    cursor.close()


"""def add_player(nickname, account_id, roster=None):

    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    sql = "INSERT INTO Player (nickname, account_id, roster)"

    cursor.close()
    conn.close()"""


