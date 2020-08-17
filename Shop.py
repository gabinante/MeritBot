import discord
from discord.ext import commands, tasks
import random
from discord.ext.commands import has_permissions
import math
from datetime import datetime
import sqlite3
import pytz
import asyncio
import traceback

name = "⭐ Merit"

conn = sqlite3.connect('merit.db', timeout=5.0)
c = conn.cursor()
conn.row_factory = sqlite3.Row


def itemChecker(item):
    c.execute(f''' SELECT item, price, stock FROM shophistory WHERE item = ?''', (f"{item}",))
    itemProperties = c.fetchall()[0]

    itemName = itemProperties[0]
    itemPrice = itemProperties[1]

    if itemProperties[2] == 0:
        itemStock = "Unlimited"
    else:
        itemStock = itemProperties[2]

    return itemName, itemPrice, itemStock


def stockTransaction(amount, item):
    c.execute(f''' SELECT stock FROM shop WHERE item = "{item}" ''')
    result = c.fetchall()

    for data in result:
        stockAvailable = data[0]
        stockAvailable += amount
        c.execute(f''' UPDATE shop SET stock = ? WHERE item = ? ''', (stockAvailable, item))
        conn.commit()

    return


def currencyTransaction(currency, id):
    c.execute(f''' UPDATE economy SET currency = ? WHERE user_id = ? ''', (currency, id))
    conn.commit()

    return


def get_currency(id):
    c.execute(f''' SELECT currency FROM economy WHERE user_id = {id} ''')
    result = c.fetchall()

    for data in result:
        currency = data[0]

        return currency


async def requestEmbedTemplate(ctx, description, author):
    embed = discord.Embed(description=f"{description}")
    embed.set_footer(text=f"Requested by {author}", icon_url=author.avatar_url)
    return await ctx.send(embed=embed)


async def requestEmbedTemplateWithTitle(ctx, title, description, author):
    embed = discord.Embed(title=f"{title}", description=f"{description}")
    embed.set_footer(text=f"Requested by {author}", icon_url=author.avatar_url)
    return await ctx.send(embed=embed)


async def shopEmbed(ctx, author, nameMessage=None, priceMessage=None, stockMessage=None):
    embed = discord.Embed(title=f"Product Item Information",
                          description=f"As you respond with more information, item info will show up below.")
    embed.set_footer(text=f'Type "cancel" to cancel.', icon_url=author.avatar_url)
    try:
        embed.add_field(name="Item", value=f"{nameMessage.content}")
    except:
        pass
    try:
        embed.add_field(name="Price", value=f"{priceMessage.content}")
    except:
        pass
    try:
        if stockMessage.content == "0":
            embed.add_field(name="Stock", value=f"Unlimited")
        else:
            embed.add_field(name="Stock", value=f"{stockMessage.content}")
    except:
        pass

    return await ctx.send(embed=embed)


async def shopErrorEmbed(ctx, author, nameMessage=None, priceMessage=None, stockMessage=None):
    embed = discord.Embed(title=f"Error!",
                          description=f"Invalid Price/Role/Argument provided. Please make sure your input is a valid positive integer or role mention!")
    embed.set_footer(text=f'Type "cancel" to cancel.', icon_url=author.avatar_url)
    try:
        embed.add_field(name="Item", value=f"{nameMessage.content}")
    except:
        pass
    try:
        embed.add_field(name="Price", value=f"{priceMessage.content} ⭐")
    except:
        pass
    try:
        if stockMessage.content == "0":
            embed.add_field(name="Stock", value=f"Unlimited")
        else:
            embed.add_field(name="Stock", value=f"{stockMessage.content}")
    except:
        pass

    return await ctx.send(embed=embed)


class Shop(commands.Cog, name=f'{name}'):  # You create a class instance and everything goes in it

    def __init__(self, bot):  # This runs when you first load this extension script
        self.bot = bot
        print(f"{name}.py has loaded!")

    @commands.command(description="`!leaderboard`\n\nChecks the Leaderboard for the richest coins owner!")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def leaderboard(self, ctx):

        top10Users = {}

        for key, value in c.execute('SELECT user_id, currency FROM economy ORDER BY currency DESC LIMIT 10'):
            top10Users.update({key: value})

        leaderboard_embed = discord.Embed(title="Merit Leaderboard",
                                          description=f"These are the users with the highest ⭐!",
                                          timestamp=datetime.utcnow())

        for user in top10Users:
            member = ctx.message.guild.get_member(user)

            leaderboard_embed.add_field(name=member,
                                        value=top10Users[user],
                                        inline=True)

        leaderboard_embed.set_footer(text=f"Requested by {ctx.message.author}", icon_url=ctx.author.avatar_url)
        await ctx.send(embed=leaderboard_embed)

    @commands.command(aliases=["bal"],
                      description="`!balance [user mention (optional)]`\n\nChecks the Balance of a user (or yourself)!")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def balance(self, ctx, user: discord.Member = None):

        if user:

            amount = get_currency(user.id)
            await requestEmbedTemplate(ctx, f"{user.mention} currently have {'{:,}'.format(amount)} ⭐.",
                                       ctx.message.author)



        else:

            amount = get_currency(ctx.message.author.id)
            await requestEmbedTemplate(ctx, f"You currently have {'{:,}'.format(amount)} ⭐.", ctx.message.author)

    @commands.command(description="`!buy [item name]`\n\n")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def buy(self, ctx, *, itemName: str):

        global roleRequirement

        c.execute(f'SELECT item, price, stock FROM shop WHERE server_id = ? AND item = ?',
                  (ctx.message.guild.id, itemName))
        result = c.fetchall()

        if not result:
            await requestEmbedTemplate(ctx,
                                       "There is no item with such name! Please make sure you have entered the correct item name.",
                                       ctx.message.author)
            return

        embed = discord.Embed(title="Your Cart: Is this the item you'd like to buy?",
                              description="Make sure it's the correct item. Items are **NOT** refundable!")

        for items in result:

            itemProperties = items

            itemName = itemProperties[0]
            embed.add_field(name=f"Item Name", value=f"{itemName}")
            itemPrice = itemProperties[1]
            embed.add_field(name=f"Price", value=f"{'{:,}'.format(itemPrice)} ⭐")
            itemStock = itemProperties[2]
            embed.add_field(name=f"Stock Remaining", value=f"{itemStock}")

            msg = await ctx.send(embed=embed)
            await msg.add_reaction("☑")
            await msg.add_reaction("❌")

            def confirmationCheck(reaction, user):

                return str(reaction.emoji) in ['☑',
                                               '❌'] and user == ctx.message.author and reaction.message.id == msg.id

            try:

                reaction, user = await self.bot.wait_for('reaction_add', check=confirmationCheck, timeout=30)

                if str(reaction.emoji) == "❌":

                    await requestEmbedTemplate(ctx, "Purchase cancelled.", ctx.message.author)

                elif str(reaction.emoji) == "☑":

                    balance = get_currency(ctx.message.author.id)
                    balance -= itemPrice

                    if balance < 0:

                        await requestEmbedTemplate(ctx,
                                                   f"❌ Purchase unsuccessful.\n\nYou do not have sufficient balance to make this purchase.\n\n**Your Balance:** {balance + itemPrice}",
                                                   ctx.message.author)

                    else:

                        if itemStock == "Unlimited":

                            c.execute(
                                f''' SELECT "{itemName}" FROM inventory WHERE user_id = {ctx.message.author.id}''')
                            result = c.fetchall()

                            itemQuantity = result[0][0]
                            itemQuantity += 1

                            c.execute(f'SELECT thankyoumessage FROM shopsettings WHERE identifier = {1}')
                            result = c.fetchall()

                            thankYouMessage = result[0][0]

                            currencyTransaction(balance, ctx.message.author.id)
                            c.execute(f''' UPDATE inventory SET "{itemName}" = ? WHERE user_id = ? ''',
                                      (itemQuantity, ctx.message.author.id))
                            conn.commit()

                            c.execute(f''' SELECT channel_id FROM meritLogging WHERE server_id = {ctx.guild.id}''')
                            loggingChannel = c.fetchall()[0][0]
                            loggingChannelObject = self.bot.get_channel(loggingChannel)

                            embed = discord.Embed(title="Receipt", description=f"Buyer: {ctx.message.author.mention}\nItem Purchased: {itemName}\nItem Price: {itemPrice}")
                            await loggingChannelObject.send(embed=embed)

                            await requestEmbedTemplate(ctx,
                                                       f"☑️ Purchase is successful.\n\n{thankYouMessage}\n\n**Balance:** {'{:,}'.format(balance)}\n**{itemName}'s Quantity (Now):** {'{:,}'.format(itemQuantity)}",
                                                       ctx.message.author)

                        elif itemStock <= 0:

                            await requestEmbedTemplate(ctx,
                                                       "❌ Purchase is unsuccessful.\n\nThere is insufficient stock for the item.",
                                                       ctx.message.author)

                        else:

                            c.execute(
                                f''' SELECT "{itemName}" FROM inventory WHERE user_id = {ctx.message.author.id}''')
                            result = c.fetchall()

                            itemQuantity = result[0][0]
                            itemQuantity += 1

                            c.execute(f'SELECT thankyoumessage FROM shopsettings WHERE identifier = {1}')
                            result = c.fetchall()

                            thankYouMessage = result[0][0]

                            stockTransaction(-1, itemName)
                            currencyTransaction(balance, ctx.message.author.id)

                            c.execute(f''' UPDATE inventory SET "{itemName}" = ? WHERE user_id = ? ''',
                                      (itemQuantity, ctx.message.author.id))
                            conn.commit()

                            c.execute(f''' SELECT channel_id FROM meritLogging WHERE server_id = {ctx.guild.id}''')
                            loggingChannel = c.fetchall()[0][0]
                            loggingChannelObject = self.bot.get_channel(loggingChannel)

                            embed = discord.Embed(title="Receipt",
                                                  description=f"Buyer: {ctx.message.author.mention}\nItem Purchased: {itemName}\nItem Price: {itemPrice}")
                            await loggingChannelObject.send(embed=embed)

                            await requestEmbedTemplate(ctx,
                                                       f"☑️ Purchase is successful.\n\n{thankYouMessage}\n\n**Balance:** {'{:,}'.format(balance)}\n**{itemName}'s Quantity (Now):** {'{:,}'.format(itemQuantity)}",
                                                       ctx.message.author)

            except asyncio.TimeoutError:

                await requestEmbedTemplate(ctx,
                                           "HMPH! You took too long to respond. Try again when you're going to respond to me!",
                                           ctx.message.author)

    @commands.command(description="`!inv`\n\n", aliases=["inv"])
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def inventory(self, ctx):

        c.execute(f''' SELECT * FROM inventory WHERE user_id = {ctx.author.id}''')
        names = list(map(lambda x: x[0], c.description))

        result = c.fetchall()
        inventory = result[0]

        embed = discord.Embed(title=f"{ctx.message.author}'s Inventory",
                              description=f"Here are the items and their respective quantity that you currently possess. Items with zero quantity will not be shown.")

        i = 1

        for item in inventory:

            try:
                if int(inventory[i]) != 0:
                    print(inventory[i])
                    embed.add_field(name=f"{names[i]}", value=f"{inventory[i]}")
                i += 1
            except IndexError:
                pass

        await ctx.send(embed=embed)

    @commands.command(description="`!shop`\n\nStarts the shop up.")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def shop(self, ctx):

        try:

            c.execute(f'SELECT name, description FROM shopsettings WHERE identifier = {1}')
            result = c.fetchall()

            title = result[0][0]
            desc = result[0][1]

            c.execute(f'SELECT item, price, stock FROM shop WHERE server_id = {ctx.message.guild.id}')
            items = c.fetchall()

            pages = math.ceil(len(items) / 4)

            i = 1

            everyPage = [item for item in items[4 * (i - 1):i * 4]]

            embed = discord.Embed(title=f"{title}", description=f"{desc}")
            embed.set_thumbnail(url=f"{ctx.message.guild.icon_url}")
            embed.set_footer(text=f"Page {i} of {pages}", icon_url=ctx.author.avatar_url)

            if not items:
                raise IndexError

            for item in everyPage:

                itemDetails = ""

                if item[2] != 0:

                    itemDetails += f"Stock Available: {item[2]}\n"

                else:

                    itemDetails += "Stock Available: Unlimited\n"

                embed.add_field(name=f"{item[1]} ⭐ • {item[0]} ", value=f"{itemDetails}", inline=False)

            msg = await ctx.send(embed=embed)
            await msg.add_reaction('⏪')
            await msg.add_reaction('⏩')

            def check(reaction, user):

                return str(reaction.emoji) in ['⏪',
                                               '⏩'] and user == ctx.message.author and reaction.message.id == msg.id

            async def handle_rotate(reaction, msg, check, i):

                await msg.remove_reaction(reaction, ctx.message.author)

                if str(reaction.emoji) == '⏩':

                    i += 1

                    if i > pages:

                        embed = discord.Embed(title=f"{title}", description=f"You have reached the end of the pages!")
                        embed.set_thumbnail(url=f"{ctx.message.guild.icon_url}")
                        embed.set_footer(text=f"Press '⏪' to go back.", icon_url=ctx.author.avatar_url)
                        await msg.edit(embed=embed)

                    else:

                        everyPage = [item for item in items[4 * (i - 1):i * 4]]

                        embed = discord.Embed(title=f"{title}", description=f"{desc}")
                        embed.set_thumbnail(url=f"{ctx.message.guild.icon_url}")
                        embed.set_footer(text=f"Page {i} of {pages}", icon_url=ctx.author.avatar_url)

                        if not items:
                            raise IndexError

                        for item in everyPage:

                            itemDetails = ""

                            if item[2] != 0:

                                itemDetails += f"Stock Available: {item[2]}\n"

                            else:

                                itemDetails += "Stock Available: Unlimited\n"

                            embed.add_field(name=f"{item[1]} ⭐ • {item[0]} ",
                                            value=f"{itemDetails}",
                                            inline=False)

                        await msg.edit(embed=embed)

                elif str(reaction.emoji) == '⏪':

                    i -= 1

                    if i <= 0:

                        embed = discord.Embed(title=f"{title}", description=f"You have reached the end of the pages!")
                        embed.set_thumbnail(url=f"{ctx.message.guild.icon_url}")
                        embed.set_footer(text=f"Press '⏩' to go back.", icon_url=ctx.author.avatar_url)
                        await msg.edit(embed=embed)

                    else:

                        everyPage = [item for item in items[4 * (i - 1):i * 4]]

                        embed = discord.Embed(title=f"{title}", description=f"{desc}")
                        embed.set_thumbnail(url=f"{ctx.message.guild.icon_url}")
                        embed.set_footer(text=f"Page {i} of {pages}", icon_url=ctx.author.avatar_url)

                        if not items:
                            raise IndexError

                        for item in everyPage:

                            itemDetails = ""

                            if item[2] != 0:

                                itemDetails += f"Stock Available: {item[2]}\n"

                            else:

                                itemDetails += "Stock Available: Unlimited\n"

                            embed.add_field(name=f"{item[1]} ⭐ • {item[0]} ",
                                            value=f"{itemDetails}",
                                            inline=False)

                        await msg.edit(embed=embed)

                else:

                    return

                reaction, user = await self.bot.wait_for('reaction_add', check=check)
                await handle_rotate(reaction, msg, check, i)

            reaction, user = await self.bot.wait_for('reaction_add', check=check)
            await handle_rotate(reaction, msg, check, i)


        except IndexError as e:

            await requestEmbedTemplate(ctx,
                                       "Sorry, there isn't such a page (or there isn't a shop yet)!\nTell the server owner / admins to add to the shop by typing `!setshop` or `!shopsettings`",
                                       ctx.message.author)
            traceback.print_exc()

        except Exception as e:

            traceback.print_exc()


def setup(bot):
    bot.add_cog(Shop(bot))
