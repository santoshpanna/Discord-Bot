from discord.ext import tasks, commands
import discord, pprint
from .price.amazon import Amazon
from .helpers.helpmaker import Help
from .helpers import guild
from common.database import Database
from common import common


class Reddit(commands.Cog):
    bot = None

    def __init__(self, bot):
        self.bot = bot
        self.deals.start()
        self.cleaner.start()
        self.masterLogger = common.getMasterLog()
        self.amazon = Amazon()
        self.groupedCommands = {}
        self.db = Database()
        self.groupedCommands['sub'] = {'name': 'sub', 'arguments': 'url alert_price', 'description': 'adds url for tracking with trigger when current price is lower than alert_price'}
        self.groupedCommands['unsub'] = {'name': 'unsub', 'arguments': 'uuid', 'description': 'unsubscribe to current deal.'}
        self.groupedCommands['update'] = {'name': 'update', 'arguments': 'uuid alert_price', 'description': 'updates current deal with newer alert_price.'}
        self.groupedCommands['cooldown'] = {'name': 'cooldown', 'arguments': 'uuid','description': 'resets the cooldown time so that you get continuous price alerts.'}
        self.groupedCommands['list'] = {'name': 'list', 'description': 'lists all subscribed pricealerts by user.'}
        self.help = Help()

    def cog_unload(self):
        self.deals.cancel()
        self.cleaner.cancel()

    # 1 month, like bots gonna run continuously for 1 month straight
    @tasks.loop(hours = 168.0)
    async def cleaner(self): 
        # self.db.dealsCleaner(self.bot)
        await self.bot.get_channel(self.masterLogger).send(f"cleaned deals.")

    @commands.group(pass_context=True)
    async def pricetracker(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send(embed=self.help.make(ctx.author.name, 'pricetracker', None, self.groupedCommands))

    @pricetracker.command()
    async def help(self, ctx):
        await ctx.send(embed=self.help.make(ctx.author.name, 'pricetracker', None, self.groupedCommands))

    @pricetracker.command()
    @commands.is_owner()
    async def clean(self, ctx):
        # self.db.dealsCleaner(self.bot)
        await self.bot.get_channel(self.masterLogger).send(f"force clean deal command by {ctx.author.name}.")

    @pricetracker.command()
    async def sub(self, ctx, url: str, alert: str):
        if self.amazon.isAmazonLink(url):
            await self.amazon.insertDeal(self.bot, ctx, url, alert)
        else:
            if url.strip() == "":
                await ctx.send("f{ctx.author.name}, url is empty.")
            elif alert.strip() == "":
                await ctx.send(f"{ctx.author.name}, alert price is empty.")
            elif url.strip() == "" and alert.strip() == "":
                await ctx.send(f"{ctx.author.name}, url and alert price are empty.")
            else:
                await ctx.send(f"{ctx.author.name}, something went wrong.")

    @pricetracker.command()
    async def unsub(self, ctx, uuid:str):
        data = {}
        data['member_id'] = ctx.author.id
        data['uuid'] = uuid
        status = self.db.deletePriceAlert(data)
        if status:
            await ctx.send(f"{ctx.author.name}, you have successfully un-subscribed from pricealert for **{uuid}**.")
        else:
            await ctx.send(f"{ctx.author.name}, the id is incorrect. Use `!pricetracker list` to view your subscribed pricealerts.")

    @pricetracker.command()
    async def update(self, ctx, uuid: str, price:int):
        data = {}
        data['member_id'] = ctx.author.id
        data['uuid'] = uuid
        data['alert_at'] = price

        status = self.db.updateAlertPrice(data)

        if status == 1:
            await ctx.send(f"{ctx.author.name}, **{uuid}** has been successfully updated with alert price **{price}**.")
        elif status == 0:
            await ctx.send(f"{ctx.author.name}, we are unable to update alert price for **{uuid}**.")
        elif status == -1:
            await ctx.send(f"{ctx.author.name}, we cannot find any subscription for **{uuid}**.")


    @pricetracker.command()
    async def cooldown(self, ctx, uuid:str):
        data = {}
        data['member_id'] = ctx.author.id
        data['uuid'] = uuid

        status = self.db.updatePriceCooldown(data)

        if status == 1:
            await ctx.send(f"{ctx.author.name}, **{uuid}** cooldown has been reset.")
        elif status == 0:
            await ctx.send(f"{ctx.author.name}, we are unable to reset cooldown for **{uuid}**.")
        elif status == -1:
            await ctx.send(f"{ctx.author.name}, we cannot find any subscription for **{uuid}**.")

    @pricetracker.command()
    async def list(self, ctx):

        alerts = self.db.getPriceAlerts(ctx.author.id)

        if alerts:
            description = f'Your current subscribed deals\n\n'
            description = description + "**uuid** - link - alert_price\n"
            for alert in alerts:
                description = description + f'**{alert["uuid"]}** : {alert["url"]} - {alert["currency"]} {alert["alert_at"]}\n'
            embed = discord.Embed(title=f"{ctx.author.name} deals", description=description)
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"{ctx.author.name} you have no active price alert subscription.")


    def createRichDeals(self, deals, deal):
        # check if url already exist in dictionary
        if deal['url'] not in deals:
            # make temporary dictionary
            temp = {}
            temp['_id'] = deal["_id"]
            temp['title'] = deal['title']

            # make member dictionary
            temp['members'] = []
            member = {}
            member['id'] = deal['member_id']
            member['alert_at'] = deal['alert_at']
            member['currency'] = deal['currency']
            member['uuid'] = deal['uuid']
            member['cooldown'] = deal['cooldown']

            temp['members'].append(member)
            temp['service'] = deal['service']
            temp['service_id'] = deal['service_id']

            # add temporary dictionary to main dictionary with key being the url
            deals[deal['url']] = temp
        # key already exists
        else:
            # add member to existing dictionary
            member = {}
            member['id'] = deal['member_id']
            member['alert_at'] = deal['alert_at']
            member['uuid'] = deal['uuid']
            deals[deal['url']]['members'].append(member)

    @tasks.loop(hours = 1.0)
    async def deals(self):
        # limit and offset of paginated query
        data = {}
        data['limit'] = 1000
        data['offset'] = 0

        # all deals container
        all_deals = {}

        # first query to get the count and initial 1000 deals
        deals = self.db.getAllPriceDeals(data)
        for deal in deals:   
            self.createRichDeals(all_deals, deal)

        # if count g.t. limit : e.g 1024 >= 1000
        # and count l.t. offset + limit : e.g
        # 1st run : 1024 <= 0 + 1000
        # 2nd run : 1024 <= 1000 + 1000 # false
        count = deals.count()
        while count >= data['limit'] and count <= (data['offset'] + data['limit']):
            data['offset'] = data['offset'] + data['limit']
            deals = self.db.getAllPriceDeals(data)
            for deal in deals:   
                self.createRichDeals(all_deals, deal)

        for key in all_deals:
            price = None
            min_price = None
            flag = False
            # check for service name
            if all_deals[key]['service'] == 'amazon':
                # get current price
                price = self.amazon.getPrice(key)
                min_price = self.amazon.getMin(price)

            # if price exists i.e., product is not out of stock
            if min_price:
                # iterate the members
                for member in all_deals[key]['members']:
                    if member['currency'] == u"\u00A4":
                        self.db.updateAlertCurrency(member, price['currency'])
                    # if price is lower than alert price or equal to alert price, send a private message
                    if min_price < member['alert_at'] and common.getDatetimeIST() >= member['cooldown']:
                        self.bot.send_message(member['id'], f'Price for **{price["title"]}** has dropped and is now **{price["currency"]} {min_price}.00**.\nPlease update alert price by command `!pricetracker update {member["uuid"]} <new alert price>` or,\nDelete this deal by `!pricetracker delete {member["uuid"]}`\nFurther alerts for this deal is supressed for next 12 hours.\nIf you want to continue to receive in price alerts in cooldown period, issue command by `!pricetracker cooldown {member["uuid"]}`.')
                        # db update flag
                        flag = True
            if flag:
                self.db.updatePrice(key, all_deals[key]['members'], min_price)

def setup(bot):
    bot.add_cog(Reddit(bot))
