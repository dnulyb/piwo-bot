from interactions import (
    Extension,
    slash_command, 
    slash_option, 
    SlashContext,
    SlashCommandChoice,
    OptionType,
    Embed
)
import src.db.db as db
from src.db.db import get_tournament_db_id
from dotenv import find_dotenv, load_dotenv, get_key
from src.gsheet import google_sheet_write, google_sheet_write_batch
from src.ubi.authentication import get_nadeo_access_token
from src.commands.map import get_map_records, format_map_record
from src.other.map_analysis import get_map_infos, get_map_leaderboard_info

from datetime import datetime
import time


class Tournament(Extension):

    @slash_command(
        name="tournament",
        description="Tournament management commands.",
        sub_cmd_name="manage",
        sub_cmd_description="Tournament management",
        dm_permission=False
    )
    @slash_option(
        name="action",
        description="Tournament management action",
        required=True,
        opt_type = OptionType.STRING,
        choices=[
            SlashCommandChoice(name="create", value="create"),
            SlashCommandChoice(name="delete", value="delete"),
            SlashCommandChoice(name="auto update ON", value="autoon"),
            SlashCommandChoice(name="auto update OFF", value="autooff")
        ]
    )
    @slash_option(
        name="name",
        description="Name of the tournament you want to manage",
        required=True,
        opt_type = OptionType.STRING
    )
    async def tournament(self, ctx: SlashContext, action: str, name: str = ""):

        conn = db.open_conn()

        try:
            match action:
                case "create":
                    query = [(db.add_tournament, [name])]
                    res = "Created tournament: " + name
                    db.execute_queries(conn, query)
                case "delete":
                    query = [(db.remove_tournament, [name])]
                    res = "Deleted tournament: " + name
                    db.execute_queries(conn, query)
                case "autoon":
                    query = [(db.auto_update_tournament, (1, name))]
                    res = "Turned ON auto update for tournament: " + name
                    db.execute_queries(conn, query)
                case "autooff":
                    query = [(db.auto_update_tournament, (0, name))]
                    res = "Turned OFF auto update for tournament: " + name
                    db.execute_queries(conn, query)
                case _:
                    res = "invalid tournament action"

            # always send reply
            await ctx.send(f"{res}")

        except Exception as e:
            await ctx.send(f"Error occurred while running command: {e}", ephemeral=True)

        finally:
            conn.close() 

    @slash_command(
        name="list",
        sub_cmd_name="tournaments",
        sub_cmd_description="Lists all tournaments.",
        dm_permission=False
    )
    async def list(self, ctx: SlashContext):
        conn = db.open_conn()
        try:
            query = (db.list_tournaments, None)
            res = db.retrieve_data(conn, query)
            embed = format_tournament_list(res)
            await ctx.send(embed=embed, ephemeral=True)
        except Exception as e:
            await ctx.send(f"Error occurred while running command: {e}", ephemeral=True)
        finally:
            conn.close() 

    @slash_command(
        name="tournament",
        sub_cmd_name="gsheet_add",
        sub_cmd_description="Register a google sheet to a tournament.",
        dm_permission=False
    )
    @slash_option(
        name="tournament",
        description="Name of the tournament",
        required=True,
        opt_type = OptionType.STRING
    )
    @slash_option(
        name="sheet_name",
        description="Name of the sheet",
        required=True,
        opt_type = OptionType.STRING
    )
    @slash_option(
        name="sheet_number",
        description="Number of the sheet to send data to. 0 = first sheet, 1 = second, and so on.",
        required=True,
        opt_type = OptionType.INTEGER
    )
    async def gsheet_add(self, ctx: SlashContext, tournament: str, sheet_name: str, sheet_number: int):

        conn = db.open_conn()

        try:

            tournament_id = get_tournament_db_id(conn, tournament)
            if(tournament_id == None):
                await ctx.send(f"Error occurred while running command: Tournament not found", ephemeral=True)
                return

            query = [(db.add_gsheet, (sheet_name, sheet_number, tournament_id))]
            db.execute_queries(conn, query)
            res = "Added google sheet: " + sheet_name + ", with data sheet number: " + str(sheet_number) + ", to tournament: " + tournament

            # always send reply
            await ctx.send(f"{res}")

        except Exception as e:
            await ctx.send(f"Error occurred while running command: {e}", ephemeral=True)

        finally:
            conn.close() 

    @slash_command(
        name="tournament",
        sub_cmd_name="gsheet_update",
        sub_cmd_description="Update the google sheet for a tournament. Also updates the tournament map times.",
        dm_permission=False
    )
    @slash_option(
        name="tournament",
        description="Name of the tournament",
        required=True,
        opt_type = OptionType.STRING
    )
    async def gsheet_update(self, ctx: SlashContext, tournament: str):

        await ctx.defer()

        update_tournament_times(tournament)

        (res, ephemeral) = update_sheet(tournament)
        await ctx.send(f"{res}", ephemeral=ephemeral)


def update_tournament_times(tournament):

    conn = db.open_conn()

    # Update tournament times
    # load everything that should be updated from db:
    # Get tournament map ids
    tournament_id = get_tournament_db_id(conn, tournament)

    if tournament_id == None:
        conn.close()
        msg = f"Error occurred while running command: Tournament '{tournament}' not found"
        ephemeral = True
        return (msg, ephemeral)
    
    maps = db.retrieve_data(conn, (db.get_tournament_maps, [tournament_id]))
    if(len(maps) == 0):
        conn.close()
        msg = f"Error occurred while running command: No maps found for tournament '{tournament}'"
        ephemeral = True
        return (msg, ephemeral)

    map_names = []
    map_ids = []
    for (map_name, map_id) in maps:
        map_names.append(map_name)
        map_ids.append(map_id)

    # Get tournament player ids 
    players = db.retrieve_data(conn, (db.get_tournament_roster_players, [tournament_id]))
    if(len(players) == 0):
        conn.close()
        msg = f"Error occurred while running command: No players found for tournament '{tournament}'"
        ephemeral = True
        return (msg, ephemeral)

    #print("Players: ", players)

    player_names = []
    player_ids = []
    player_roster = []
    for (name, id, roster) in players:
        player_names.append(name)
        player_ids.append(id)
        player_roster.append(roster)

            
    # get data from nadeo and format it nicely
    print("Retrieving nadeo data for tournament: " + tournament)

    token = get_nadeo_access_token()
    res = get_map_records(player_ids, map_ids, token)
    #print(res)
        
    # update db 
    queries = []
    for [time, player_ubi_id, map_ubi_id] in res:

        player_id = db.retrieve_data(conn, (db.get_player_id_by_account_id, [player_ubi_id]))

        if(len(player_id) == 0):
            conn.close()
            msg = f"Error occurred while running command: Player '{player_ubi_id}' not found"
            ephemeral = True
            return (msg, ephemeral)
            
        player_id = player_id[0][0]

        map_id = db.retrieve_data(conn, (db.get_map_db_id_by_map_id, [map_ubi_id]))

        if(len(map_id) == 0):
            conn.close()
            msg = f"Error occurred while running command: Map '{map_ubi_id}' not found"
            ephemeral = True
            return (msg, ephemeral)
            
        map_id = map_id[0][0]

        queries.append((db.add_time, (player_id, map_id, time)))

    db.execute_queries(conn, queries)

    print("Nadeo data for tournament: " + tournament + ", added to database.")


# Returns (msg, epemeral)
#   msg:        message to send to discord
#   ephemeral:  if the message should be ephemeral (aka visible to only the person who used the command)
def update_sheet(tournament):

    conn = db.open_conn()

    try:

        tournament_id = get_tournament_db_id(conn, tournament)

        if tournament_id == None:
            conn.close()
            msg = f"Error occurred while running command: Tournament '{tournament}' not found"
            ephemeral = True
            return (msg, ephemeral)

        
        # Get sheet info
        sheet_info = db.retrieve_data(conn, (db.get_gsheet, [tournament_id]))
        if(sheet_info == []):
            msg = f"Error occurred while running command: Tournament sheet not found"
            ephemeral = True
            return (msg, ephemeral)
        
        (sheet_name, sheet_number) = sheet_info[0]

        # Collect all player map times
        rosters_list = db.retrieve_data(conn, (db.get_tournament_rosters, [tournament_id]))
        maps_list = db.retrieve_data(conn, (db.get_tournament_maps, [tournament_id]))

        maps = []
        map_names = []
        map_ids = []
        for (map_name, map_uid) in maps_list:
            map_id = db.retrieve_data(conn, (db.get_map_id, [map_name]))
            maps.append(map_id[0][0])
            map_names.append(map_name)
            map_ids.append(map_uid)

        map_infos = get_map_infos(map_ids)
        sorted_map_info = []
        for map_id in map_ids:
            for map_info in map_infos:
                if(map_id == map_info[1]):
                    sorted_map_info.append(map_info)

        map_wrs = []
        map_wrs.append("WR")
        for (_, _, map_uid) in sorted_map_info:

            (wr, _, _, _) = get_map_leaderboard_info(map_uid)
            if wr is None:
                map_wrs.append((""))
            else:
                wr = format_map_record(wr, False)
                map_wrs.append((wr))

            time.sleep(0.5)

        rosters = []
        players = []
        for roster in rosters_list:
            rosters.append(roster[0])

            roster_players = db.retrieve_data(conn, (db.get_specific_roster_players, [roster[0]]))
            for player in roster_players:
                players.append(player[0])

        all_players = []
        for player in players:

            player_id = db.retrieve_data(conn, (db.get_player_id, [player]))
            player_id = player_id[0][0]


            player_times = []
            for map in maps:
                player_time = db.retrieve_data(conn, (db.get_player_time, (map, player_id)))
                if(player_time == []):
                    player_time = "999.999"
                else:
                    player_time = player_time[0][0]
                    player_time = format_map_record(player_time, False)

                player_times.append(player_time)

            all_players.append((player, player_times))

        #sorted_players = sorted(all_players, key=lambda x:(str.casefold(x[0])))
        sorted_players = all_players

        #Write row of player times to gsheet
        dotenv_path = find_dotenv()
        load_dotenv(dotenv_path)

        credentials = get_key(dotenv_path, "CREDENTIALS_FILE")
        start_col = "A"
        start_row = 3

        ranges = []
        all_players = []
        for (player_name, player_times) in sorted_players:

            range = start_col + str(start_row) + ":Z" + str(start_row)
            ranges.append(range)
            all_players.append([[player_name] + player_times])
            start_row += 1

        #Write update time
        now = datetime.now()
        dmY_HMS = now.strftime("%d/%m/%Y %H:%M:%S")
        google_sheet_write("A1", ["Latest update (UTC): " + dmY_HMS], True, sheet_name, sheet_number, credentials)

        #Write map names
        google_sheet_write("B1:Z1", map_names, True, sheet_name, sheet_number, credentials)

        #Write map wrs
        google_sheet_write("A2:Z2", map_wrs, True, sheet_name, sheet_number, credentials)

        #Write data
        google_sheet_write_batch(ranges, all_players, True, sheet_name, sheet_number, credentials)

        # always send reply
        conn.close()
        msg = "Updated google sheet: " + sheet_name + ", with data sheet number: " + str(sheet_number) + ", for tournament: " + tournament
        ephemeral = False
        return (msg, ephemeral)

    except Exception as e:
        conn.close()
        msg = f"Error occurred while running command: {e}"
        ephemeral = True
        return (msg, ephemeral)

def format_tournament_list(tournaments):

    embed = Embed()
    embed.title = "Tournaments:"

    names = ""
    autoupdates = ""
    for (name, autoupdate) in tournaments:

        names += name + "\n"
        if autoupdate == 1:
            autoupdates += "ON" + "\n"
        else:
            autoupdates += "OFF" + "\n"

    embed.add_field(name="Tournament", value=names, inline=True)
    embed.add_field(name="Auto update", value=autoupdates, inline=True)


    return embed

    


