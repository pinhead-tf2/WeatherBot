import aiosqlite
import discord
from discord import option
from discord.commands import SlashCommandGroup
from discord.ext import commands


async def options(ctx: discord.AutocompleteContext):
    async with aiosqlite.connect("botstorage.db") as db:
        async with db.execute("PRAGMA table_info(usersettings)") as cursor:
            # gets every column in the usersettings table
            allcolumns = [row[1] for row in await cursor.fetchall()]
            # gets all except user_id
            return [column for column in allcolumns if column != 'user_id']


class Settings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    settings = SlashCommandGroup("settings", "Change your preferences in the bot")

    @settings.command(name="view", description="Views a setting's current value")
    @option("option", description="Select the cog you wish to manage",
            autocomplete=discord.utils.basic_autocomplete(options))
    async def view(self, ctx,
                   option: str):
        async with aiosqlite.connect("botstorage.db") as db:
            async with db.execute(f"SELECT {option} FROM usersettings WHERE user_id = {ctx.author.id}") as cursor:
                row = await cursor.fetchone()
                if row is not None:
                    await ctx.respond(f"{option}'s value is {row[0]}", ephemeral=True)
                else:
                    await ctx.respond(f"You haven't set a value for this option yet. "
                                      f"Use `/settings set {option} value` to set one", ephemeral=True)


def setup(bot):
    bot.add_cog(Settings(bot))
