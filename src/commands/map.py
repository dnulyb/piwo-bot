from interactions import (
    Extension,
    slash_command, 
    slash_option, 
    SlashContext,
    OptionType
)
import src.db.db as db

class Map(Extension):

    @slash_command(
        name="map_add",
        description="Adds a map to a tournament."
    )
    @slash_option(
        name="tournament",
        description="Name of the tournament you want to add maps to",
        required=True,
        opt_type = OptionType.STRING
    )
    @slash_option(
        name="map_name",
        description="name of the map you want to add.",
        required=True,
        opt_type = OptionType.STRING
    )
    @slash_option(
        name="map_id",
        description="id of the map you want to add.",
        required=True,
        opt_type = OptionType.STRING
    )
    async def map_add(self, ctx: SlashContext, tournament: str, map_name: str, map_id: str):

        conn = db.open_conn()

        try:
            # Get tournament id
            tournament_id = db.retrieve_data(conn, (db.get_tournament_id, [tournament]))

            if(len(tournament_id) == 0):
                await ctx.send(f"Error occurred while running command: Tournament '{tournament}' not found")
                conn.close()
                return

            tournament_id = tournament_id[0][0]

            # Add the map to "Map" table
            #TODO: Change "uid" to "id" or something more fitting, in Map table
            db.execute_queries(conn, [(db.add_map, (map_name, map_id))])


            # Add the tournament and map to "Mappack" table
            map_database_id = db.retrieve_data(conn, (db.get_map_id, [map_name]))
            if(len(map_database_id) == 0):
                await ctx.send(f"Error occurred while running command: Map '{map}' not found")
                conn.close()
                return
            map_database_id = map_database_id[0][0]
        
            db.execute_queries(conn, [(db.add_to_mappack, (tournament_id, map_database_id))])

            await ctx.send("Added map to tournament '" + tournament + "': " + map_name)

        except Exception as e:
            await ctx.send(f"Error occurred while running command: {e}")
        finally:
            conn.close() 

    @slash_command(
        name="map_delete",
        description="Delete a map."
    )
    @slash_option(
        name="map_name",
        description="Name of the map you want to delete",
        required=True,
        opt_type = OptionType.STRING
    )
    async def map_delete(self, ctx: SlashContext, map_name: str):

        conn = db.open_conn()
        try:

            map_database_id = db.retrieve_data(conn, (db.get_map_id, [map_name]))
            if(len(map_database_id) == 0):
                await ctx.send(f"Error occurred while running command: Map '{map_name}' not found")
                conn.close()
                return
            map_database_id = map_database_id[0][0]

            #Delete from Mappack
            query = [(db.remove_from_mappack, [map_database_id])]
            db.execute_queries(conn, query)

            #Delete from Map
            query = [(db.remove_map, [map_name])]
            db.execute_queries(conn, query)
            await ctx.send("Deleted map: " + map_name)
        except Exception as e:
            await ctx.send(f"Error occurred while running command: {e}")
        finally:
            conn.close() 

    @slash_command(
        name="map_list",
        description="Lists all maps."
    )
    @slash_option(
        name="tournament",
        description="Name of the tournament you want to see maps for",
        required=False,
        opt_type = OptionType.STRING
    )
    async def map_list(self, ctx: SlashContext, tournament: str = None):
        
        conn = db.open_conn()
        try:
            if(tournament == None):
                query = (db.get_maps, None)
            else:
                tournament_id = db.retrieve_data(conn, (db.get_tournament_id, [tournament]))
                if(len(tournament_id) == 0):
                    print(f"Error occurred while running command: Tournament '{tournament}' not found")
                    conn.close()
                    quit()

                tournament_id = tournament_id[0][0]
                query = (db.get_tournament_maps, [tournament_id])

            res = db.retrieve_data(conn, query)
            await ctx.send(f"{res}")
        except Exception as e:
            await ctx.send(f"Error occurred while running command: {e}")
        finally:
            conn.close() 



    

