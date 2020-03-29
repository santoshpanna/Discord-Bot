import requests, re, json
from bs4 import BeautifulSoup
from common.database import Database
from common import common
from w3lib.url import url_query_parameter

class Headphonezone:
    def __init__(self):
        self.headers = {}
        self.headers['User-Agent'] = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36'
        self.links = ["http://www.headphonezone", "https://www.headphonezone", "www.headphonezone", "http://headphonezone", "https://headphonezone", "headphonezone"]
        self.db = Database()
        self.masterLog = common.getMasterLog()
        
    def isHeadphonezoneLink(self, url):
        flag = False
        for link in self.links:
            if url.startswith(link):
                return True
        return flag
    
    def cleanURL(self, url):
        if url.find("?pid") > 0:
            return url[:url.find("?pid")]
        return url
    
    def filterPrice(self, data, variant):
        currency = None
        price = None
        title = None
        # 1 less than int max
        minm = 9223372036854775806
        for offer in data['offers']:
            if 'availability' in offer and ['availability'] != 'https://schema.org/OutOfStock':
                if 'url' in offer and variant and offer['url'].endswith(str(variant)):
                    currency = u"\u20B9"
                    price = re.sub(r'[^\d].+', '', offer['price'])
                    title = offer['sku']
                    break
                else:
                    temp = int(re.sub(r'[^\d].+', '', offer['price']))
                    try:
                        if minm > temp:
                            currency = u"\u20B9"
                            price = temp
                            title = offer['sku']
                            minm = price
                    except KeyError:
                        pass
                    
        return currency, int(price), title

    def getPrice(self, url):
        # check if its flipkart link
        if self.isHeadphonezoneLink(url):
            # remove references
            # this is done so that we save only the product url in database
            #url = self.cleanURL(url)
            price = {}
            res = requests.get(url, headers=self.headers)
            #print(res.content)
            soup = BeautifulSoup(res.content, 'html5lib')
            scripts = None
            try:
                scripts = soup.findAll('script', type='application/ld+json')
                for script in scripts:
                    script = json.loads(script.text)
                    if 'offers' in script:
                        scripts = script
                if not isinstance(scripts, dict):
                    scripts = None
            except AttributeError:
                return None
            finally:
                price['currency'], price['regular'], price['title'] = self.filterPrice(scripts, url_query_parameter(url, 'variant'))
            
            return price

    async def insertDeal(self, bot, ctx, url, alert_price):
        # check if link is from flipkart
        if self.isHeadphonezoneLink(url):
            # get member, mapping and service
            #url = self.cleanURL(url)
            member = self.db.getMember(ctx)
            deals_by_member = self.db.getPriceAlert(ctx.author.id)

            service = self.db.getService('headphonezone')

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
                            alert_price = alert_price.remove("%", "").remove(" ", "")
                            alertAt = price['regular'] - (price['regular'] / 100) * int(alert_price)
                            alertAt = int(alertAt)
                    elif alert_price.isnumeric():
                        alertAt = int(alert_price)
                    else:
                        await ctx.send(f'{ctx.author.name} alertprice is invalid, please check and re-issue the command.')

                    if alertAt:
                        # prepare dictionary for insertion
                        data = {}
                        data['member_id'] = member['id']
                        data['service'] = 'headphonezone'
                        data['service_id'] = str(service['_id'])
                        data['url'] = url
                        data['uuid'] = common.getUID(ctx.author.id)
                        data['alert_at'] = int(alert_price)
                        # u"\u00A4" is symbol for unknow currency
                        if not price['currency']:
                            data['currency'] = u"\u00A4"
                        else:
                            data['title'] = price['title']
                            data['currency'] = price['currency']
                        status = self.db.insertPriceAlert(data)

                        if status == common.STATUS.SUCCESS:
                            await ctx.send(f'{ctx.author.name} - {url} is successfully subscribed for price tracking.')
                        elif status == common.STATUS.FAIL.DUPLICATE:
                            await ctx.send(f'{ctx.author.name} - {url} is already subscribed for price tracking.')
                        else:
                            await ctx.send(f'{ctx.author.name} - due to technical error we cannot track price right now.')
                            await bot.get_channel(self.masterLog).send(f'**error flipkart price insert** url = {url}, author = {ctx.author.id}, {ctx.author.name} from {ctx.guild.name} in {ctx.channel.name}')
