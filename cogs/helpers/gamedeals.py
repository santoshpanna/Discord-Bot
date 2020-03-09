import re
from common import database, common

# acceptable store list
# TODO - shift to database
stores = ['steampowered.com', 'humblebundle.com', 'epicgames.com', 'reddit.com']
steamlinks = ('steampowered.com/app', 'steampowered.com/bundle', 'steampowered.com/sub')


# removes uri
def removeURI(url):
    position = url.find('?')
    if position > 0:
        url = url[:position]
    if url.endswith('/'):
        return url[:-1]
    return url


def isNotSteamLink(url):
    flag = True

    count = url.count("http")

    if count > 1:
        url = url[url.rfind("http"):]

    for steam in steamlinks:
        if steam in url:
            flag = False

    return flag


# checks if post is from acceptable store
def isFromAcceptableStore(submission):
    for store in stores:
        if isinstance(submission, str):
            if store in submission:
                if 'steampowered.com' in submission and isNotSteamLink(submission):
                    return False
                return True
        else:
            if store in submission.url:
                if 'steampowered.com' in submission.url and isNotSteamLink(submission.url):
                    return False
                return True
    return False


# get store link from subtext
def getStoreLink(submission):
    links = re.findall(r'https?://[^\s<>"]+|www\.[^\s<>"]+', submission.selftext)

    for link in links:
        if isFromAcceptableStore(link):
            return removeURI(link)


async def cleaner(bot):
    db = database.Database()
    masterlog = common.getMasterLog()
    masterlog = bot.get_channel(masterlog)

    await masterlog.send(f"purging old deals from gamedeals.")

    db.cleanDeals()

    await masterlog.send(f"purged gamedeals.")
