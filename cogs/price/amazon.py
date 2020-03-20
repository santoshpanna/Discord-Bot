import requests, re
from bs4 import BeautifulSoup
from common.database import Database
from common import common


class Amazon:
    def __init__(self):
        self.headers = {}
        self.headers['User-Agent'] = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36'
        self.links = ['http://www.amazon', 'https://www.amazon', 'www.amazon', 'http://amazon', 'https://amazon', 'amazon']
        self.db = Database()
        self.masterLog = common.getMasterLog()

    def isAmazonLink(self, url):
        flag = False
        for link in self.links:
            if url.startswith(link):
                return True
        return flag

    def cleanURL(self, url):
        if url.find('/ref') > 0:
            return url[:url.find('/ref')]
        return url

    def filterPrice(self, price):
        price = price.get_text()
        currency = price[0]
        price = re.sub(r'[^\d\.]+', '', price)
        price = price.split(".")[0]
        return currency, int(price)

    def getPrice(self, url):
        url = self.cleanURL(url)

        price = {}
        res = requests.get(url, headers=self.headers)
        soup = BeautifulSoup(res.content, 'html5lib')

        price['title'] = soup.find(id="productTitle").get_text().strip()

        regular_price = soup.find(id="priceblock_ourprice")
        # product is out of stock
        if regular_price:
            price['currency'], price['regular'] = self.filterPrice(regular_price)
        deal_price = soup.find(id="priceblock_dealprice")
        # lightning deal is going on
        if deal_price:
            price['currency'], price['deal'] = self.filterPrice(deal_price)

        if deal_price and not regular_price:
                price['regular'] = price['deal']

        return price

    def getMin(self, price):
        if not price:
            return None

        if 'deal' in price:
            if price['deal'] < price['regular']:
                return price['deal']
        return price['regular']

    async def insertDeal(self, bot, ctx, url, alert_price):
        # check if link is amazon
        if self.isAmazonLink(url):
            # get member, mapping and service
            url = self.cleanURL(url)
            member = self.db.getMember(ctx)
            deals_by_member = self.db.getPriceAlerts(ctx.author.id)

            service = self.db.getService('amazon')

            if deals_by_member.count() >= member['priceTrackerLimit']:
                await ctx.send(f'{ctx.author.name} you have maxed out your tracking limit. Delete one or more of your previous tracking. `!pricetracker help`')
            else:
                # check if member is already subscribed to service for this url
                flag = False
                for mapping in deals_by_member:
                    if url == mapping['url']:
                        flag = True

                # member is already subscribed
                if flag:
                    await ctx.send(f"{ctx.author.name} you already subscribed to price alert for this url.")
                else:
                    alertAt = None
                    price = self.getPrice(url)

                    if alert_price.endswith('%'):
                        if price:
                            min_price = self.getMin(price)

                            alert_price = alert_price.remove("%", "").remove(" ", "")

                            if price:
                                alertAt = min_price - (min_price / 100) * int(alert_price)
                                alertAt = int(alertAt)
                    elif alert_price.isnumeric():
                        alertAt = int(alert_price)
                    else:
                        await ctx.send(f'{ctx.author.name} alertprice is invalid, please check and re-issue the command.')

                    if alertAt:
                        data = {}
                        data['member_id'] = member['id']
                        data['service'] = 'amazon'
                        data['service_id'] = str(service['_id'])
                        data['url'] = url
                        data['uuid'] = common.getUID(ctx.author.id)
                        data['alert_at'] = int(alert_price)
                        # u"\u00A4" is symbol for unknow currency
                        if not price:
                            data['currency'] = u"\u00A4"
                        else:
                            data['title'] = price['title']
                            data['currency'] = price['currency']
                        status = self.db.insertPriceDeal(data)

                        if status:
                            await ctx.send(f'{ctx.author.name} - {url} is successfully subscribed for price tracking.')
                        else:
                            await ctx.send(f'{ctx.author.name} - due to technical error we cannot track price right now.')
                            await self.bot.get_channel(self.masterLog).send(f'**error amazon price insert** url = {url}, author = {ctx.author.id}, {ctx.author.name} from {ctx.guild.name} in {ctx.channel.name}')

