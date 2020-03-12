import requests, discord, asyncio, w3lib.html
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from ..helpers import guild
from common import common, database


class DestinyUpdates:
    # destiny update url
    url = "https://www.bungie.net/en/Explore/Category?category=Updates"

    async def run(self, bot):
        db = database.Database()
        masterLogger = common.getMasterLog()

        # destiny updates
        service = db.getService("destinyupdates")
        if 'latest' not in service:
            service['latest'] = None

        # request the page
        req = requests.get(self.url)

        # post log in logging channel
        await bot.get_channel(masterLogger).send(f"scraped destiny 2 updates.")

        # return variable
        updates = []

        # soupy
        soup = BeautifulSoup(req.content, 'html5lib')

        # post container:
        container = soup.find('div', attrs = {'id':'explore-contents'})

        # iterating though each post
        i = 0
        for post in container.findAll('a'):
            # check for max 5 updates
            i = i + 1
            if i >= 4:
                break

            posts = {}
            posts['link'] = post.get('href')
            posts['title'] = post.find('div', {"class":"title"}).text

            # addition request for date and patchnotes
            detail_req = requests.get('https://www.bungie.net/'+posts['link'])
            detail_soup = BeautifulSoup(detail_req.content, 'html5lib')

            # beautify date
            posts['date'] = detail_soup.select("div.metadata")[0].text
            posts['date'] = posts['date'].split("-")[0].strip()
            
            try:
                # the date is older than 1 day
                posts['date'] = str(datetime.strptime(posts['date'], "%b %d, %Y"))[:-9]
            except:
                # convert relative hours to date
                posts['date'] = posts['date'].replace("h", "")
                delta = timedelta(hours=int(posts['date']))
                posts['date'] = str(datetime.strftime((datetime.today() - delta), "%b %d, %Y"))

            posts['patchnotes'] = str(detail_soup.find("div", attrs={"class":"content text-content"}))

            # removing tags
            posts['patchnotes'] = posts['patchnotes'].replace("\t","").replace("\n","")
            posts['patchnotes'] = posts['patchnotes'].replace("<div class=\"content text-content\">","")
            posts['patchnotes'] = posts['patchnotes'].replace("<h2>","\n").replace("</h2>","")
            posts['patchnotes'] = posts['patchnotes'].replace("<h3>","\n").replace("</h3>","")
            posts['patchnotes'] = posts['patchnotes'].replace("<div>","\n").replace("</div>","")
            posts['patchnotes'] = posts['patchnotes'].replace("<ul>","").replace("</ul>","")
            posts['patchnotes'] = posts['patchnotes'].replace("<li>","- ").replace("</li>","\n")
            posts['patchnotes'] = posts['patchnotes'].replace("<b>","").replace("</b>","")
            posts['patchnotes'] = posts['patchnotes'].replace("<u>","").replace("</u>","")
            posts['patchnotes'] = posts['patchnotes'].replace("<br/><br/>","\n").replace("<br/>","")
            posts['patchnotes'] = posts['patchnotes'].replace("<hr/>","")
            posts['patchnotes'] = posts['patchnotes'].replace("<p"," <p")

            posts['patchnotes'] = w3lib.html.remove_tags(posts['patchnotes'])

            # discord embed description limit
            if len(posts['patchnotes']) >= 2048:
                posts['patchnotes'] = posts['patchnotes'][:2040]+"\n..."

            # check if the there are any new updates
            if posts['date'] == service["latest"]:
                break
            else:
                await bot.get_channel(masterLogger).send(f'**from d2** : latest = {service["latest"]} id = {posts["date"]}')
                updates.append(posts)

        # returns list in ascending order
        for update in updates[::-1]:
            # send an embed message
            embed=discord.Embed(
                title=update["title"],
                url="https://www.bungie.net/"+update["link"],
                description=update['patchnotes']
            )
            embed.add_field(name="Date", value=update["date"], inline=True)

            # get all the channels with service enabled
            channels = guild.getChannels("destinyupdates")
            for channel in channels: 
                await bot.get_channel(channel["channel_id"]).send(embed=embed)
                # if logging is enabled post log
                if "logging" in channel:
                    await bot.get_channel(channel["logging"]).send(f"sent {update['title']} in {channel['channel_name']}")
            
            # sleep for 1 second
            await asyncio.sleep(1)

        # update database
        data = {}
        data["name"] = "destinyupdates"
        if len(updates) != 0:
            data["lastposted"] = common.getDatetimeIST()
            data["latest"] = updates[len(updates)-1]["date"]

        db.updateService(data)
