from discord.ext import commands
import discord
from .helpers import guild
from common import common


def normalize(cog):
    return 'cogs.'+cog+'_setup'


class Core(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.masterLogger = common.getMasterLog()

    @commands.group(pass_context=True)
    async def help(self, ctx):
        if ctx.invoked_subcommand is None:
            description = 'To invoke a command use `!<command>`\n'
            description = description + 'To view subcommands use `!<command> help`\n'
            description = description + 'Available commands are : \n'
            description = description + '**service**\n'
            description = description + '**status**\n'
            description = description + '**mod**\n'
            description = description + '**fun**\n'
            description = description + '**pricetracker**\n'
            description = description + '\n'
            description = description + f'`{"!help service" : <20} - to view available services`'
            embed = discord.Embed(title='Help', description=description)
            await ctx.send(embed=embed)

    @help.command()
    async def service(self, ctx):
        description = 'To subscribe to a service type `!service init <servicename>`\n'
        description = description + 'To unsubscribe to a service type `!service deinit <servicename>`\n'
        description = description + 'Available services are : \n'
        servicelist = common.getServiceList()
        for service in servicelist:
            description = description + f'**{service : <30}** - {servicelist[service]}\n'
        description = description + '\n'
        description = description + 'Type the ***init*** and ***deinit*** command in channel you want to subscribe service in.'
        description = description + ' Multiple service can be subscribed to in one channel.'
        embed = discord.Embed(title='Service List', description=description)
        await ctx.send(embed=embed)

    @commands.command(name='load')
    @commands.is_owner()
    async def load(self, ctx, *, cog: str):
        try:
            self.bot.load_extension(normalize(cog))
        except Exception as e:
            await self.bot.get_channel(self.masterLogger).send(f'** ERROR loading {cog}: ** {type(e).__name__}')
        else:
            await ctx.send(f'** Loaded: ** {cog}')
            await self.bot.get_channel(self.masterLogger).send(f'** Loaded: ** {cog}')

    @commands.command(name='unload')
    @commands.is_owner()
    async def unload(self, ctx, *, cog: str):
        try:
            self.bot.unload_extension(normalize(cog))
        except Exception as e:
            await self.bot.get_channel(self.masterLogger).send(f'** ERROR unloading {cog}: ** {type(e).__name__}')
        else:
            await ctx.send(f'** Unloaded: ** {cog}')
            await self.bot.get_channel(self.masterLogger).send(f'** Unloaded: ** {cog}')

    @commands.command(name='reload')
    @commands.is_owner()
    async def reload(self, ctx, *, cog: str):
        try:
            self.bot.unload_extension(normalize(cog))
            self.bot.load_extension(normalize(cog))
        except Exception as e:
            await self.bot.get_channel(self.masterLogger).send(f'** ERROR reloading {cog}: ** {type(e).__name__}')
        else:
            await ctx.send(f'** Reloaded: ** {cog}')
            await self.bot.get_channel(self.masterLogger).send(f'** Reloaded: ** {cog}')


def setup(bot):
    bot.add_cog(Core(bot))
