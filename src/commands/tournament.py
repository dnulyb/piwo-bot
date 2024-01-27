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


class Tournament(Extension):

    @slash_command(
        name="tournament",
        sub_cmd_name="manage",
        sub_cmd_description="Tournament management"
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
            await ctx.send(f"Error occurred while running command: {e}")

        finally:
            conn.close() 

    @slash_command(
        name="list",
        sub_cmd_name="tournaments",
        sub_cmd_description="Lists all tournaments."
    )
    async def list(self, ctx: SlashContext):
        conn = db.open_conn()
        try:
            query = (db.list_tournaments, None)
            res = db.retrieve_data(conn, query)
            embed = format_tournament_list(res)
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"Error occurred while running command: {e}")
        finally:
            conn.close() 

# Returns None if the tournament cannot be found
def get_tournament_id(conn, tournament):

    tournament_id = db.retrieve_data(conn, (db.get_tournament_id, [tournament]))
    if(len(tournament_id) == 0):
        return None
    
    return tournament_id[0][0]

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

    


