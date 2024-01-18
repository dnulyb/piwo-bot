from interactions import (
    Extension,
    slash_command, 
    slash_option, 
    SlashContext,
    OptionType
)
import src.db.db as db

class Roster(Extension):

    @slash_command(
    name="roster_create",
    description="Create a roster."
    )
    @slash_option(
        name="name",
        description="Name of the roster you want to create",
        required=True,
        opt_type = OptionType.STRING
    )
    @slash_option(
        name="tournament",
        description="Tournament the roster belongs to",
        required=True,
        opt_type = OptionType.STRING
    )
    async def roster_create(self, ctx: SlashContext, name: str, tournament: str):

        conn = db.open_conn()
        try:
            query = [(db.add_roster, (name, tournament))]
            db.execute_queries(conn, query)
            ctx.send("Created roster: " + name + ", for tournament: " + tournament)

        except Exception as e:
            await ctx.send(f"Error occurred while running command: {e}")
        finally:
            conn.close() 

    @slash_command(
        name="roster_delete",
        description="Delete a roster."
    )
    @slash_option(
        name="name",
        description="Name of the roster you want to delete",
        required=True,
        opt_type = OptionType.STRING
    )
    async def roster_delete(self, ctx: SlashContext, name: str):

        conn = db.open_conn()
        try:
            query = [(db.remove_roster, [name])]
            db.execute_queries(conn, query)
            ctx.send("Deleted roster: " + name)
        except Exception as e:
            await ctx.send(f"Error occurred while running command: {e}")
        finally:
            conn.close() 

    @slash_command(
        name="roster_list",
        description="Lists all rosters."
    )
    async def roster_list(self, ctx: SlashContext):
        conn = db.open_conn()
        try:
            query = (db.list_rosters, None)
            res = db.retrieve_data(conn, query)
            await ctx.send(f"{res}")
        except Exception as e:
            await ctx.send(f"Error occurred while running command: {e}")
        finally:
            conn.close() 