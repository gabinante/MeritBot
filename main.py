import discord
import math
from discord.ext import commands
from discord.ext.commands import has_permissions
import sqlite3
from authentication import bot_token
from datetime import datetime
import pytz
import random
import traceback

now = int(datetime.now(pytz.timezone("Singapore")).timestamp())

conn = sqlite3.connect('prefix.db', timeout=5.0)
c = conn.cursor()
conn.row_factory = sqlite3.Row

startup_extensions = ['merit', 'Shop']
help_extensions = ['help']

c.execute('''CREATE TABLE IF NOT EXISTS prefix (
        `guild_id` INT PRIMARY KEY,
        `prefix` TEXT)''')

prefixDictionary = {}

for prefix in c.execute(f'SELECT guild_id, prefix FROM prefix'):
    prefixDictionary.update({prefix[0]: f"{prefix[1]}"})


async def determine_prefix(bot, message):
    prefixDictionary = {}

    for prefix in c.execute(f'SELECT guild_id, prefix FROM prefix'):
        prefixDictionary.update({prefix[0]: f"{prefix[1]}"})

    currentPrefix = prefixDictionary[message.guild.id]

    return commands.when_mentioned_or(currentPrefix)(bot, message)


bot = commands.Bot(command_prefix=determine_prefix, help_command=None)

if __name__ == "__main__":

    for extension in startup_extensions:

        try:

            bot.load_extension(extension)

        except Exception as e:  #

            exc = f'{type(e).__name__}: {e}'
            print(f'Failed to load extension {extension}\n{exc}')
            traceback.print_exc()


@bot.command(help="Loads an extension. Bot Owner only!")
@commands.is_owner()
async def load(ctx, extension_name: str):
    """Loads an extension."""

    try:

        bot.load_extension(extension_name)

    except (AttributeError, ImportError) as e:

        await ctx.send(f"```py\n{type(e).__name__}: {str(e)}\n```")
        return

    await ctx.send(f"{extension_name} loaded.")


@bot.command(help="Unloads an extension. Bot Owner only!")
@commands.is_owner()
async def unload(ctx,
                 extension_name: str):  # Used as a command on Discord to unload an extension script for maintenance. Same as load.

    """Unloads an extension."""

    bot.unload_extension(extension_name)

    await ctx.send(f"{extension_name} unloaded.")


@bot.command()
@has_permissions(manage_messages=True)
async def setprefix(ctx, new):
    guild = ctx.message.guild.id
    name = bot.get_guild(guild)
    c = conn.cursor()

    prefixDictionary.update({guild: f"{new}"})

    for key, value in c.execute('SELECT guild_id, prefix FROM prefix'):

        if key == guild:
            c.execute(''' UPDATE prefix SET prefix = ? WHERE guild_id = ? ''', (new, guild))
            conn.commit()
            embed = discord.Embed(description=f"{name}'s Prefix has now changed to `{new}`.")
            await ctx.send(embed=embed)

    c.close()


@bot.command()
async def myprefix(ctx):
    guild = ctx.message.guild.id
    name = bot.get_guild(guild)
    currentPrefix = prefixDictionary[guild]
    embed = discord.Embed(description=f"{name}'s Prefix currently is `{currentPrefix}`.")
    await ctx.send(embed=embed)


@bot.event
async def on_ready():
    print("Logging in as " + str(bot.user))
    print(str(bot.user) + " has connected to Discord!")
    print("Current Discord Version: " + discord.__version__)
    print("Number of servers currently connected to MeritBot:")
    print(len([s for s in bot.guilds]))
    print("Number of players currently connected to MeritBot:")
    m = sum(guild.member_count for guild in bot.guilds)
    print(m)

    guild_id_database = []

    for row in c.execute('SELECT guild_id FROM prefix'):
        guild_id_database.append(row[0])

    async for guild in bot.fetch_guilds(limit=150):

        if guild.id not in guild_id_database:
            c.execute(''' INSERT OR REPLACE INTO prefix VALUES (?, ?)''', (guild.id, '!'))
            conn.commit()
            print(f"Created a prefix database for {guild.id}")


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):

        seconds = error.retry_after
        minutes = seconds / 60
        hours = seconds / 3600

        if seconds / 60 < 1:

            embed = discord.Embed(
                description=f'Scram! You\'re using this command too often! Try again in {str(int(seconds))} seconds!')
            await ctx.send(embed=embed)

        elif minutes / 60 < 1:

            embed = discord.Embed(
                description='Scram! You\'re using this command too often! Try again in {0} minutes and {1} seconds!'.format(
                    math.floor(minutes), (int(seconds) - math.floor(minutes) * 60)))
            await ctx.send(embed=embed)

        else:

            embed = discord.Embed(
                description='Scram! You\'re using this command too often! Try again in {0} hours, {1} minutes, {2} seconds!'.format(
                    math.floor(hours), (int(minutes) - math.floor(hours) * 60),
                    int(seconds) - math.floor(minutes) * 60))
            await ctx.send(embed=embed)

    if isinstance(error, commands.CheckFailure):
        embed = discord.Embed(description='You do not have the permission to do this!')
        await ctx.send(embed=embed)

    if isinstance(error, commands.MissingRequiredArgument):
        embed = discord.Embed(description='Missing arguments on your command! Please check and retry again!')
        await ctx.send(embed=embed)
    raise error


@bot.event
async def on_guild_join(guild):
    guild_id_database = []

    for row in c.execute('SELECT guild_id FROM prefix'):
        guild_id_database.append(row[0])

    if guild.id not in guild_id_database:
        c.execute(''' INSERT OR REPLACE INTO prefix VALUES (?, ?)''', (guild.id, '!'))
        conn.commit()
        print(f"Joined a new server: created a prefix database for {guild.id}")


@bot.command()
async def ping(ctx):
    await ctx.send(f"Latency: {bot.latency}s")


bot.remove_command('help')

if __name__ == "__main__":  # Loads all extension specified above on bot start-up.
    for extension in help_extensions:
        try:
            bot.load_extension(extension)
        except Exception as e:
            exc = f'{type(e).__name__}: {e}'
            print(f'Failed to load extension {extension}\n{exc}')

bot.run(f'{bot_token}', bot=True, reconnect=True)
