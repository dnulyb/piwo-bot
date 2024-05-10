from interactions import (
    Extension,
    slash_command, 
    slash_option,
    OptionType,
    SlashContext,
    Embed,
    listen,
    Task,
    TimeTrigger
)
from interactions.api.events import Startup

import src.db.db as db

from dotenv import find_dotenv, load_dotenv, get_key

class Team(Extension):

    @slash_command(
        name="team",
        description="Team management, update team info etc.",
        sub_cmd_name="roster_message_update",
        sub_cmd_description="Updates the roster message in the roster channel.",
        dm_permission=False
    )
    async def roster_message_update(self, ctx: SlashContext):

        dotenv_path = find_dotenv()
        load_dotenv(dotenv_path)

        roster_channel_id = get_key(dotenv_path, ("DISCORD_ROSTER_CHANNEL"))
        roster_channel_message_id = get_key(dotenv_path, ("DISCORD_ROSTER_MESSAGE"))
        channel = self.bot.get_channel(roster_channel_id)
        message = await channel.fetch_message(roster_channel_message_id)

        embed = format_team_intro_embed()
        await message.edit(content="", embed=embed)

        await ctx.send("team roster message updated.")

    @slash_command(
        name="team",
        sub_cmd_name="send_message_to_roster_channel",
        sub_cmd_description="Sends a placeholder message to the roster channel.",
        dm_permission=False
    )
    async def send_message_to_roster_channel(self, ctx: SlashContext):

        dotenv_path = find_dotenv()
        load_dotenv(dotenv_path)

        roster_channel_id = get_key(dotenv_path, ("DISCORD_ROSTER_CHANNEL"))
        channel = self.bot.get_channel(roster_channel_id)

        await channel.send("[this message will be edited with the full team roster]")
        await ctx.send("message sent to roster channel.")


    @slash_command(
        name="team",
        sub_cmd_name="info_list",
        sub_cmd_description="Get all stored team info.",
        dm_permission=False
    )
    async def info_list(self, ctx: SlashContext):

        info_list = get_teaminfo_list()
        if(len(info_list) == 0):
            await ctx.send("Error: No team info found in database.", ephemeral=True)
            return
        
        embed = format_teaminfo_list(info_list)

        await ctx.send(embed=embed, ephemeral=True)

    @slash_command(
        name="team",
        sub_cmd_name="info_update",
        sub_cmd_description="Add or update team info.",
        dm_permission=False
    )
    @slash_option(
        name="name",
        description="Name of the info item you want to add/update",
        required=True,
        opt_type = OptionType.STRING
    )
    @slash_option(
        name="value",
        description="The info to add/update. Use '[NEWLINE]' to make a new line in the info.",
        required=True,
        opt_type = OptionType.STRING
    )
    async def info_update(self, ctx: SlashContext, name: str, value: str):

        try:

            # Hack to make newlines in the info
            value = value.replace("[NEWLINE]", "\n")

            conn = db.open_conn()
            query = [(db.add_to_teaminfo, (name, value))]
            db.execute_queries(conn, query)

            await ctx.send("Team info updated: " + name)

        except Exception as e:
            await ctx.send(f"Error occurred while running command: {e}", ephemeral=True)
        finally:
            conn.close()

    @slash_command(
        name="team",
        sub_cmd_name="info_remove",
        sub_cmd_description="Remove team info.",
        dm_permission=False
    )
    @slash_option(
        name="name",
        description="Name of the info item you want to remove",
        required=True,
        opt_type = OptionType.STRING
    )
    async def info_remove(self, ctx: SlashContext, name: str):

        try:

            conn = db.open_conn()
            query = [(db.remove_teaminfo, [name])]
            db.execute_queries(conn, query)

            await ctx.send("Team info removed: " + name)

        except Exception as e:
            await ctx.send(f"Error occurred while running command: {e}", ephemeral=True)
        finally:
            conn.close()

    @slash_command(
        name="team",
        sub_cmd_name="introduction",
        sub_cmd_description="Get the full team introduction.",
        dm_permission=False
    )
    async def introduction(self, ctx: SlashContext):

        embed = format_team_intro_embed()

        await ctx.send(embed=embed)


    @Task.create(TimeTrigger(hour=23, minute=0)) #midnight CET
    async def roster_update_trigger(self):

        dotenv_path = find_dotenv()
        load_dotenv(dotenv_path)

        roster_channel_id = get_key(dotenv_path, ("DISCORD_ROSTER_CHANNEL"))
        roster_channel_message_id = get_key(dotenv_path, ("DISCORD_ROSTER_MESSAGE"))
        channel = self.bot.get_channel(roster_channel_id)
        message = await channel.fetch_message(roster_channel_message_id)

        embed = format_team_intro_embed()
        await message.edit(content="", embed=embed)
    
    @listen(Startup)
    async def on_startup(self):
        self.roster_update_trigger.start()
    
def format_team_intro_embed():

    team_title = get_teaminfo("team_title")
    team_intro = get_teaminfo("team_intro")
    team_color = get_teaminfo("team_color")

    competitive_roster = get_official_roster("competitive")
    tech_roster = get_official_roster("tech")
    ice_roster = get_official_roster("ice")
    casual_roster = get_official_roster("casual")

    competitive_final = ""
    for (player, country, extra) in competitive_roster:
        competitive_final += country + " " + player
        if(extra == "captain"):
            competitive_final += " (C)"
        competitive_final += "\n"

    tech_final = ""
    for (player, country, extra) in tech_roster:
        tech_final += country + " " + player
        if(extra == "captain"):
            tech_final += " (C)"
        tech_final += "\n"
    
    ice_final = ""
    for (player, country, extra) in ice_roster:
        ice_final += country + " " + player
        if(extra == "captain"):
            ice_final += " (C)"
        ice_final += "\n"

    casual_final = ""
    for (player, country, extra) in casual_roster:
        casual_final += country + " " + player
        if(extra == "captain"):
            casual_final += " (C)"
        casual_final += "\n"
    

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

def format_teaminfo_list(info_list):

    embed = Embed()
    embed.title = "TeamInfo list"
    embed.description = "List of all the TeamInfo items in the database."

    for (info_name, info_value) in info_list:
        # Replace the "\n" to make it easier to copypaste & edit in discord slash command
        info_value = info_value.replace("\n", "[NEWLINE]")
        embed.add_field(name=info_name, value=info_value, inline=False)

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

    


