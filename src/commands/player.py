from interactions import (
    Extension,
    slash_command, 
    slash_option, 
    SlashContext,
    OptionType
)
import src.db.db as db

class Player(Extension):

    @slash_command(
    name="player_add",
    description="Add a player to the database."
    )
    @slash_option(
        name="nickname",
        description="Nickname of the player you want to add.",
        required=True,
        opt_type = OptionType.STRING
    )
    @slash_option(
        name="account_id",
        description="Account id of the player you want to add.",
        required=True,
        opt_type = OptionType.STRING
    )
    async def player_add(self, ctx: SlashContext, nickname: str, account_id: str):

        conn = db.open_conn()

        try:

            query = [(db.add_player, (nickname, account_id))]
            db.execute_queries(conn, query)
            res = "Added player: " + nickname

            # always send reply
            await ctx.send(f"{res}")

        except Exception as e:
            await ctx.send(f"Error occurred while running command: {e}")

        finally:
            conn.close() 

    @slash_command(
        name="player_remove",
        description="Remove a player from the database."
    )
    @slash_option(
        name="nickname",
        description="Nickname of the player you want to remove.",
        required=True,
        opt_type = OptionType.STRING
    )

    async def player_remove(self, ctx: SlashContext, nickname: str):

        conn = db.open_conn()

        try:

            query = [(db.remove_player, [nickname])]
            db.execute_queries(conn, query)
            res = "Removed player: " + nickname

            # always send reply
            await ctx.send(f"{res}")

        except Exception as e:
            await ctx.send(f"Error occurred while running command: {e}")

        finally:
            conn.close() 

    @slash_command(
        name="player_list",
        description="Lists all players in the database."
    )
    async def player_list(self, ctx: SlashContext):

        conn = db.open_conn()

        try:

            query = [db.list_players, None]
            res = db.retrieve_data(conn, query)

            # always send reply
            await ctx.send(f"{res}")

        except Exception as e:
            await ctx.send(f"Error occurred while running command: {e}")

        finally:
            conn.close() 
