import sqlite3
import os.path

db_file = os.path.join(os.path.dirname(__file__), "team.sqlite")
db_init_sql = os.path.join(os.path.dirname(__file__), "team.sql")

def init():

    print(db_file + "\n" + db_init_sql)

    init_query = open(db_init_sql, "r").read()

    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.executescript(init_query)