import requests, re, json
from bs4 import BeautifulSoup
from common.database import Database
from common import common

class Flipkart:
    def __init__(self):
        self.headers = {}
        self.headers['User-Agent'] = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36'
        self.links = ["http://www.flipkart", "https://www.flipkart", "www.flipkart", "http://flipkart", "https://flipkart", "flipkart"]
        self.db = Database()
        self.masterLog = common.getMasterLog()

    def isFlipkartLink(self, url):
        flag = False
        for link in self.links:
            if url.startswith(link):
                return True
        return flag
    
    def cleanURL(self, url):
        if url.find("?pid") > 0:
            return url[:url.find("?pid")]
        return url
    
    def filterPrice(self, json_data):
        currency = None
        price = None
        title = None
        data = None
        try:
            data = json_data['pageDataV4']['page']['pageData']['pageContext']
        except KeyError:
            pass
        finally:
            try:
                currency = u"\u20B9"
                price = data['pricing']['finalPrice']['value']
                title = data['titles']['title']
            except KeyError:
                pass

        return currency, int(price), title

    def getPrice(self, url):
        url = self.cleanURL(url)
        price = {}
        res = requests.get(url, headers=self.headers)
        #print(res.content)
        soup = BeautifulSoup(res.content, 'html5lib')
        script = None
        try:
            script = soup.find('script', attrs={'id' : 'is_script'}).get_text()
        except AttributeError:
            pass
        script = script.replace('window.__INITIAL_STATE__ = ', '')
        script = script[:-2]
        json_data = None
        try:
            json_data = json.loads(script)
        except Exception:
            pass
        finally:
            price['currency'], price['regular'], price['title'] = self.filterPrice(json_data)
            
        return price

    async def insertDeal(self, bot, ctx, url, alert_price):
        # check if link is from flipkart
        if self.isFlipkartLink(url):
            # get member, mapping and service
            url = self.cleanURL(url)
            member = self.db.getMember(ctx)
            deals_by_member = self.db.getPriceAlerts(ctx.author.id)

            service = self.db.getService('flipkart')

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
                        data['service'] = 'flipkart'
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
                        status = self.db.insertPriceDeal(data)

                        if status:
                            await ctx.send(f'{ctx.author.name} - {url} is successfully subscribed for price tracking.')
                        else:
                            await ctx.send(f'{ctx.author.name} - due to technical error we cannot track price right now.')
                            await self.bot.get_channel(self.masterLog).send(f'**error amazon price insert** url = {url}, author = {ctx.author.id}, {ctx.author.name} from {ctx.guild.name} in {ctx.channel.name}')


