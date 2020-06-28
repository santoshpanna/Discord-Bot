import requests

from discord.ext import tasks, commands
import discord
from .helpers.steam import Steam
from .helpers.helpmaker import Help
from .helpers.guild import getChannelByService
from common.database import Database
from common import common


class Youtube(commands.Cog):
    youtube_api_url = 'https://www.googleapis.com/youtube/v3/search'

    def __init__(self, bot):
        self.bot = bot
        self.help = Help()
        self.db = Database()
        self.config = common.getConfig()
        self.cache = {'live': None, 'videos': None}

    @tasks.loop(minutes=1, count=10)
    async def checkLive(self):
        # get the api key and channel id
        api_key = self.config['YOUTUBE']['api_key']
        channel_id = self.config['YOUTUBE']['channel_id']

        # forming the url to query
        url = self.youtube_api_url + '?part=snippet&channelId=' + channel_id + '&key=' + api_key + '&type=video&order=date&eventType=live'

        # set data to None
        data = None

        try:
            # request the data
            data = requests.get(url).json()
        except Exception as e:
            # TODO - better exception handling

            # stop the job
            # TODO - check impact of cancel vs stop
            self.checkLive.cancel()

        if data and 'items' in data:
            # get the discord channel
            channel = self.bot.get_channel(int(self.config['DISCORD']['live_channel_id']))

            # if there are no live streams
            if len(data['items']) == 0:
                # rudimentary check to confirm its a text channel, not really necessary
                if channel.type.name == 'text':
                    # if channel status is live change to offline
                    if channel.name.startswith('🟢'):
                        await channel.edit(name='live-streams')

                        # stop the job
                        # TODO - check impact of cancel vs stop
                        self.checkLive.cancel()
            else:
                # the cache does not exist, the app restarted or initial start
                if not self.cache['live']:
                    # get the data from database and populate the cache
                    old_cache = self.db.getYoutube('live')

                    # special case, start of service i.e., there is no data in database
                    if not old_cache:
                        # TODO - make this logic better, works for now
                        # this will make the if case false and would directly jump to else part
                        old_cache = {'videoId': None}

                    # check if the current data is equal to data in database
                    # if it is update the cache and do nothing else
                    if old_cache['videoId'] == data['items'][0]['id']['videoId']:
                        self.cache['live'] = old_cache
                    # else old cache is invalid and there is new livestream
                    # update everything
                    else:
                        # we consider the only the first item
                        temp = {}
                        temp['videoId'] = data['items'][0]['id']['videoId']
                        temp['publishTime'] = data['items'][0]['snippet']['publishTime']
                        temp['publishedAt'] = data['items'][0]['snippet']['publishedAt']
                        temp['title'] = data['items'][0]['snippet']['title']
                        temp['description'] = data['items'][0]['snippet']['description']
                        temp['liveBroadcastContent'] = data['items'][0]['snippet']['liveBroadcastContent']
                        temp['image'] = data['items'][0]['snippet']['thumbnails']['high']['url']

                        # update the database and cache
                        err = self.db.setYoutube(temp)
                        self.cache['live'] = temp

                        embed = discord.Embed(
                            title=self.cache['live']['title'],
                            url=f"https://www.youtube.com/watch?v={self.cache['live']['videoId']}",
                            description=self.cache['live']['description']
                        )
                        embed.set_image(url=self.cache['live']['image'])

                        # send the notification
                        await channel.send(
                            '@everyone\nWe are LIVE\n\nCome join in on the fun.\nPlease Like 👍 and share 🔗.\n\n',
                            embed=embed)

                        # change the channel name
                        await channel.edit(name='🟢we-are-live')

                        # stop the job
                        # TODO - check impact of cancel vs stop
                        self.checkLive.cancel()

    def checkUploads(self):
        # get the api key and channel id
        api_key = self.config['YOUTUBE']['api_key']
        channel_id = self.config['YOUTUBE']['channel_id']

        # forming the url to query

        url = self.youtube_api_url + '?part=snippet&channelId=' + channel_id + '&key=' + api_key + '&maxResults=10&order=date&type=video'

        # set data to None
        data = None

        try:
            # request the data
            data = requests.get(url).json()
        except Exception as e:
            # pass
            # TODO - better exception handling
            pass
        pass

    @commands.group(pass_context=True)
    async def ytlive(self, ctx):
        if ctx.invoked_subcommand is None:
            # check the status of job
            if self.checkLive.is_running():
                await ctx.send(f"Job is already running ignoring this request.")
            else:
                # start the jobs
                self.checkLive.start()


def setup(bot):
    bot.add_cog(Youtube(bot))
