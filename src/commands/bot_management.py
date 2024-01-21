from interactions import (
    Extension,
    slash_command, 
    SlashContext,
    check, 
    is_owner
)

import pkgutil

"""
#custom check example
async def my_check(ctx: BaseContext):
    return ctx.author.username.startswith("a")

@slash_command(name="my_command")
@check(my_check)
async def command(ctx: SlashContext):
    await ctx.send("Your username starts with an 'a'!", ephemeral=True)
"""


class BotManagement(Extension):

    @slash_command(
        name="shutdown",
        description="Shuts down the bot."
    )
    @check(is_owner())
    async def shutdown(self, ctx: SlashContext):
        await ctx.send("Shutting down the bot.", ephemeral=True)
        await self.bot.stop()

    @slash_command(
        name="reload_extensions",
        description="Reloads all bot extensions."
    )
    @check(is_owner())
    async def reload_extensions(self, ctx: SlashContext):
        extensions = [m.name for m in pkgutil.iter_modules(["src/commands"], prefix="src.commands.")]
        for extension in extensions:
            self.bot.reload_extension(extension)

        await ctx.send("Reloaded bot extensions.", ephemeral=True)

    @slash_command(
        name="ping",
        description="Replies to pings",
    )
    async def ping(self, ctx: SlashContext):
        await ctx.send("pong")