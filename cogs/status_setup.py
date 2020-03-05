from discord.ext import commands
from datetime import datetime
from .csgo import server_status
from common import common
import requests
from requests.auth import HTTPDigestAuth
import discord, platform, psutil


class Status(commands.Cog):
    bot = None

    def __init__(self, bot):
        self.bot = bot
        config = common.getConfig()
        self.masterLog = int(config['COMMON']['logging'])
    
    @commands.group(pass_context=True)
    async def status(self, ctx):
        """
            command to get or set the varius statues, depeneding on the subcommand
        """
        if ctx.invoked_subcommand is None:
            await ctx.send(f'Hello {ctx.author}.')

    @status.command(pass_context=True)
    async def server(self, ctx):
        """
            subcommand to get the server status
        """
        embed = discord.Embed(
            title = 'Server Information'
        )

        config = common.getConfig()

        url = f"https://cloud.mongodb.com/api/atlas/v1.0/groups/{config['DATABASE']['groupid']}/processes"

        res = requests.get(url, auth=HTTPDigestAuth(config['DATABASE']['publickey'], config['DATABASE']['privatekey']))

        embed.add_field(name="Python Version", value=platform.python_version(), inline=False)
        embed.add_field(name="OS", value=platform.platform(), inline=False)

        bt = datetime.now() - datetime.fromtimestamp(psutil.boot_time())
        hours, remainder = divmod(bt.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)

        embed.add_field(name="Uptime", value=f'{int(hours)} hours, {int(minutes)} mins, {int(seconds)} seconds', inline=False)
        embed.add_field(name="CPU", value=f'{psutil.cpu_percent()}% | Physical [{psutil.cpu_count(logical=False)}] | Logical [{psutil.cpu_count(logical=True)}]', inline=False)
        embed.add_field(name="RAM", value=f'{psutil.virtual_memory().percent}% | {round(psutil.virtual_memory().total / (1024.0 **3))} GB', inline=False)
        if res.status_code != requests.codes.ok:
            embed.add_field(name="DB Hosts Status", value=f"Down", inline=False)
        else:
            res = res.json()
            string = f"{res['totalCount']} | ["
            for process in res['results'][::-1]:
                temp = string + f"{process['typeName'].replace('REPLICA_', '')} | "
            # remove "| "
            temp = temp[:-2]
            string = string + temp + ']'
            embed.add_field(name="DB Hosts Running", value=string, inline=False)

        await ctx.send(embed=embed)

    @status.command(pass_context=True)
    @commands.is_owner()
    async def set(self, ctx, status: str):
        """
            subcommand to set the current bot status
        """
        await self.bot.change_presence(status=discord.Status.idle, activity=discord.CustomActivity(name=status))
        await self.bot.get_channel(self.masterLog).send(f"changed status to {status}")

    @status.command(pass_context=True)
    async def csgo(self, ctx):
        """
            commands for csgo
            if no sub commands is passed display the current no of searching players and players online instead
        """
        if ctx.message.channel.name == 'lobby' or ctx.message.channel.name == 'csgo':
            await server_status.serverStatus(ctx)
        else:
            await ctx.send("Command not enabled for this channel.")


def setup(bot):
    bot.add_cog(Status(bot))
