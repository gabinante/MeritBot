import discord
from discord.ext import commands
import sqlite3
import random

conn = sqlite3.connect('prefix.db', timeout=5.0)
c = conn.cursor()
conn.row_factory = sqlite3.Row

startup_extensions = ['Status', 'adminCommands', 'Shop', 'serverSettings', 'roleIncome', 'Economy']
help_extensions = ['help']

c.execute('''CREATE TABLE IF NOT EXISTS prefix (
        `guild_id` INT PRIMARY KEY,
        `prefix` TEXT)''')

prefixDictionary = {}


def determine_prefix(guild):
    currentPrefix = prefixDictionary[guild.id]

    return currentPrefix


class Help(commands.Cog, name="Help"):

    def __init__(self, bot):
        self.bot = bot
        print("help.py extension has loaded!")

    commands.command(
        name='help',
        description='The help command!',
        aliases=['commands', 'command'],
        usage='cog'
    )

    @commands.command()
    async def help(self, ctx):

        for prefix in c.execute(f'SELECT guild_id, prefix FROM prefix'):
            prefixDictionary.update({prefix[0]: f"{prefix[1]}"})

        msgGuild = ctx.message.guild

        # The third parameter comes into play when
        # only one word argument has to be passed by the user

        # Get a list of all cogs

        cogs = [c for c in self.bot.cogs.keys()]
        guild = ctx.message.guild.id

        # If cog is specified by the user, we list the specific cog and commands with it

        global embed


        embed = discord.Embed(description=f"`{determine_prefix(msgGuild)}myprefix` for this server's prefix and `{determine_prefix(msgGuild)}setprefix` to change this server's prefix.",)
        embed.set_author(name="Command List and Help", icon_url=self.bot.user.avatar_url)
        embed.set_footer(
            text=f"Requested by {ctx.message.author.name} :: Your server's prefix currently is {determine_prefix(msgGuild)}",
            icon_url=self.bot.user.avatar_url)

        hidden_cogs = ['Help']

        for cog in cogs:

            if cog not in hidden_cogs:

                try:

                    cog_commands = self.bot.get_cog(cog).get_commands()
                    commands_list = ''

                    for comm in cog_commands:
                        commands_list += f'`{comm}` '

                    embed.add_field(name=cog, value=commands_list, inline=True)

                except:

                    pass

        msg = await ctx.send(embed=embed)

        await msg.add_reaction('🛠️')
        await msg.add_reaction('⭐')

        def check(reaction, user):

            return str(reaction.emoji) in ['🛠️', '⭐'] and user == ctx.message.author and reaction.message.id == msg.id

        async def handle_reaction(reaction, msg, check):

            await msg.remove_reaction(reaction, ctx.message.author)

            if str(reaction.emoji) == '🛠️':

                help_embed = discord.Embed(title='🛠️ Admin Commands Help')
                help_embed.set_footer(
                    text=f"Requested by {ctx.message.author.name} :: Your server's prefix currently is {determine_prefix(msgGuild)}",
                    icon_url=self.bot.user.avatar_url)

                cog_commands = self.bot.get_cog("🛠️ Admin Commands").get_commands()
                commands_list = ''

                for comm in cog_commands:
                    commands_list += f'**{comm.name}** - {comm.description}\n'

                    help_embed.add_field(name=comm, value=comm.description, inline=True)

                await msg.edit(embed=help_embed)

            elif str(reaction.emoji) == '⭐':

                help_embed = discord.Embed(title='⭐ Merit Help')
                help_embed.set_footer(
                    text=f"Requested by {ctx.message.author.name} :: Your server's prefix currently is {determine_prefix(msgGuild)}",
                    icon_url=self.bot.user.avatar_url)

                cog_commands = self.bot.get_cog("⭐ Merit").get_commands()
                commands_list = ''

                for comm in cog_commands:
                    commands_list += f'**{comm.name}** - {comm.description}\n'

                    help_embed.add_field(name=comm, value=comm.description, inline=True)

                await msg.edit(embed=help_embed)

            else:

                return

            reaction, user = await self.bot.wait_for('reaction_add', check=check, timeout=30)
            await handle_reaction(reaction, msg, check)

        reaction, user = await self.bot.wait_for('reaction_add', check=check, timeout=30)
        await handle_reaction(reaction, msg, check)


def setup(bot):
    bot.add_cog(Help(bot))
