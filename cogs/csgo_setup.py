from discord.ext import commands
from .csgo import server_status
from .helpers.steam import Steam
from common.database import Database
from .helpers.helpmaker import Help
from common import common

class CSGO(commands.Cog):
    steam_api_key = None

    def __init__(self, bot):
        self.bot = bot
        self.masterLog = common.getMasterLog()
        self.directCommands = {}
        self.directCommands['register'] = {'name': 'register', 'arguments': 'profile link or id', 'description': 'registers profile for steam services.'}
        self.help = Help()

    @commands.group(pass_context=True)
    async def csgo(self, ctx):
        if ctx.invoked_subcommand is None:
            if ctx.message.channel.name == 'lobby' or ctx.message.channel.name == 'csgo':
                await server_status.serverStatus(ctx)
            else:
                await ctx.send("Command not enabled for this channel.")

    @csgo.command()
    async def help(self, ctx):
        await ctx.send(embed=self.help.make(ctx.author.name, 'csgo', self.directCommands, None, None))

    @csgo.command()
    async def register(self, ctx, username: str):
        # register member for csgo related services

        if ctx.message.channel.name == 'csgo':
            obj = Steam()

            await obj.register(self.bot, ctx, username)
        else:
            await ctx.send(f"{ctx.message.author}, command is not enabled for this channel.")

    @csgo.command()
    async def stats(self, ctx):
        if ctx.message.channel.name == 'csgo':
            pass


def setup(bot):
    bot.add_cog(CSGO(bot))