from interactions import (
    Extension,
    slash_command, 
    slash_option, 
    SlashContext,
    OptionType,
    SlashCommandChoice,
    Embed
)
import src.db.db as db

class Player(Extension):

    @slash_command(
        name="player",
        description="Player management commands.",
        sub_cmd_name="add",
        sub_cmd_description="Add a player to the database.",
        dm_permission=False
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
    @slash_option(
        name="country",
        description="Discord flag country code of the player you want to add. Example: :flag_pl:",
        required=False,
        opt_type = OptionType.STRING
    )
    @slash_option(
        name="official_roster",
        description="Is the player part of an official PIWO roster?",
        required=False,
        opt_type = OptionType.STRING
    )
    @slash_option(
        name="extra",
        description="If the player is captain, etc.",
        required=False,
        opt_type = OptionType.STRING
    )
    async def add(self, ctx: SlashContext, nickname: str, account_id: str, 
                         country: str = None, official_roster: str = None, extra: str = None):

        conn = db.open_conn()

        try:

            query = [(db.add_player, (nickname, account_id, country, official_roster, extra))]
            db.execute_queries(conn, query)
            res = "Added player: " + nickname

            # always send reply
            await ctx.send(f"{res}")

        except Exception as e:
            await ctx.send(f"Error occurred while running command: {e}", ephemeral=True)

        finally:
            conn.close() 

    @slash_command(
        name="player",
        sub_cmd_name="remove",
        sub_cmd_description="Remove a player from the database.",
        dm_permission=False
    )
    @slash_option(
        name="nickname",
        description="Nickname of the player you want to remove.",
        required=True,
        opt_type = OptionType.STRING
    )
    async def remove(self, ctx: SlashContext, nickname: str):

        conn = db.open_conn()

        try:

            query = [(db.remove_player, [nickname])]
            db.execute_queries(conn, query)
            res = "Removed player: " + nickname

            # always send reply
            await ctx.send(f"{res}")

        except Exception as e:
            await ctx.send(f"Error occurred while running command: {e}", ephemeral=True)

        finally:
            conn.close() 

    @slash_command(
        name="list",
        description="List all database entries of a certain type.",
        sub_cmd_name="players",
        sub_cmd_description="Lists all players in the database.",
        dm_permission=False
    )
    async def list(self, ctx: SlashContext):

        conn = db.open_conn()

        try:

            query = [db.list_players, None]
            res = db.retrieve_data(conn, query)
            if(len(res) == 0):
                await ctx.send("Error retrieving players: No players found.", ephemeral=True)
                return
            
            embed = format_player_list(res)

            # always send reply
            await ctx.send(embed=embed, ephemeral=True)

        except Exception as e:
            await ctx.send(f"Error occurred while running command: {e}", ephemeral=True)

        finally:
            conn.close() 

    @slash_command(
        name="info",
        description="Get info about various things in the database.",
        sub_cmd_name="player",
        sub_cmd_description="Get info about a player in the database.",
        dm_permission=False
    )
    @slash_option(
        name="nickname",
        description="Nickname of the player you want info about.",
        required=True,
        opt_type = OptionType.STRING
    )
    async def info_player(self, ctx: SlashContext, nickname: str):

        conn = db.open_conn()

        try:

            query = (db.get_player_info, [nickname])
            res = db.retrieve_data(conn, query)
            if(len(res) == 0):
                await ctx.send("Error retrieving player info: Player not found.", ephemeral=True)
                return
            
            embed = format_player(res)

            # always send reply
            await ctx.send(embed=embed, ephemeral=True)

        except Exception as e:
            await ctx.send(f"Error occurred while running command: {e}", ephemeral=True)

        finally:
            conn.close() 

    @slash_command(
        name="player",
        sub_cmd_name="update",
        sub_cmd_description="Update info for a player.",
        dm_permission=False
    )
    @slash_option(
        name="nickname",
        description="Nickname of the player.",
        required=True,
        opt_type = OptionType.STRING
    )
    @slash_option(
        name="action",
        description="What to update.",
        required=True,
        opt_type = OptionType.STRING,
        choices=[
            SlashCommandChoice(name="nickname", value="nickname"),
            SlashCommandChoice(name="account_id", value="account_id"),
            SlashCommandChoice(name="country", value="country"),
            SlashCommandChoice(name="official_roster", value="official_roster"),
            SlashCommandChoice(name="extra", value="extra")        ]
    )
    @slash_option(
        name="value",
        description="The updated value.",
        required=True,
        opt_type = OptionType.STRING
    )
    async def update(self, ctx: SlashContext, nickname: str, action: str, value: str):

        conn = db.open_conn()

        try:
            match action:
                case "nickname":
                    query = [(db.update_player_name, (value, nickname))]
                    db.execute_queries(conn, query)
                    res = "Updated nickname for player: " + nickname + "," + value
                case "account_id":
                    query = [(db.update_player_account_id, (value, nickname))]
                    db.execute_queries(conn, query)
                    res = "Updated account_id for player: " + nickname + "," + value
                case "country":
                    query = [(db.update_player_country, (value, nickname))]
                    db.execute_queries(conn, query)
                    res = "Updated country for player: " + nickname + "," + value
                case "official_roster":
                    query = [(db.update_player_official_roster, (value, nickname))]
                    db.execute_queries(conn, query)
                    res = "Updated official_roster for player: " + nickname + "," + value
                case "extra":
                    query = [(db.update_player_extra, (value, nickname))]
                    db.execute_queries(conn, query)
                    res = "Updated extra for player: " + nickname + "," + value
                case _:
                    res = "invalid player update action"

            # always send reply
            await ctx.send(f"{res}")

        except Exception as e:
            await ctx.send(f"Error occurred while running command: {e}", ephemeral=True)

        finally:
            conn.close() 


def format_player_list(players):

    embed = Embed()
    embed.title = "List of all players:"
    field_name = '\u200b'


    value = ""

    for i, (player, country, roster) in enumerate(players, start=1):

        if (country is None):
            country = "None"
        if (roster is None):
            roster = "None"
        value += player + ", " + country + ", " + roster + "\n"

        # Have we almost reached the embed value limit?
        if(len(value) >= 900):
            embed.add_field(name=field_name, value=value, inline=False)

            # Are there more players?
            if(i < len(players)):
                value = ""
            else:
                #If not, we can just return
                return embed

    embed.add_field(name=field_name, value=value, inline=False)


    return embed

def format_player(player):

    embed = Embed()
    embed.title = "Player info"

    (nickname, account_id, country, official_roster) = player[0]
    if (account_id is None):
        account_id = "None"
    if (country is None):
        country = "None"
    if (official_roster is None):
        official_roster = "None"

    value = ""
    value += "Nickname: " + nickname + "\n"
    value += "Account id: " + account_id + "\n"
    value += "Country: " + country + "\n"
    value += "Official roster: " + official_roster

    embed.add_field(name="\u200b", value=value, inline=False)

    return embed