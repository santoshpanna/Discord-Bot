import praw, os, discord, requests
from steamstorefront import SteamStoreFront
from datetime import datetime
from collections import deque
from bs4 import BeautifulSoup
from common import common, database
from ..helpers import steam, gamedeals, guild
from ..helpers.gamedeals import isFromAcceptableStore


class GameDeals:
    r = None
    steam = None

    # constructor to initialize varialbles
    def __init__(self):
        config = common.getConfig()
        self.masterLogger = common.getMasterLog()
        self.r = praw.Reddit(client_id=config['REDDIT']['client.id'], client_secret=config['REDDIT']['client.secret'], user_agent=config['REDDIT']['user.agent'])
        self.steam = steam.Steam()
        self.ssf = SteamStoreFront()

    # get new results
    def getSubreddit(self, subreddit, limit):
        rsub = self.r.subreddit(subreddit)
        res = rsub.new(limit=limit)
        return res

    def keyDoesNotExists(self, deq, dict):
        for el in deq:
            if el['url'] == dict['url']:
                return False
        return True

    async def run(self, bot):
        masterLogger = common.getMasterLog()
        db = database.Database()

        # subreddits to fetch
        subreddits = ['gamedeals', 'steamdeals', 'freegamefindings']

        # final post container of non existing and distinct deals
        enriched_post = deque()

        # for each subreddit
        for subreddit in subreddits:
            # get the service record
            service = db.getService(subreddit)
            if 'latest' not in service:
                service['latest'] = None

            # get the latest submissions
            posts = []
            try:
                posts = self.getSubreddit(subreddit, 30)
            except Exception:
                await bot.get_channel(masterLogger).send(f"**Error** : unable to fetch r/{subreddit}")

            # id container
            id = None

            if common.getEnvironment() == 'dev':
                # post log in masterlogger
                await bot.get_channel(masterLogger).send(f"scraped {subreddit}.")

            # iterate through posts
            for post in posts:
                # this is done for getting the first id
                if not id:
                    id = post.id

                # if there are no new post, break
                if post.id == service['latest']:
                    break

                if isFromAcceptableStore(post):
                    deal = {}
                    deal['title'] = post.title
                    deal['id'] = post.id
                    if "reddit.com" in post.url:
                        deal['url'] = gamedeals.getStoreLink(post)
                    else:
                        deal['url'] = gamedeals.removeURI(post.url)
                    deal['created'] = common.getTimeFromTimestamp(post.created)
                    if 'url' in deal and deal['url']:
                        # check if its steam store link
                        if 'steampowered.com' in deal['url']:
                            price = None
                            try:
                                price = self.ssf.getPrice(url=deal['url'])
                            except InvalidArgument as e:
                                if common.getEnvironment() == 'prod' or common.getEnvironment() == 'dev':
                                    await bot.get_channel(masterLogger).send(f"error getting price for {deal['url']} of reddit id {deal['id']}. Arguments passed {e.error}, error type {e.type}.")
                                pass
                            if price:
                                deal['price'] = price['final']
                        if self.keyDoesNotExists(enriched_post, deal):
                            enriched_post.appendleft(deal)

            # update database
            data = {}
            data["name"] = subreddit
            if len(enriched_post) > 0:
                data["lastposted"] = common.getDatetimeIST()
                if id:
                    data["latest"] = id

            status = db.upsertService(data)
            if status == common.STATUS.SUCCESS.INSERTED:
                await bot.get_channel(masterLogger).send(f"**Created Service**: {data['name']}.")
            elif status == common.STATUS.FAIL.INSERT:
                await bot.get_channel(masterLogger).send(f"**DB Insert Error - Service**: {data['name']}.")
            elif status == common.STATUS.FAIL.UPDATE:
                await bot.get_channel(masterLogger).send(f"**DB Update Error - Service**: {data['name']}.")
            else:
                pass

        # send the final deque for posting
        await self.send(enriched_post, bot)

    # steam deals
    async def send(self, posts, bot):
        db = database.Database()

        # go through new submissions
        for post in posts:
            status = db.upsertGameDeal(post)

            # 1 = updated, 2 = created, -1 = error in update/inserting
            channels = guild.getChannels('gamedeals')
            for channel in channels:
                # the deal already exists
                if status == common.STATUS.SUCCESS.UPDATED:
                    # price check for steam games
                    if 'steampowered.com' in post['url']:
                        try:
                            existingDeal = db.getGameDeal(post)
                            new_price = self.ssf.getPrice(url=post['url'])
                            new_price = new_price['final'] if new_price else 9223372036854775806
                                                         
                            if 'price' in existingDeal:
                                old_price = existingDeal['price']
                                # if new price is less than older price post the deal
                                if int(new_price) < int(old_price):
                                    await self.steam.post(bot, channel, post)
                        # can't compare price, so leave the deal
                        except InvalidArgument as e:
                            if common.getEnvironment() == 'prod' or common.getEnvironment() == 'dev':
                                await bot.get_channel(common.getMasterLog()).send(f"error getting price for {post['url']} of reddit id {post['id']}. Arguments passed {e.error}, error type {e.type}.")
                            pass
                    # else:
                    #     await self.steam.post(bot, channel, post)

                # the deal is a new one
                elif status == common.STATUS.SUCCESS.INSERTED:
                    # special handler for steam
                    if 'steampowered.com' in post['url']:
                        await self.steam.post(bot, channel, post)
                    else:
                        await bot.get_channel(channel['channel_id']).send(post['url'])
                        # if logging is enabled post log
                        if 'logging' in channel:
                            await bot.get_channel(channel['logging']).send(f"sent {post['title']} in {channel['channel_name']}")

                # there has been error updating or inserting deal
                else:
                    # log it in master log
                    bot.get_channel(self.masterLogger).send(f"**DB Error**: Failed Updating/Inserting {post['id']}.")
