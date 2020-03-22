from discord.ext import commands
from datetime import datetime
from .csgo import server_status
from common import common
import requests
from .helpers.helpmaker import Help
from .helpers import gamedeals
from .reddit.crackwatch import CrackWatch


class Cleaner(commands.Cog):
    bot = None

    def __init__(self, bot):
        self.bot = bot
        self.masterLog = common.getMasterLog()
        self.groupedCommands = {}
        self.groupedCommands['deals'] = {'name': 'deals', 'description': 'force purges old deals'}
        self.groupedCommands['cracks'] = {'name': 'cracks', 'description': 'force purges old cracks'}
        self.groupedCommands['prices'] = {'name': 'prices', 'description': 'force purges old price trackers'}
        self.help = Help()
    
    @commands.group(pass_context=True)
    @commands.is_owner()
    async def clean(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send(embed=self.help.make(ctx.author.name, 'clean', None, self.groupedCommands, None))

    @clean.command()
    @commands.is_owner()
    async def help(self, ctx):
        await ctx.send(embed=self.help.make(ctx.author.name, 'clean', None, self.groupedCommands, None))

    @clean.command()
    @commands.is_owner()
    async def deals(self, ctx):
        await gamedeals.cleaner(self.bot)

    @clean.command()
    @commands.is_owner()
    async def cracks(self, ctx):
        cw = CrackWatch()
        await cw.cleaner(self.bot)

    @clean.command()
    @commands.is_owner()
    async def prices(self, ctx):
        await ctx.send("Not implemented.")


def setup(bot):
    bot.add_cog(Cleaner(bot))
