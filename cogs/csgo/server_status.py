import requests, discord
from datetime import datetime
from common import common


async def serverStatus(ctx):
    # api url to query data

    config = common.getConfig()

    url = 'https://api.steampowered.com/ICSGOServers_730/GetGameServersStatus/v1/?key='+config['STEAM']['API_KEY']

    # request the data
    res = requests.get(url).json()

    # getting selected data
    embed = discord.Embed(
        title="CSGO SERVER STATUS",
        # steam url's doesn't work
        #url="steam://rungameid/730",
        #description="[Run Game](steam://rungameid/730)"
        )

    #embed.set_image(url='http://media.steampowered.com/apps/csgo/blog/images/wallpaper_nologo.jpg')

    embed.add_field(name="Load", value=res['result']['datacenters']['India']['load'].title(), inline=True)
    embed.add_field(name="Online Players", value=f"{res['result']['matchmaking']['online_players']:,}", inline=True)
    embed.add_field(name="Online Servers", value=f"{res['result']['matchmaking']['online_servers']:,}", inline=True)
    embed.add_field(name="Players Searching", value=f"{res['result']['matchmaking']['searching_players']:,}", inline=True)
    embed.add_field(name="Average Search Time", value=res['result']['matchmaking']['search_seconds_avg'], inline=True)

    embed.set_footer(text=datetime.today().strftime("%Y-%m-%d %H:%M:%S"))

    await ctx.send(embed=embed)
