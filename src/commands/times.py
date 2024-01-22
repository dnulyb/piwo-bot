from interactions import (
    Extension,
    slash_command, 
    slash_option, 
    SlashContext,
    OptionType
)
import src.db.db as db
from src.ubi.authentication import(
    check_token_refresh,
    get_nadeo_access_token
)
from src.ubi.records import(
    get_map_records
)

class Times(Extension):

    @slash_command(
        name="update",
        description="Updates tournament times."
    )
    @slash_option(
        name="tournament",
        description="Name of the tournament you want to see maps for",
        required=True,
        opt_type = OptionType.STRING
    )
    async def update(self, ctx: SlashContext, tournament: str = None):

        await ctx.defer()

        if(tournament == None):
            await ctx.send("Error updating: no tournament provided")
            return

        conn = db.open_conn()

        try:

            # load everything that should be updated from db:
            # Get tournament map ids
            tournament_id = db.retrieve_data(conn, (db.get_tournament_id, [tournament]))

            if(len(tournament_id) == 0):
                await ctx.send(f"Error occurred while running command: Tournament '{tournament}' not found")
                conn.close()
                return
                
            tournament_id = tournament_id[0][0]
            maps = db.retrieve_data(conn, (db.get_tournament_maps, [tournament_id]))
            if(len(maps) == 0):
                await ctx.send(f"Error occurred while running command: No maps found for tournament '{tournament}'")
                conn.close()
                return

            map_names = []
            map_ids = []
            for (map_name, map_id) in maps:
                map_names.append(map_name)
                map_ids.append(map_id)

            # Get tournament player ids 
            players = db.retrieve_data(conn, (db.get_tournament_roster_players, [tournament_id]))
            if(len(players) == 0):
                await ctx.send(f"Error occurred while running command: No players found for tournament '{tournament}'")
                conn.close()
                return

            print("Players: ", players)

            player_names = []
            player_ids = []
            player_roster = []
            for (name, id, roster) in players:
                player_names.append(name)
                player_ids.append(id)
                player_roster.append(roster)

                    
            # get data from nadeo and format it nicely
            print("Retrieving nadeo data for tournament: " + tournament)

            # Make sure we have a valid nadeo access token
            # TODO: Move this check into a separate function that's on a timer,
            #           so we never have an invalid token
            check_token_refresh()

            token = get_nadeo_access_token()
            res = get_map_records(player_ids, map_ids, token)
            #print(res)
                
            # update db 
            queries = []
            for [time, player_ubi_id, map_ubi_id] in res:

                player_id = db.retrieve_data(conn, (db.get_player_id_by_account_id, [player_ubi_id]))

                if(len(player_id) == 0):
                    await ctx.send(f"Error occurred while running command: Player '{player_ubi_id}' not found")
                    conn.close()
                    return
                    
                player_id = player_id[0][0]

                map_id = db.retrieve_data(conn, (db.get_map_db_id_by_map_id, [map_ubi_id]))

                if(len(map_id) == 0):
                    await ctx.send(f"Error occurred while running command: Map '{map_ubi_id}' not found")
                    conn.close()
                    return
                    
                map_id = map_id[0][0]

                queries.append((db.add_time, (player_id, map_id, time)))

            db.execute_queries(conn, queries)

            print("Nadeo data for tournament: " + tournament + ", added to database.")

            await ctx.send(f"Updated times for tournament: " + tournament)

        except Exception as e:
            await ctx.send(f"Error occurred while running command: {e}")
        finally:
            conn.close()


    @slash_command(
        name="top_x",
        description="Retrieves the top X times for a map."
    )
    @slash_option(
        name="map_name",
        description="Name of the map you want retrieve times maps for",
        required=True,
        opt_type = OptionType.STRING
    )
    @slash_option(
        name="x",
        description="How many times you want to retrieve.",
        required=True,
        opt_type = OptionType.INTEGER   
    )
    async def top_x(self, ctx: SlashContext, map_name: str, x: int):

        conn = db.open_conn()

        try:
            res = db.retrieve_data(conn, (db.get_n_map_times, (map_name, x)))
            await ctx.send(f"{res}")
        except Exception as e:
            await ctx.send(f"Error occurred while running command: {e}")
        finally:
            conn.close()

    @slash_command(
        name="top5",
        description="Retrieves the top 5 times for a map."
    )
    @slash_option(
        name="map_name",
        description="Name of the map you want retrieve times maps for",
        required=True,
        opt_type = OptionType.STRING
    )
    async def top5(self, ctx: SlashContext, map_name: str):

        conn = db.open_conn()

        try:
            res = db.retrieve_data(conn, (db.get_n_map_times, (map_name, 5)))
            await ctx.send(f"{res}")
        except Exception as e:
            await ctx.send(f"Error occurred while running command: {e}")
        finally:
            conn.close()

    @slash_command(
        name="top10",
        description="Retrieves the top 10 times for a map."
    )
    @slash_option(
        name="map_name",
        description="Name of the map you want retrieve times maps for",
        required=True,
        opt_type = OptionType.STRING
    )
    async def top10(self, ctx: SlashContext, map_name: str):

        conn = db.open_conn()

        try:
            res = db.retrieve_data(conn, (db.get_n_map_times, (map_name, 10)))
            await ctx.send(f"{res}")
        except Exception as e:
            await ctx.send(f"Error occurred while running command: {e}")
        finally:
            conn.close()


    @slash_command(
        name="leaderboard",
        description="Retrieves all times for a map. A maximum of 50 times will be retrieved."
    )
    @slash_option(
        name="map_name",
        description="Name of the map you want retrieve times maps for",
        required=True,
        opt_type = OptionType.STRING
    )
    async def leaderboard(self, ctx: SlashContext, map_name: str):

        conn = db.open_conn()

        try:
            res = db.retrieve_data(conn, (db.get_n_map_times, (map_name, 50)))
            await ctx.send(f"{res}")
        except Exception as e:
            await ctx.send(f"Error occurred while running command: {e}")
        finally:
            conn.close()
