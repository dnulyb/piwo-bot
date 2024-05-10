from interactions import (
    Extension,
    slash_command, 
    slash_option, 
    SlashContext,
    OptionType,
    Embed
)
import src.db.db as db
from src.db.db import get_tournament_db_id

class Roster(Extension):

    @slash_command(
        name="roster",
        description="Roster management commands.",
        sub_cmd_name="create",
        sub_cmd_description="Create a roster.",
        dm_permission=False
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
    async def create(self, ctx: SlashContext, name: str, tournament: str):

        conn = db.open_conn()
        try:

            tournament_id = get_tournament_db_id(conn, tournament)

            if tournament_id == None:
                await ctx.send(f"Error occurred while running command: Tournament '{tournament}' not found", ephemeral=True)
                conn.close()
                return

            query = [(db.add_roster, (name, tournament_id))]
            db.execute_queries(conn, query)
            await ctx.send("Created roster: " + name + ", for tournament: " + tournament)

        except Exception as e:
            await ctx.send(f"Error occurred while running command: {e}", ephemeral=True)
        finally:
            conn.close() 

    @slash_command(
        name="roster",
        sub_cmd_name="delete",
        sub_cmd_description="Delete a roster.",
        dm_permission=False
    )
    @slash_option(
        name="name",
        description="Name of the roster you want to delete",
        required=True,
        opt_type = OptionType.STRING
    )
    async def delete(self, ctx: SlashContext, name: str):

        conn = db.open_conn()
        try:
            query = [(db.remove_roster, [name])]
            db.execute_queries(conn, query)
            await ctx.send("Deleted roster: " + name)
        except Exception as e:
            await ctx.send(f"Error occurred while running command: {e}", ephemeral=True)
        finally:
            conn.close() 

    @slash_command(
        name="list",
        sub_cmd_name="rosters",
        sub_cmd_description="Lists all rosters.",
        dm_permission=False
    )
    async def list(self, ctx: SlashContext):
        conn = db.open_conn()
        try:
            query = (db.list_rosters, None)
            res = db.retrieve_data(conn, query)
            embed = format_roster_list(res)
            await ctx.send(embed=embed, ephemeral=True)
        except Exception as e:
            await ctx.send(f"Error occurred while running command: {e}", ephemeral=True)
        finally:
            conn.close() 

    @slash_command(
        name="roster",
        sub_cmd_name="add",
        sub_cmd_description="Adds players to a roster. Separate player names by commas, example: 'p1,p2,p3'.",
        dm_permission=False
    )
    @slash_option(
        name="roster",
        description="Name of the roster you want to add players to",
        required=True,
        opt_type = OptionType.STRING
    )
    @slash_option(
        name="names",
        description="Comma separated list of players you want to add to the roster.",
        required=True,
        opt_type = OptionType.STRING
    )
    async def add(self, ctx: SlashContext, roster: str, names: str):
        
        conn = db.open_conn()

        try:
            # Get roster id
            roster_id = db.retrieve_data(conn, (db.get_roster_id, [roster]))

            if(len(roster_id) == 0):
                await ctx.send(f"Error occurred while running command: Roster '{roster}' not found", ephemeral=True)
                conn.close()
                return

            roster_id = roster_id[0][0]

            # Get player ids and build queries
            player_names = names.split(',')
            queries = []
            for player in player_names:

                player_id = db.retrieve_data(conn, (db.get_player_id, [player]))
                if(len(player_id) == 0):
                    await ctx.send(f"Error occurred while running command: Player '{player}' not found", ephemeral=True)
                    conn.close()
                    return
                
                player_id = player_id[0][0]
                
                queries.append((db.add_participant, (player_id, roster_id)))


            db.execute_queries(conn, queries)
            await ctx.send("Added players to roster '" + roster + "': " + names)

        except Exception as e:
            await ctx.send(f"Error occurred while running command: {e}", ephemeral=True)
        finally:
            conn.close() 

    @slash_command(
        name="roster",
        sub_cmd_name="remove_players",
        sub_cmd_description="Removes players from a roster. Separate player names by commas, example: 'p1,p2,p3'.",
        dm_permission=False
    )
    @slash_option(
        name="roster",
        description="Name of the roster you want to remove players from",
        required=True,
        opt_type = OptionType.STRING
    )
    @slash_option(
        name="names",
        description="Comma separated list of players you want to remove from the roster.",
        required=True,
        opt_type = OptionType.STRING
    )
    async def remove_players(self, ctx: SlashContext, roster: str, names: str):
        
        conn = db.open_conn()

        try:
            # Get roster id
            roster_id = db.retrieve_data(conn, (db.get_roster_id, [roster]))

            if(len(roster_id) == 0):
                await ctx.send(f"Error occurred while running command: Roster '{roster}' not found", ephemeral=True)
                conn.close()
                return

            roster_id = roster_id[0][0]

            # Get player ids and build queries
            player_names = names.split(',')
            queries = []
            for player in player_names:

                player_id = db.retrieve_data(conn, (db.get_player_id, [player]))
                if(len(player_id) == 0):
                    await ctx.send(f"Error occurred while running command: Player '{player}' not found", ephemeral=True)
                    conn.close()
                    return
                
                player_id = player_id[0][0]
                
                queries.append((db.remove_participant, (player_id, roster_id)))


            db.execute_queries(conn, queries)
            await ctx.send("Removed players from roster '" + roster + "': " + names)

        except Exception as e:
            await ctx.send(f"Error occurred while running command: {e}", ephemeral=True)
        finally:
            conn.close() 

    # Keep this as its own base command for now
    @slash_command(
        name="registered_players",
        description="Shows all players registered to a roster.",
        dm_permission=False
    )
    @slash_option(
        name="tournament",
        description="Name of the tournament you want to see roster players for",
        required=False,
        opt_type = OptionType.STRING
    )
    async def registered_players(self, ctx: SlashContext, tournament: str = None):

        conn = db.open_conn()
        try:
            if(tournament == None):
                query = (db.get_roster_players, None)
            else:

                tournament_id = get_tournament_db_id(conn, tournament)

                if tournament_id == None:
                    await ctx.send(f"Error occurred while running command: Tournament '{tournament}' not found", ephemeral=True)
                    conn.close()
                    return

                query = (db.get_tournament_roster_players, [tournament_id])

            res = db.retrieve_data(conn, query)
            embed = format_registered_players(res)
            await ctx.send(embed=embed, ephemeral=True)
        except Exception as e:
            await ctx.send(f"Error occurred while running command: {e}", ephemeral=True)
        finally:
            conn.close() 


def format_registered_players(players):

    embed = Embed()
    embed.title = "Registered players"

    res = {}
    for (player, account_id, roster) in players:
        if roster in res:
            res[roster].append((player, account_id))
        else:
            res[roster] = [(player, account_id)]

    for key in res:
        all_players = ""
        all_account_ids = ""
        for (player, account_id) in res[key]:
            all_players += player + "\n"
            all_account_ids += account_id + "\n"

            # Have we almost reached the embed value limit?
            if(len(all_players) >= 900
            or len(all_account_ids) >= 900):
                embed.add_field(name=key, value='\u200b', inline=False)
                embed.add_field(name="Player", value=all_players, inline=True)
                embed.add_field(name="Account id", value=all_account_ids, inline=True)

                all_players = ""
                all_account_ids = ""

        embed.add_field(name=key, value='\u200b', inline=False)
        embed.add_field(name="Player", value=all_players, inline=True)
        embed.add_field(name="Account id", value=all_account_ids, inline=True)


    return embed

def format_roster_list(rosters):

    embed = Embed()
    embed.title = "Rosters for tournaments:"

    res = {}
    for (roster, tournament) in rosters:
        if tournament in res:
            res[tournament].append(roster)
        else:
            res[tournament] = [roster]

    for key in res:
        value = ""
        for val in res[key]:
            value += val + "\n"
        embed.add_field(name=key, value=value, inline=False)

    return embed