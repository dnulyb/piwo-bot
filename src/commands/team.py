from interactions import (
    Extension,
    slash_command, 
    slash_option,
    OptionType,
    SlashContext,
    Embed
)

import src.db.db as db


class Team(Extension):

    @slash_command(
        name="teaminfo_list",
        description="Get all stored team info."
    )
    async def teaminfo_list(self, ctx: SlashContext):

        info_list = get_teaminfo_list()

        await ctx.send(f"{info_list}")

    @slash_command(
        name="teaminfo_update",
        description="Add or update team info."
    )
    @slash_option(
        name="name",
        description="Name of the info item you want to add/update",
        required=True,
        opt_type = OptionType.STRING
    )
    @slash_option(
        name="value",
        description="The info to add/update",
        required=True,
        opt_type = OptionType.STRING
    )
    async def teaminfo_update(self, ctx: SlashContext, name: str, value: str):

        try:

            conn = db.open_conn()
            query = [(db.add_to_teaminfo, (name, value))]
            db.execute_queries(conn, query)

            await ctx.send("Team info added: " + name)

        except Exception as e:
            await ctx.send(f"Error occurred while running command: {e}")
        finally:
            conn.close()

    @slash_command(
        name="teaminfo_remove",
        description="Remove team info."
    )
    @slash_option(
        name="name",
        description="Name of the info item you want to remove",
        required=True,
        opt_type = OptionType.STRING
    )
    async def teaminfo_remove(self, ctx: SlashContext, name: str):

        try:

            conn = db.open_conn()
            query = [(db.remove_teaminfo, [name])]
            db.execute_queries(conn, query)

            await ctx.send("Team info removed: " + name)

        except Exception as e:
            await ctx.send(f"Error occurred while running command: {e}")
        finally:
            conn.close()

    @slash_command(
        name="team_introduction",
        description="Get the full team introduction."
    )
    async def team_introduction(self, ctx: SlashContext):

        embed = format_team_intro_embed()

        await ctx.send(embed=embed)
    
def format_team_intro_embed():

    team_title = get_teaminfo("team_title")
    team_intro = get_teaminfo("team_intro")
    team_color = get_teaminfo("team_color")

    competitive_roster = get_official_roster("competitive")
    tech_roster = get_official_roster("tech")
    ice_roster = get_official_roster("ice")
    casual_roster = get_official_roster("casual")

    competitive_final = ""
    for (player, country, _) in competitive_roster:
        competitive_final += country + " " + player + "\n"

    tech_final = ""
    for (player, country, _) in tech_roster:
        tech_final += country + " " + player + "\n"
    
    ice_final = ""
    for (player, country, _) in ice_roster:
        ice_final += country + " " + player + "\n"

    casual_final = ""
    for (player, country, _) in casual_roster:
        casual_final += country + " " + player + "\n"
    

    embed = Embed()
    embed.color = team_color
    embed.title = team_title
    embed.description = team_intro

    # Competitive roster
    embed.add_field(name="Competitive roster", value=competitive_final, inline=False)

    # Tech roster
    embed.add_field(name="Tech roster", value=tech_final, inline=False)


    # Ice roster
    embed.add_field(name="Ice roster", value=ice_final, inline=False)


    # Casual roster
    embed.add_field(name="Casual roster", value=casual_final, inline=False)


    return embed


def get_teaminfo_list():

    conn = db.open_conn()

    res = db.retrieve_data(conn, (db.get_teaminfo_list, None))
    conn.close()

    return res

def get_teaminfo(name):

    conn = db.open_conn()

    res = db.retrieve_data(conn, (db.get_teaminfo, [name]))
    conn.close()

    return res[0][0]


def get_official_roster(name):

    conn = db.open_conn()
    res = db.retrieve_data(conn, (db.get_players_by_official_roster, [name]))
    conn.close()

    return res

    


