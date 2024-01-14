BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS "Roster" (
	"id"	INTEGER,
	"name"	TEXT NOT NULL UNIQUE,
	PRIMARY KEY("id" AUTOINCREMENT)
);
CREATE TABLE IF NOT EXISTS "Player" (
	"id"	INTEGER,
	"nickname"	TEXT NOT NULL UNIQUE,
	"account_id"	TEXT NOT NULL UNIQUE,
	"roster"	TEXT,
	FOREIGN KEY("roster") REFERENCES "Roster"("name"),
	PRIMARY KEY("id" AUTOINCREMENT)
);
CREATE TABLE IF NOT EXISTS "Participant" (
	"id"	INTEGER,
	"player_id"	INTEGER NOT NULL,
	"tournament_id"	INTEGER NOT NULL,
	UNIQUE("player_id","tournament_id"),
	FOREIGN KEY("tournament_id") REFERENCES "Tournament"("id"),
	FOREIGN KEY("player_id") REFERENCES "Player"("id"),
	PRIMARY KEY("id" AUTOINCREMENT)
);
CREATE TABLE IF NOT EXISTS "Map" (
	"id"	INTEGER,
	"name"	TEXT NOT NULL UNIQUE,
	"uid"	TEXT NOT NULL UNIQUE,
	PRIMARY KEY("id" AUTOINCREMENT)
);
CREATE TABLE IF NOT EXISTS "Mappack" (
	"id"	INTEGER,
	"tournament_id"	INTEGER,
	"map_id"	INTEGER,
	UNIQUE("tournament_id","map_id"),
	FOREIGN KEY("tournament_id") REFERENCES "Tournament"("id"),
	FOREIGN KEY("map_id") REFERENCES "Map"("id"),
	PRIMARY KEY("id" AUTOINCREMENT)
);
CREATE TABLE IF NOT EXISTS "Time" (
	"id"	INTEGER,
	"player_id"	INTEGER NOT NULL,
	"map_id"	INTEGER NOT NULL,
	"time"	TEXT NOT NULL,
	UNIQUE("player_id","map_id"),
	FOREIGN KEY("map_id") REFERENCES "Map"("id"),
	FOREIGN KEY("player_id") REFERENCES "Player"("id"),
	PRIMARY KEY("id" AUTOINCREMENT)
);
CREATE TABLE IF NOT EXISTS "Tournament" (
	"id"	INTEGER,
	"name"	TEXT NOT NULL UNIQUE,
	"auto_update"	INTEGER,
	PRIMARY KEY("id" AUTOINCREMENT)
);
COMMIT;
