from steamstorefront import SteamStoreFront
from common.database import Database
from common import common
import discord, time, asyncio, steam
from datetime import datetime


class Steam:

    async def post(self, bot, channel, kwargs):
        obj = None
        category = ''

        if 'url' in kwargs:
            valid = ('https://store.steampowered.com', 'store.steampowered.com')
            if kwargs['url'].startswith(valid):
                category = category = str(kwargs['url'].split("/")[3])
                obj = SteamStoreFront(url=kwargs['url'])
        elif 'name' in kwargs:
            category = 'app'
            obj = SteamStoreFront(name=kwargs['name'])
        elif 'appid' in kwargs:
            if 'category' in kwargs:
                category = kwargs['category']
                obj = SteamStoreFront(appid=kwargs['appid'], category=kwargs['category'])
            obj = SteamStoreFront(appid=kwargs['appid'])

        if 'force' not in kwargs:
            if category == 'app':
                if obj.getRatings()[0] <= 50.0:
                    obj = None

        if obj:
            description = ''

            # setting description
            if category == 'app':
                description = obj.getDescription(short=True)
            elif category == 'sub':
                items = obj.getApps()
                if items:
                    for item in items:
                        description = description + "[{}]({})\n".format(item["name"], 'https://store.steampowered.com/app/'+str(item['id']))
            else:
                items = obj.getPackageItem()
                if items:
                    for item in items:
                        description = description + "[{}]({})".format(item["name"], item['app_link'])


            # discord embed description limit
            if description and len(description) >= 2048:
                description = description[:2040]+"\n..."

            # initial embed
            embed=discord.Embed(
                title=obj.getName(),
                url=obj.getLink(),
                description=description
            )

            # additional embeds
            # header image
            embed.set_image(url=obj.getHeaderImage())

            if category == 'app':
                # adding price
                price_dict = obj.getPrice(currency='in')
                if price_dict:
                    price = "{}% [{} -> {}]".format(price_dict['discount_percent'], price_dict['initial_formatted'], price_dict['final_formatted'])
                    embed.add_field(name="Price", value=price, inline=True)

                # adding release date
                if not obj.getReleaseDate()["coming_soon"]:
                    date = obj.getReleaseDate()["date"]
                else:
                    date = "Coming soon"
                embed.add_field(name="Release Date", value=date, inline=True)

            elif category == 'sub':
                # adding price
                rupee = u"\u20B9"
                price_dict = obj.getPrice(currency='in')
                if price_dict:
                    price = "{}% [{}{}.00 -> {}{}.00]".format(price_dict['discount_percent'], rupee, str(price_dict['initial'])[:-2], rupee, str(price_dict['final'])[:-2])
                    embed.add_field(name="Price", value=price, inline=True)

                # adding release date
                if not obj.getReleaseDate()["coming_soon"]:
                    date = obj.getReleaseDate()["date"]
                else:
                    date = "Coming soon"
                embed.add_field(name="Release Date", value=date, inline=True)
            else:
                # adding price
                price_dict = obj.getPrice()
                if price_dict:
                    price = "{}% [{} -> {}]".format(price_dict['discount_percent'], price_dict['initial_formatted'], price_dict['final_formatted'])
                    embed.add_field(name="Price", value=price, inline=True)

            embed.set_footer(text=str(datetime.fromtimestamp(time.time()).strftime("%Y-%m-%d %H:%M:%S")))

            # send the message
            await bot.get_channel(channel["channel_id"]).send(embed=embed)
            if "logging" in channel:
                await bot.get_channel(channel["logging"]).send(f"sent {obj.getName()} in {channel['channel_name']}")

            # sleep for 1 sec
            await asyncio.sleep(1)

    def getPrice(self, url):
        app = SteamStoreFront(url=url)
        return app.getPrice()

    async def register(self, bot, ctx, username):
        # database
        db = Database()

        obj = None
        # getting the steam id from provided username
        # if username provided is profile link
        if username.startswith('https://steamcommunity.com/'):
            obj = steam.steamid.from_url(username)
        elif username.isnumeric():
            obj = steam.steamid.SteamID(username)
        else:
            profile_link = "https://steamcommunity.com/id/"+username
            obj = steam.steamid.from_url(profile_link)

        # the provided link was invalid
        if obj.type != steam.steamid.EType.Individual:
            await ctx.send(f"{ctx.message.author} the link you provided is invalid.")
        else:
            # continue with registration process
            # the profile is not public
            # doesn't provide a major risk but we can't get certain data, so we suggest and move on
            if obj.universe != obj.steam.steamid.EUniverse.Public:
                await ctx.send(f"{ctx.message.author} your profile is not public, this might cause some problem we suggest you set your profile to public.")

            status = db.insertUserSteam('steam', obj)
            if status == common.STATUS.FAIL.INSERT:
                await ctx.send(f"{ctx.message.author}, registration unsuccessful. This is internal error.")
                bot.get_channel(common.getMasterLog()).send(f"**DB Insert Error**: Unable to insert csgo user {username} requested from user {ctx.message.author}.")
            elif status == common.STATUS.SUCCESS:
                await ctx.send(f"{ctx.message.author}, registration successful.")
            elif status == common.STATUS.FAIL.DUPLICATE:
                await ctx.send(f"{ctx.message.author}, you are already registered for this service.")
