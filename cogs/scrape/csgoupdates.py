from bs4 import BeautifulSoup
from datetime import datetime
import requests, discord, asyncio, w3lib.html
from ..helpers import guild
from common import common, database


class CsgoUpdates:
    # csgo update url
    url = "https://blog.counter-strike.net/index.php/category/updates/"

    async def run(self, bot):
        db = database.Database()
        masterLogger = common.getMasterLog()

        # request the page
        req = requests.get(self.url)

        # get service from database
        service = db.getService("csgoupdates")

        if common.getEnvironment() == 'dev':
            # post log in logging channel
            await bot.get_channel(masterLogger).send(f"**Scraped**: CSGO Updates.")
        
        # return variable
        updates = []

        # soupy
        soup = BeautifulSoup(req.content, 'html5lib')

        # post container:
        container = soup.find('div', attrs = {'id': 'post_container'})

        # iterating though each post
        for post in container.findAll('div', attrs = {'class':'inner_post'}):
            posts = {}
            posts['title'] = post.h2.text

            # beautify date
            posts['date'] = post.find('p', attrs={'class':'post_date'}).text[:-5]
            posts['date'] = str(datetime.strptime(posts['date'], "%Y.%m.%d"))[:-9]
            posts['url'] = post.select("a")[0].get('href')

            # patchnotes
            posts['patchnotes'] = []
            for p in post.findAll('p'):
                try:
                    if p.attrs['class']:
                        pass
                except KeyError:
                    # remove html tags
                    posts['patchnotes'].append(str(p).replace("<br/>", "").replace("<p>", "").replace("</p>", ""))

            posts['patchnotes'] = "\n\n".join(posts['patchnotes'])
            posts['patchnotes'] = w3lib.html.remove_tags(posts['patchnotes'])

            posts['id'] = posts['date']
            posts['service_name'] = 'csgoupdates'
            posts['service_id'] = str(service['_id'])
            status = db.upsertPatchnotes(posts)
            if status == common.STATUS.INSERTED:
                updates.append(posts)
            elif status == common.STATUS.REDUNDANT:
                break
            else:
                await bot.get_channel(masterLogger).send(f"**Scrape Error - CSGO Updates**: id = {posts['id']}.")

        # process list in ascending order
        for update in updates[::-1]:
            # discord embed description limit
            if len(update['patchnotes']) >= 2048:
                update['patchnotes'] = update['patchnotes'][:2040] + "\n..."

            # send an embed message
            embed=discord.Embed(
                title=update["title"],
                url=update["url"],
                description=update["patchnotes"]
            )

            embed.add_field(name="Date", value=update["date"], inline=True)
            
            # send message
            channels = guild.getChannels("csgoupdates")
            for channel in channels: 
                await bot.get_channel(channel["channel_id"]).send(embed=embed)
                # if logging is enabled post log
                if "logging" in channel:
                    await bot.get_channel(channel["logging"]).send(f"sent {update['title']} in {channel['channel_name']}")

            # sleep for 1 second
            await asyncio.sleep(1)

        # update database
        data = {}
        data["name"] = "csgoupdates"
        if len(updates) > 0:
            data["lastposted"] = common.getDatetimeIST()
            data["latest"] = updates[0]["date"]

        status = db.upsertService(data)
        if status == common.STATUS.SUCCESS.INSERTED:
            await bot.get_channel(masterLogger).send(f"**Created Service**: {data['name']}.")
        elif status == common.STATUS.FAIL.INSERT:
            await bot.get_channel(masterLogger).send(f"**DB Insert Error - Service**: {data['name']}.")
        elif status == common.STATUS.FAIL.UPDATE:
            await bot.get_channel(masterLogger).send(f"**DB Update Error - Service**: {data['name']}.")
        else:
            pass
   
