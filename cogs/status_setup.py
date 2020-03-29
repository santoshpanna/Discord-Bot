from discord.ext import commands
from datetime import datetime
from .csgo import server_status
from common import common
from common.database import Database
import requests, humanize
from requests.auth import HTTPDigestAuth
import discord, platform, psutil
from .helpers.helpmaker import Help


class Status(commands.Cog):
    bot = None

    def __init__(self, bot):
        self.bot = bot
        self.masterLog = common.getMasterLog()
        self.groupedCommands = {}
        self.groupedCommands['server'] = {'name': 'server', 'description': 'shows details about server'}
        self.groupedCommands['csgo'] = {'name': 'csgo', 'description': 'shows csgo server status'}
        self.help = Help()
    
    @commands.group(pass_context=True)
    async def status(self, ctx):
        if ctx.invoked_subcommand is None:
            db = Database()

            embed = discord.Embed(
                title='Bot Status'
            )

            counts = db.getCountEstimates()
            status = db.getStatus()

            embed.add_field(name="Bot Name", value="[Shinigami]", inline=False)
            embed.add_field(name="Bot Uptime", value=f"{humanize.naturaldelta(datetime.now() - status['botStartTime'])}", inline=False)
            embed.add_field(name="Current tracked game deals", value=f"{counts['gamedeals']}", inline=False)
            embed.add_field(name="Current tracked game cracks", value=f"{counts['cracks']}", inline=False)
            embed.add_field(name="Current tracked game repacks", value=f"{counts['repacks']}", inline=False)
            embed.add_field(name="Bot Source", value=f"[https://github.com/santoshpanna/Discord-Bot](github.com)", inline=False)

            await ctx.send(embed=embed)

    @status.command()
    async def help(self, ctx):
        await ctx.send(embed=self.help.make(ctx.author.name, 'status', None, self.groupedCommands, None))

    @status.command()
    async def server(self, ctx):
        # subcommand to get the server status
        embed = discord.Embed(
            title = 'Server Information'
        )

        config = common.getConfig()

        url = f"https://cloud.mongodb.com/api/atlas/v1.0/groups/{config['DATABASE']['groupid']}/processes"

        res = requests.get(url, auth=HTTPDigestAuth(config['DATABASE']['publickey'], config['DATABASE']['privatekey']))

        embed.add_field(name="Python Version", value=platform.python_version(), inline=False)
        embed.add_field(name="OS", value=platform.platform(), inline=False)

        embed.add_field(name="Server Uptime", value=f'{humanize.naturaldelta(datetime.now() - datetime.fromtimestamp(psutil.boot_time()))}', inline=False)
        embed.add_field(name="CPU", value=f'{psutil.cpu_percent()}% | Physical [{psutil.cpu_count(logical=False)}] | Logical [{psutil.cpu_count(logical=True)}]', inline=False)
        embed.add_field(name="RAM", value=f'{psutil.virtual_memory().percent}% | {round(psutil.virtual_memory().total / (1024.0 **3))} GB', inline=False)

        api_res = requests.get(config['COMMON']['api.url']).json()
        if api_res['status'] == 1:
            embed.add_field(name="API Server", value='online', inline=False)
        else:
            embed.add_field(name="API Server", value='offline', inline=False)

        if res.status_code != requests.codes.ok:
            embed.add_field(name="DB Hosts Status", value=f"Down", inline=False)
        else:
            res = res.json()
            string = f"{res['totalCount']} | ["
            temp = ""
            for process in res['results'][::-1]:
                temp = temp + f"{process['typeName'].replace('REPLICA_', '')} | "
            # remove "| "
            temp = temp[:-2]
            string = string + temp + ']'
            embed.add_field(name="DB Hosts Running", value=string, inline=False)

        await ctx.send(embed=embed)

    @status.command()
    @commands.is_owner()
    async def set(self, ctx, status: str):
        # subcommand to set the current bot status
        await self.bot.change_presence(status=discord.Status.idle, activity=discord.CustomActivity(name=status))
        await self.bot.get_channel(self.masterLog).send(f"**Changed status**: To {status}")

    @status.command()
    async def csgo(self, ctx):
        # commands for csgo
        # if no sub commands is passed display the current no of searching players and players online instead
        if ctx.message.channel.name == 'lobby' or ctx.message.channel.name == 'csgo':
            await server_status.serverStatus(ctx)
        else:
            await ctx.send("Command not enabled for this channel.")


def setup(bot):
    bot.add_cog(Status(bot))
