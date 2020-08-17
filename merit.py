import asyncio
import sqlite3
import traceback

import discord
from discord.ext import commands
from discord.ext.commands import has_permissions

name = "🛠️ Admin Commands"

conn = sqlite3.connect('merit.db', timeout=5.0)
c = conn.cursor()
conn.row_factory = sqlite3.Row

c.execute('''CREATE TABLE IF NOT EXISTS meritLogging (`server_id` INT PRIMARY KEY, `channel_id` INT) ''')

c.execute('''CREATE TABLE IF NOT EXISTS inventory (`user_id` INT PRIMARY KEY) ''')

c.execute('''CREATE TABLE IF NOT EXISTS shop (`server_id` INT, `item` STR, `price` INT, `stock` INT) ''')

c.execute('''CREATE TABLE IF NOT EXISTS shophistory (`server_id` INT, `item` STR, `price` INT, `stock` INT) ''')

c.execute('''CREATE TABLE IF NOT EXISTS economy (`user_id` INT PRIMARY KEY, `currency` INT)''')

c.execute(
    '''CREATE TABLE IF NOT EXISTS shopsettings ( `identifier` INT PRIMARY KEY, `name` STR, `description` STR, `thankyoumessage` STR) ''')




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


def createProfile(ID):
    c.execute(''' INSERT OR REPLACE INTO economy VALUES (?, ?) ''', (ID, 0))
    conn.commit()
    print(f"Added for {ID} into economy database.")

    try:
        c.execute(f''' INSERT INTO inventory (user_id) VALUES ({ID}) ''')
        conn.commit()
        print(f"Added for {ID} into inventory database.")
    except:
        print(f"{ID} already has an inventory database!")


class Merit(commands.Cog, name=f'{name}'):  # You create a class instance and everything goes in it

    def __init__(self, bot):  # This runs when you first load this extension script
        self.bot = bot
        print(f"{name}.py has loaded!")

    @commands.Cog.listener()
    async def on_guild_join(self, guild):

        economy_database = []

        for user in c.execute('SELECT user_id FROM economy'):
            economy_database.append(user[0])

        for member in guild.members:

            id = member.id

            if id not in economy_database:

                if not member.bot:
                    createProfile(id)

    @commands.Cog.listener()
    async def on_member_join(self, member):

        economy_database = []

        for user in c.execute('SELECT user_id FROM economy'):
            economy_database.append(user[0])

        id = member.id

        if id not in economy_database:

            if not member.bot:
                createProfile(id)

    @commands.Cog.listener()
    async def on_ready(self):

        economy_database = []

        for user in c.execute('SELECT user_id FROM economy'):
            economy_database.append(user[0])

        for guild in self.bot.guilds:

            for member in guild.members:

                id = member.id

                if id not in economy_database:  # Creates a database for a new discord member that joined the server

                    if not member.bot:
                        createProfile(id)

    @commands.command(description="`$meritlogs [channel mention]`\n\nLogs purchase at mentioned channel.")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @has_permissions(administrator=True)
    async def meritlogs(self, ctx, channel: discord.TextChannel):

        c.execute(''' INSERT INTO meritLogging VALUES (?, ?) ''', (ctx.guild.id, channel.id))
        conn.commit()

        await requestEmbedTemplate(ctx, f"☑️ Merit Logging successfully enabled on {channel.mention}.",
                                   ctx.message.author)

    @commands.command(description="`$reset [user mention]`\n\nResets a user's balance! Administrator Only!")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @has_permissions(administrator=True)
    async def reset(self, ctx, user: discord.Member):

        currencyTransaction(0, user.id)
        await requestEmbedTemplate(ctx, f"Successfully reset the balance of {user.mention}", ctx.message.author)

    @commands.command(description="`$resetinv [user mention]`\n\nResets a user's balance! Administrator Only!")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @has_permissions(administrator=True)
    async def resetinv(self, ctx, user: discord.Member):

        c.execute(f''' SELECT * FROM inventory WHERE user_id = {user.id}''')
        names = list(map(lambda x: x[0], c.description))
        result = c.fetchall()
        userData = result[0]

        i = 1

        for item in userData:
            c.execute(f''' UPDATE inventory SET "{names[i]}" = ? WHERE user_id = ? ''', (0, user.id))
            conn.commit()
            i += 1

        await requestEmbedTemplate(ctx, f"{user.mention}'s inventory has been successfully reset!", ctx.message.author)

    @commands.command(description="`$add [user mention] [amount]`\n\nModifies a user's balance! Administrator Only!")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @has_permissions(administrator=True)
    async def add(self, ctx, user: discord.Member, amount: int):

        if user == ctx.message.author:

            await requestEmbedTemplate(ctx, f"Administrators may not assign themselves merit points!",
                                       ctx.message.author)
            return

        balance = get_currency(user.id)
        balance += amount
        currencyTransaction(balance, user.id)

        if amount > 0:

            await requestEmbedTemplate(ctx, f"Successfully added {amount} ⭐ to {user.mention}",
                                       ctx.message.author)

        elif amount < 0:

            await requestEmbedTemplate(ctx,
                                       f"Successfully removed {abs(amount)} ⭐ from {user.mention}",
                                       ctx.message.author)

    @commands.command(description="`$shopsettings`\n\nSets the title and description of the shop.")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @has_permissions(administrator=True)
    async def shopsettings(self, ctx):

        def messageCheck(m):
            return m.channel == ctx.message.channel and m.author == ctx.message.author

        try:

            await requestEmbedTemplate(ctx, "What will be the title of your shop?", ctx.message.author)

            titleMessage = await self.bot.wait_for('message', check=messageCheck, timeout=30)

            await requestEmbedTemplate(ctx, "What will be the description of your shop?", ctx.message.author)

            descriptionMessage = await self.bot.wait_for('message', check=messageCheck, timeout=30)

            await requestEmbedTemplate(ctx, "What will be the thank you message of your shop?", ctx.message.author)

            thankYouMessage = await self.bot.wait_for('message', check=messageCheck, timeout=30)

            msg = await requestEmbedTemplate(ctx,
                                             f"**These are your shop details:**\n\n**Title:** {titleMessage.content}\n\n**Description:** {descriptionMessage.content}\n\n**Thank You Message:** {thankYouMessage.content}\n\nThis is the information you gave me. Is it correct?\nPlease react accordingly if it's correct. Otherwise, I will cancel the entry.",
                                             ctx.message.author)

            await msg.add_reaction("☑")
            await msg.add_reaction("❌")

            def confirmationCheck(reaction, user):

                return str(reaction.emoji) in ['☑',
                                               '❌'] and user == ctx.message.author and reaction.message.id == msg.id

            reaction, user = await self.bot.wait_for('reaction_add', check=confirmationCheck, timeout=30)

            if str(reaction.emoji) == "❌":

                await requestEmbedTemplate(ctx, "Shop set-up cancelled.", ctx.message.author)

            elif str(reaction.emoji) == "☑":

                c.execute(''' INSERT OR REPLACE INTO shopsettings VALUES (?, ?, ?, ?) ''',
                          (1, titleMessage.content, descriptionMessage.content, thankYouMessage.content))
                conn.commit()
                await requestEmbedTemplate(ctx, "☑️ Shop Created Successfully.", ctx.message.author)

        except asyncio.TimeoutError:

            await requestEmbedTemplate(ctx,
                                       "HMPH! You took too long to respond. Try again when you're going to respond to me!",
                                       ctx.message.author)

    @commands.command(description="`$setshop`\n\n")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @has_permissions(administrator=True)
    async def setshop(self, ctx):
        msg = await requestEmbedTemplate(ctx,
                                         "Would you like to `add` a new item or `remove` an existing item or `edit` an existing item?\nPlease react with ➕, ➖ or 🛠️ respectively.\nyou can cancel this command by reacting with ❌.",
                                         ctx.message.author)
        await msg.add_reaction("➕")
        await msg.add_reaction("➖")
        await msg.add_reaction("🛠️")
        await msg.add_reaction("❌")

        def check(reaction, user):
            return str(reaction.emoji) in ['➕', '➖', '🛠️', '❌'] and user == ctx.message.author and reaction.message.id == msg.id

        try:

            reaction, user = await self.bot.wait_for('reaction_add', check=check, timeout=30)

            def messageCheck(m):
                return m.channel == ctx.message.channel and m.author == ctx.message.author

            if str(reaction.emoji) == "➕":

                await ctx.send("**What should the name of the item be?**")
                msg = await shopEmbed(ctx, ctx.message.author)
                nameMessage = await self.bot.wait_for('message', check=messageCheck)

                items = []

                c.execute(f''' SELECT item FROM shop ''')
                result = c.fetchall()

                for item in result:
                    items.append(item[0])

                if nameMessage.content == "cancel":

                    await requestEmbedTemplate(ctx, "Item creation / deletion / editing cancelled.",
                                               ctx.message.author)

                elif nameMessage.content in items:

                    await requestEmbedTemplate(ctx,
                                               "The item already exist! Please restart the command and use a different name!",
                                               ctx.message.author)

                else:

                    await ctx.send("**How much will this item cost?**")
                    msg = await shopEmbed(ctx, ctx.message.author, nameMessage)

                    priceMessage = await self.bot.wait_for('message', check=messageCheck)

                    while not priceMessage.content.isdigit() or priceMessage.content == "0" or priceMessage.content == "cancel":

                        await ctx.send("**How much will this item cost?**")
                        msg = await shopErrorEmbed(ctx, ctx.message.author, nameMessage)

                        priceMessage = await self.bot.wait_for('message', check=messageCheck)

                        if priceMessage.content == "cancel":
                            await requestEmbedTemplate(ctx, "Item creation / deletion / editing cancelled.",
                                                       ctx.message.author)
                            break

                    if priceMessage.content.isdigit():

                        await ctx.send(
                            "**How many of this item will be sold before removed from the shop?\nPlease put 0 for unlimited / infinity.**")
                        msg = await shopEmbed(ctx, ctx.message.author, nameMessage, priceMessage)
                        stockMessage = await self.bot.wait_for('message', check=messageCheck)

                        while not stockMessage.content.isdigit() or str(
                                stockMessage.content) == "cancel" or int(stockMessage.content) < 0:

                            await ctx.send(
                                "**How many of this item will be sold before removed from the shop?\nPlease put 0 for unlimited / infinity.**")

                            msg = await shopErrorEmbed(ctx, ctx.message.author, nameMessage, priceMessage)

                            stockMessage = await self.bot.wait_for('message', check=messageCheck)

                            if stockMessage.content == "cancel":
                                await requestEmbedTemplate(ctx,
                                                           "Item creation / deletion / editing cancelled.",
                                                           ctx.message.author)
                                break

                        if stockMessage.content.isdigit():

                            await ctx.send(
                                "**Wonderful Job! This is the information you gave me. Is it correct?**\nPlease react accordingly if it's correct. Otherwise, I will cancel item creation so you can start all over again.")
                            msg = await shopEmbed(ctx, ctx.message.author, nameMessage, priceMessage, stockMessage)

                            await msg.add_reaction("☑")
                            await msg.add_reaction("❌")

                            def confirmationCheck(reaction, user):
                                return str(reaction.emoji) in ['☑',
                                                               '❌'] and user == ctx.message.author and reaction.message.id == msg.id

                            reaction, user = await self.bot.wait_for('reaction_add',
                                                                     check=confirmationCheck,
                                                                     timeout=30)

                            if str(reaction.emoji) == "❌":

                                await requestEmbedTemplate(ctx,
                                                           "Item creation / deletion / editing cancelled.",
                                                           ctx.message.author)

                            elif str(reaction.emoji) == "☑":

                                if stockMessage.content == "0":
                                    c.execute(
                                        ''' INSERT OR REPLACE INTO shop VALUES (?, ?, ?, ?) ''',
                                        (ctx.message.guild.id, nameMessage.content,
                                         priceMessage.content, "Unlimited"))
                                    conn.commit()
                                    c.execute(
                                        ''' INSERT OR REPLACE INTO shophistory VALUES (?, ?, ?, ?) ''',
                                        (ctx.message.guild.id, nameMessage.content,
                                         priceMessage.content, "Unlimited"))
                                    conn.commit()
                                    addItems = f"ALTER TABLE inventory ADD COLUMN `{nameMessage.content}` DEFAULT 0"
                                    c.execute(addItems)
                                    await requestEmbedTemplate(ctx,
                                                               "☑️ Item Created Successfully.",
                                                               ctx.message.author)

                                else:

                                    c.execute(
                                        ''' INSERT OR REPLACE INTO shop VALUES (?, ?, ?, ?) ''',
                                        (ctx.message.guild.id, nameMessage.content, priceMessage.content,
                                         stockMessage.content))
                                    conn.commit()
                                    c.execute(
                                        ''' INSERT OR REPLACE INTO shophistory VALUES (?, ?, ?, ?) ''',
                                        (ctx.message.guild.id, nameMessage.content, priceMessage.content,
                                         stockMessage.content))
                                    conn.commit()
                                    addItems = f"ALTER TABLE inventory ADD COLUMN `{nameMessage.content}` DEFAULT 0"
                                    c.execute(addItems)
                                    await requestEmbedTemplate(ctx,
                                                               "☑️ Item Created Successfully.",
                                                               ctx.message.author)


            elif str(reaction.emoji) == "➖":

                items = []

                c.execute(f''' SELECT item FROM shop ''')

                result = c.fetchall()

                for item in result:
                    items.append(item[0])

                def messageCheck(m):

                    return m.channel == ctx.message.channel and m.author == ctx.message.author

                try:

                    await requestEmbedTemplate(ctx,

                                               "Please respond with the name of the item you'd like me to remove.\nYou can cancel this command using `cancel`",

                                               ctx.message.author)

                    itemName = await self.bot.wait_for('message', check=messageCheck, timeout=30)

                    if itemName.content == "cancel":

                        await requestEmbedTemplate(ctx, "Item creation / deletion / editing cancelled.",

                                                   ctx.message.author)


                    elif itemName.content not in items:

                        await requestEmbedTemplate(ctx, "This item doesn't exist. Please restart the command!",

                                                   ctx.message.author)


                    else:

                        c.execute(f'SELECT item, price, stock FROM shop WHERE server_id = ? AND item = ?', (ctx.message.guild.id, itemName))

                        items = c.fetchall()
                        item = items[0]
                        itemDetails = ""

                        if item[2] != 0:
                            itemDetails += f"Stock Available: {item[2]}\n"

                        else:
                            itemDetails += "> Stock Available: Unlimited\n"


                        embed = discord.Embed(title="Deleted Products")

                        embed.add_field(name=f"{item[1]} • {item[0]} ", value=f"{itemDetails}", inline=False)

                        c.execute(''' DELETE FROM shop where item = ? ''', (f"{itemName}",))
                        conn.commit()
                        await ctx.send(embed=embed)


                except asyncio.TimeoutError:

                    await requestEmbedTemplate(ctx,

                                               "HMPH! You took too long to respond. Try again when you're going to respond to me!",

                                               ctx.message.author)




            elif str(reaction.emoji) == "🛠️":

                items = []

                c.execute(f''' SELECT item FROM shop ''')

                result = c.fetchall()

                for item in result:
                    items.append(item[0])

                def messageCheck(m):

                    return m.channel == ctx.message.channel and m.author == ctx.message.author

                try:

                    await requestEmbedTemplate(ctx,

                                               "Please respond with the name of the item you'd like me to edit.\nYou can cancel this command using `cancel`",

                                               ctx.message.author)

                    itemName = await self.bot.wait_for('message', check=messageCheck, timeout=30)

                    if itemName.content == "cancel":

                        await requestEmbedTemplate(ctx, "Item creation / deletion / editing cancelled.",

                                                   ctx.message.author)


                    elif itemName.content not in items:

                        await requestEmbedTemplate(ctx, "This item doesn't exist. Please restart the command!",

                                                   ctx.message.author)


                    else:

                        await requestEmbedTemplate(ctx, "What would you like to edit? Please name one of the following: `name` `price` `stock`", ctx.message.author)

                        editMessage = await self.bot.wait_for('message', check=messageCheck, timeout=30)

                        validResponse = ['name', 'price', 'stock']

                        c.execute(f'SELECT item, price, stock FROM shop WHERE server_id = ? AND item = ?', (ctx.guild.id, f"{itemName.content}"))

                        items = c.fetchall()

                        if editMessage.content not in validResponse:

                            await requestEmbedTemplate(ctx,

                                                       "This is not a valid response. Please restart the command!",

                                                       ctx.message.author)


                        else:

                            if editMessage.content == "name":

                                await requestEmbedTemplate(ctx,

                                                           "What would you want the name to be changed to?",

                                                           ctx.message.author)

                                nameMessage = await self.bot.wait_for('message', check=messageCheck, timeout=30)

                                if nameMessage.content in items:

                                    await requestEmbedTemplate(ctx,

                                                               "Item name already exists! Please restart the command!",

                                                               ctx.message.author)


                                else:

                                    c.execute(f''' UPDATE shop SET item = ? WHERE item = ? ''',

                                              (nameMessage.content, f"{itemName.content}"))

                                    conn.commit()

                                    c.execute(f''' UPDATE shophistory SET item = ? WHERE item = ? ''',

                                              (nameMessage.content, f"{itemName.content}"))

                                    conn.commit()

                                    await requestEmbedTemplate(ctx,

                                                               f"Okie! Updated item name from `{itemName.content}` to `{nameMessage.content}` successfully.",

                                                               ctx.message.author)


                            elif editMessage.content == "price":

                                await requestEmbedTemplate(ctx, "What would you want the price to be changed to?",

                                                           ctx.message.author)

                                priceMessage = await self.bot.wait_for('message', check=messageCheck, timeout=30)

                                if not priceMessage.content.isdigit() or priceMessage.content == "0":

                                    await requestEmbedTemplate(ctx,

                                                               "Invalid price amount! Please restart the command!",

                                                               ctx.message.author)


                                else:

                                    c.execute(f''' UPDATE shop SET price = ? WHERE item = ? ''',

                                              (priceMessage.content, f"{itemName.content}"))

                                    conn.commit()

                                    c.execute(f''' UPDATE shophistory SET price = ? WHERE item = ? ''',

                                              (priceMessage.content, f"{itemName.content}"))

                                    conn.commit()

                                    await requestEmbedTemplate(ctx,

                                                               f"Okie! Updated price to `{priceMessage.content}` successfully.",

                                                               ctx.message.author)


                            elif editMessage.content == "stock":

                                await requestEmbedTemplate(ctx, "What would you want the stock to be changed to?",

                                                           ctx.message.author)

                                stockMessage = await self.bot.wait_for('message', check=messageCheck, timeout=30)

                                if not stockMessage.content.isdigit() or int(stockMessage.content) < 0:

                                    await requestEmbedTemplate(ctx,

                                                               "Invalid stock amount! Please restart the command!",

                                                               ctx.message.author)


                                elif stockMessage.content == "0":

                                    c.execute(f''' UPDATE shop SET stock = ? WHERE item = ? ''',

                                              ('Unlimited', f"{itemName.content}"))

                                    conn.commit()

                                    c.execute(f''' UPDATE shophistory SET stock = ? WHERE item = ? ''',

                                              ('Unlimited', f"{itemName.content}"))

                                    conn.commit()

                                    await requestEmbedTemplate(ctx,

                                                               f"Okie! Updated stock to `'Unlimited'` successfully.",

                                                               ctx.message.author)


                                else:

                                    c.execute(f''' UPDATE shop SET stock = ? WHERE item = ? ''',

                                              (stockMessage.content, f"{itemName.content}"))

                                    conn.commit()

                                    c.execute(f''' UPDATE shophistory SET stock = ? WHERE item = ? ''',

                                              (stockMessage.content, f"{itemName.content}"))

                                    conn.commit()

                                    await requestEmbedTemplate(ctx,

                                                               f"Okie! Updated stock to `{stockMessage.content}` successfully.",

                                                               ctx.message.author)


                except asyncio.TimeoutError:

                    await requestEmbedTemplate(ctx,

                                               "HMPH! You took too long to respond. Try again when you're going to respond to me!",

                                               ctx.message.author)


            elif str(reaction.emoji) == "❌":

                await requestEmbedTemplate(ctx, "Item creation / deletion / editing cancelled.",

                                           ctx.message.author)


        except asyncio.TimeoutError:

            await requestEmbedTemplate(ctx,

                                       "HMPH! You took too long to respond. Try again when you're going to respond to me!",

                                       ctx.message.author)


        except Exception as e:

            traceback.print_exc()





def setup(bot):
    bot.add_cog(Merit(bot))
