import praw, re, asyncio, discord
from collections import deque
from cogs.helpers import guild
from common import database, common


class CrackWatch:
    r = None

    # constructor to initialize varialbles
    def __init__(self):
        config = common.getConfig()
        self.r = praw.Reddit(client_id=config['REDDIT']['client.id'], client_secret=config['REDDIT']['client.secret'], user_agent=config['REDDIT']['user.agent'])

    async def cleaner(self, bot):
        db = database.Database()

        masterlog = common.getMasterLog()
        masterlog = bot.get_channel(masterlog)

        await masterlog.send(f"purging old cracks.")

        db.cleanCrackwatch()

        await masterlog.send(f"purged cracks.")

    # get new results
    def getSubreddit(self, limit):
        rsub = self.r.subreddit('CrackWatch')
        res = rsub.new(limit = limit)
        return res

    def crackHead(self, flair):
        if not flair:
            return True

        reject = ['discussion', 'daily', 'humor']
        flag = True
        for bad in reject:
            if bad in flair.lower():
                flag = False
        return flag

    # get latest crack release
    async def run(self, bot):
        masterLogger = common.getMasterLog()
        db = database.Database()

        # r/CrackWatch
        subreddit = self.getSubreddit(30)

        # get latest from database
        service = db.getService("crackwatch")
        if 'latest' not in service:
            service['latest'] = None

        # posting log in masterlog
        await bot.get_channel(masterLogger).send(f"scraped crackwatch.")
        
        # create deque
        posts = deque()

        id = None

        # append data to deque
        for submission in subreddit:
            if not id:
                id = submission.id

            if submission.id == service['latest']:
                break
                
            post = {}
            post['id'] = submission.id
            post['title'] = submission.title
            post['url'] = submission.url
            post['selftext'] = submission.selftext
            post['created'] = common.getTimeFromTimestamp(submission.created)
            if self.crackHead(submission.link_flair_text):
                post['flair'] = submission.link_flair_text
                posts.appendleft(post)

        # go through new submissions
        for i in range(len(posts)):
            if not posts[i]['flair']:
                await bot.get_channel(masterLogger).send(f"**error in cw [no flair]** : check {posts[i]['url']}.")
            else:
                if 'release' in posts[i]['flair'].lower():
                    posts[i]['type'] = 'crack'
                elif "repack" in posts[i]['flair'].lower():
                    posts[i]['type'] = 'repack'
                else:
                    posts[i]['type'] = 'unknown'

                status = db.upsertCrackwatch(post)
                
                if status == 2:
                    # check for release flair
                    if posts[i]['type'] == 'crack':
                        description = posts[i]['selftext']

                        # discord embed description limit
                        if len(posts[i]['selftext']) >= 2048:
                            description = description[:2040]+"\n..."
                        
                        embed = discord.Embed(
                            title=posts[i]['title'],
                            url=posts[i]['url'],
                            description=description
                        )

                        links = re.findall(r"(?:http\:|https\:)?\/\/\S*\.(?:png|jpg)[A-Za-z0-9.\/\-\_\?\=\:]*", description)

                        if len(links) > 0:
                            embed.set_image(url=links[0])
                        elif posts[i]['url'].endswith(".jpg") or posts[i]['url'].endswith(".png"):
                            embed.set_image(url=posts[i]['url'])

                        embed.add_field(
                            name="Time",
                            value=posts[i]['created'],
                            inline=True
                        )
                        
                        # send message
                        channels = guild.getChannels("crackwatch")
                        for channel in channels: 
                            await bot.get_channel(channel["channel_id"]).send(embed=embed)
                            # if logging is enabled post log
                            if "logging" in channel:
                                await bot.get_channel(channel["logging"]).send(f"sent {posts[i]['title']} in {channel['channel_name']}")

                        # sleep for 1 sec
                        await asyncio.sleep(1)

                    # check for repack flair
                    elif posts[i]['type'] == 'repack':
                        embed = discord.Embed(
                            title=posts[i]['title'],
                            url=posts[i]['url'],
                            description=posts[i]['selftext']
                        )

                        if posts[i]['url'].endswith(".jpg") or posts[i]['url'].endswith(".png"):
                            embed.set_image(url=posts[i]['url'])

                        embed.add_field(
                            name="Time",
                            value=posts[i]['created'],
                            inline=True
                        )
                        
                        # send message
                        channels = guild.getChannels("repacknews")
                        for channel in channels: 
                            await bot.get_channel(channel["channel_id"]).send(embed=embed)
                            # if logging is enabled post log
                            if "logging" in channel:
                                await bot.get_channel(channel["logging"]).send(f"sent {posts[i]['title']} in {channel['channel_name']}")

                        # sleep for 1 second
                        await asyncio.sleep(1)

        # update database
        data = {}
        data["name"] = "crackwatch"
        if len(posts) > 0:
            data["lastposted"] = common.getDatetimeIST()
            data["latest"] = id

        db.updateService(data)

        data["name"] = "repacknews"
        db.updateService(data)
