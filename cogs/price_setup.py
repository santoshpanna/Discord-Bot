from discord.ext import tasks, commands
import discord, pprint
from .price.amazon import Amazon
from .price.flipkart import Flipkart
from .price.headphonezone import Headphonezone
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
        self.flipkart = Flipkart()
        self.headphonezone = Headphonezone()
        self.groupedCommands = {}
        self.db = Database()
        self.groupedCommands['sub'] = {'name': 'sub', 'arguments': 'url alert_price', 'description': 'adds url for tracking with trigger when current price is lower than alert_price'}
        self.groupedCommands['unsub'] = {'name': 'unsub', 'arguments': 'uuid', 'description': 'unsubscribe to current deal.'}
        self.groupedCommands['update'] = {'name': 'update', 'arguments': 'uuid alert_price', 'description': 'updates current deal with newer alert_price.'}
        self.groupedCommands['cooldown'] = {'name': 'cooldown', 'arguments': 'uuid','description': 'resets the cooldown time so that you get continuous price alerts.'}
        self.groupedCommands['list'] = {'name': 'list', 'description': 'lists all subscribed pricealerts by user.'}
        self.extra = 'Supported stores are amazon, flipkart and headphonezone.'
        self.help = Help()

    def cog_unload(self):
        self.deals.cancel()
        self.cleaner.cancel()

    # todo - implement cleanup routines
    @tasks.loop(hours = 168.0)
    async def cleaner(self): 
        # self.db.dealsCleaner(self.bot)
        # await self.bot.get_channel(self.masterLogger).send(f"cleaned deals.")
        pass

    @commands.group(pass_context=True)
    async def pricetracker(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send(embed=self.help.make(ctx.author.name, 'pricetracker', None, self.groupedCommands, self.extra))

    @pricetracker.command()
    async def help(self, ctx):
        await ctx.send(embed=self.help.make(ctx.author.name, 'pricetracker', None, self.groupedCommands, self.extra))

    @pricetracker.command()
    @commands.is_owner()
    async def clean(self, ctx):
        # self.db.dealsCleaner(self.bot)
        await self.bot.get_channel(self.masterLogger).send(f"force clean deal command by {ctx.author.name}.")

    @pricetracker.command()
    async def sub(self, ctx, url: str, alert: str):
        if self.amazon.isAmazonLink(url):
            await self.amazon.insertDeal(self.bot, ctx, url, alert)
        elif self.flipkart.isFlipkartLink(url):
            await self.flipkart.insertDeal(self.bot, ctx, url, alert)
        elif self.headphonezone.isHeadphonezoneLink(url):
            await self.headphonezone.insertDeal(self.bot, ctx, url, alert)
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
        if status == common.STATUS.SUCCESS:
            await ctx.send(f"{ctx.author.name}, you have successfully un-subscribed from pricealert for **{uuid}**.")
        else:
            await ctx.send(f"{ctx.author.name}, the id is incorrect. Use `!pricetracker list` to view your subscribed pricealerts.")

    @pricetracker.command()
    async def update(self, ctx, uuid: str, price:int):
        data = {}
        data['member_id'] = ctx.author.id
        data['uuid'] = uuid
        data['alert_at'] = price

        status = self.db.updatePriceAlert(data)

        if status == common.STATUS.SUCCESS:
            await ctx.send(f"{ctx.author.name}, **{uuid}** has been successfully updated with alert price **{price}**.")
        elif status == common.STATUS.FAIL.NOT_FOUND:
            await ctx.send(f"{ctx.author.name}, we are unable to update alert price for **{uuid}**.")
        elif status == common.STATUS.FAIL.UPDATE:
            await ctx.send(f"{ctx.author.name}, we cannot find any subscription for **{uuid}**.")

    @pricetracker.command()
    async def cooldown(self, ctx, uuid:str):
        data = {}
        data['member_id'] = ctx.author.id
        data['uuid'] = uuid
        data['alert_at'] = common.getDatetimeIST()

        status = self.db.updatePriceAlert(data)

        if status == common.STATUS.SUCCESS:
            await ctx.send(f"{ctx.author.name}, **{uuid}** cooldown has been reset.")
        elif status == common.STATUS.FAIL.NOT_FOUND:
            await ctx.send(f"{ctx.author.name}, we are unable to reset cooldown for **{uuid}**.")
        elif status == common.STATUS.FAIL.UPDATE:
            await ctx.send(f"{ctx.author.name}, we cannot find any subscription for **{uuid}**.")

    @pricetracker.command()
    async def list(self, ctx):

        alerts = self.db.getPriceAlert(ctx.author.id)

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
        deals = self.db.getPriceAlert(data)
        for deal in deals:   
            self.createRichDeals(all_deals, deal)

        # if count g.t. limit : e.g 1024 >= 1000
        # and count l.t. offset + limit : e.g
        # 1st run : 1024 <= 0 + 1000
        # 2nd run : 1024 <= 1000 + 1000 # false
        count = deals.count()
        while data['limit'] <= count <= (data['offset'] + data['limit']):
            data['offset'] = data['offset'] + data['limit']
            deals = self.db.getPriceAlert(data)
            for deal in deals:   
                self.createRichDeals(all_deals, deal)

        for key in all_deals:
            price = None
            flag = False
            # check for service name
            if all_deals[key]['service'] == 'amazon':
                price = self.amazon.getPrice(key)
                if price and isinstance(price, dict):
                    price['current'] = self.amazon.getMin(price)

            elif all_deals[key]['service'] == 'flipkart':
                price = self.flipkart.getPrice(key)
                if price and isinstance(price, dict):
                    price['current'] = price['regular']

            elif all_deals[key]['service'] == 'headphonezone':
                price = self.headphonezone.getPrice(key)
                if price and isinstance(price, dict):
                    price['current'] = price['regular']

            # if price exists i.e., product is not out of stock
            if 'current' in price and price['current']:
                # iterate the members
                for member in all_deals[key]['members']:
                    if member['currency'] == u"\u00A4":
                        update_payload = {}
                        update_payload['_id'] = all_deals[key]['_id']
                        update_payload['member_id'] = member['id']
                        update_payload['uuid'] = member['uuid']
                        update_payload['currency'] = price['currency']
                        self.db.updatePriceAlert(update_payload)
                    # if price is lower than alert price or equal to alert price, send a private message
                    if price['current'] < member['alert_at'] and common.getDatetimeIST() >= member['cooldown']:
                        self.bot.send_message(member['id'], f'Price for **{price["title"]}** has dropped and is now **{price["currency"]} {price["current"]}.00**.\nPlease update alert price by command `!pricetracker update {member["uuid"]} <new alert price>` or,\nDelete this deal by `!pricetracker delete {member["uuid"]}`\nFurther alerts for this deal is supressed for next 12 hours.\nIf you want to continue to receive in price alerts in cooldown period, issue command by `!pricetracker cooldown {member["uuid"]}`.')
                        # db update flag
                        flag = True
            if flag:
                status = self.db.updatePriceAlerts(key, price['current'])
                if status == common.STATUS.FAIL.UPDATE:
                    await self.bot.get_channel(self.masterLogger).send(f"**Error - Price Alert** : Bulk update error for url = {key} and price = {price['current']}.")


def setup(bot):
    bot.add_cog(Reddit(bot))
