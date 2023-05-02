import aiosqlite
import discord
import os
import time
import aiohttp

from discord import option
from discord.ext import commands
from discord.commands import SlashCommandGroup
from os import getenv
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
bot = discord.Bot(
    debug_guilds=[991589246949404673],
    status=discord.Status.dnd,
    activity=discord.Game(name="Initializing..."),
    owner_ids=[246291288775852033]
)
bot.startup_complete = False
bot.WEATHER_TOKEN = getenv("WEATHER_TOKEN")
bot.startTime = time.time()
bot.version = 'Indev'
bot.releaseDate = 'Undetermined'
bot.aiohttp_session = None


@bot.event
async def on_ready():
    if bot.startup_complete:
        try:
            await bot.aiohttp_session.close()
            await bot.close()
        except RuntimeError:
            await bot.close()
        finally:
            exit()
    bot.startup_complete = True

    bot.aiohttp_session = aiohttp.ClientSession()
    bot.error_webhook = discord.Webhook.from_url(
        getenv("WEBHOOK_URL"),
        session=bot.aiohttp_session
    )

    async with aiosqlite.connect("botstorage.db") as db:
        await db.execute('''CREATE TABLE IF NOT EXISTS usersettings
                        ([user_id] INTEGER, [use_image] INTEGER)''')
        await db.commit()

    await bot.change_presence(activity=discord.Game('Awake'), status=discord.Status.online)
    print(f"{bot.user} started | Start timestamp: {datetime.now().strftime('%I:%M %p, %m/%d/%Y')} | "
          f"Time to start: {round(time.time() - bot.startTime, 4)} seconds")


admin = SlashCommandGroup("admin", "Admin/owner only commands", checks=[commands.is_owner()],)


@admin.command()
@commands.is_owner()
async def shutdown(ctx):
    await ctx.respond("ok, shutting down", ephemeral=True)
    await bot.aiohttp_session.close()
    await bot.close()


cogs = admin.create_subgroup("cogs", "Cog-related commands")


async def get_loaded_cogs():
    loaded_cogs = []
    for loaded_cog in list(bot.cogs):
        loaded_cogs.append(f"cogs.{loaded_cog}".lower())
    return loaded_cogs


async def cog_names(ctx: discord.AutocompleteContext):
    load_choice = ctx.options['load_choice']
    loaded_cogs = await get_loaded_cogs()
    if load_choice == 'reload' or load_choice == 'unload':
        return loaded_cogs
    else:
        unloaded_cogs = []
        for cogname in os.listdir('cogs'):
            if cogname.endswith('.py'):
                unloaded_cogs.append(f'cogs.{cogname[:-3]}'.lower())
        for loaded_cog in loaded_cogs:
            filter(loaded_cog.__ne__, unloaded_cogs)
        return unloaded_cogs


@cogs.command(name="cog", description="Manages the loadstate of a cog")
@option("load_choice", description="Choose what you'll do with the cog", choices=['reload', 'load', 'unload'])
@option("cog_name", description="Select the cog you wish to manage",
        autocomplete=discord.utils.basic_autocomplete(cog_names))
@commands.is_owner()
async def cog(ctx,
              load_choice: str,
              cog_name: str
              ):
    interaction = await ctx.respond(f"*Attempting to {load_choice} cog {cog_name}...*", ephemeral=True)
    match load_choice:
        case 'reload':
            bot.reload_extension(cog_name)
        case 'load':
            bot.load_extension(cog_name)
        case 'unload':
            bot.unload_extension(cog_name)
        case _:
            await interaction.edit_original_response(content="i don't know how you chose an invalid option, "
                                                             "but you did. great job.", ephemeral=True)
    await interaction.edit_original_response(content=f"**Successfully {load_choice}ed {cog_name}!**")


@cogs.command()
@commands.is_owner()
async def listcogs(ctx):
    await ctx.respond("Loaded cogs: ".join(map(str, bot.cogs)))


@bot.event
async def on_application_command_error(ctx: discord.ApplicationContext, error: Exception):
    if isinstance(error, discord.ApplicationCommandInvokeError):
        if isinstance((error := error.original), discord.HTTPException):
            message = (
                "An HTTP exception has occurred: "
                f"{error.status} {error.__class__.__name__}"
            )
            if error.text:
                message += f": {error.text}"
            return await ctx.respond(message, ephemeral=True)
        elif not isinstance(error, discord.DiscordException):
            await ctx.respond("Unexpected error encountered, how the fuck did you do that", ephemeral=True)
            header = f"Command: `/{ctx.command.qualified_name}`"
            if ctx.guild is not None:
                header += f" | Guild: `{ctx.guild.name} ({ctx.guild_id})`"
            # await bot.error_webhook.send(
            #     f"{header}\n```\n{''.join(format_exception(type(error), error, error.__traceback__))}"
            # )
            raise error
    await ctx.respond(
        embed=discord.Embed(
            title=error.__class__.__name__,
            description=str(error),
            color=discord.Color.red(),
        ), ephemeral=True
    )


for filename in os.listdir('cogs'):
    if filename.endswith('.py'):
        bot.load_extension(f'cogs.{filename[:-3]}')


bot.add_application_command(admin)  # preferably would automate this, idk how


bot.run(getenv("TOKEN"))
