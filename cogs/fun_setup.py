from discord.ext import commands
from .helpers.helpmaker import Help
from common.database import Database
from .core_setup import Core
from common.common import getServiceList
from random import seed, randint
import time


class Fun(commands.Cog):
    steam_api_key = None

    def __init__(self, bot):
        self.bot = bot
        self.directCommands = {}
        self.directCommands['slap'] = {'name': 'slap', 'arguments': 'person name', 'description': 'slaps the person'}
        self.directCommands['roll'] = {'name': 'roll', 'description': 'rolls a number between 1-8'}
        self.help = Help()

    @commands.group(pass_context=True)
    async def fun(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send(embed=self.help.make(ctx.author.name, 'fun', self.directCommands, None))

    @fun.command()
    async def help(self, ctx):
        await ctx.send(embed=self.help.make(ctx.author.name, 'fun', self.directCommands, None))

    @commands.command()
    async def slap(self, ctx):
        await ctx.send(f"{ctx.author.name} slaps {ctx.author.name}.")

    @commands.command()
    async def slap(self, ctx, name: str):
        slaps_with = ['a stale fish', 'a fish', 'cookies', 'a barrel', 'booze', 'vodka', 'a gaint dildo', 'a dildo']
        seed(time.time())
        await ctx.send(f"**{ctx.author.name}** slaps **{name}** with ***{slaps_with[randint(0, len(slaps_with)-1)]}***.")

    @commands.command()
    async def roll(self, ctx):
        seed(time.time())
        await ctx.send(f"**{ctx.author.name}** rolled ***{randint(1,9)}***")


def setup(bot):
    bot.add_cog(Fun(bot))
