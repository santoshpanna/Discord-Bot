from discord.ext import commands
from common import common


def normalize(cog):
    return 'cogs.'+cog+'_setup'


class Core(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.masterLogger = common.getMasterLog()

    @commands.command(name='load', hidden=True)
    @commands.is_owner()
    async def load(self, ctx, *, cog: str):
        try:
            self.bot.load_extension(normalize(cog))
        except Exception as e:
            await self.bot.get_channel(self.masterLogger).send(f'** ERROR loading {cog}: ** {type(e).__name__}')
        else:
            await ctx.send(f'** Loaded: ** {cog}')
            await self.bot.get_channel(self.masterLogger).send(f'** Loaded: ** {cog}')

    @commands.command(name='unload', hidden=True)
    @commands.is_owner()
    async def unload(self, ctx, *, cog: str):
        try:
            self.bot.unload_extension(normalize(cog))
        except Exception as e:
            await self.bot.get_channel(self.masterLogger).send(f'** ERROR unloading {cog}: ** {type(e).__name__}')
        else:
            await ctx.send(f'** Unloaded: ** {cog}')
            await self.bot.get_channel(self.masterLogger).send(f'** Unloaded: ** {cog}')

    @commands.command(name='reload', hidden=True)
    @commands.is_owner()
    async def reload(self, ctx, *, cog: str):
        try:
            self.bot.unload_extension(normalize(cog))
            self.bot.load_extension(normalize(cog))
        except Exception as e:
            await self.bot.get_channel(self.masterLogger).send(f'** ERROR loading {cog}: ** {type(e).__name__}')
        else:
            await ctx.send(f'** Loaded: ** {cog}')
            await self.bot.get_channel(self.masterLogger).send(f'** Loaded: ** {cog}')


def setup(bot):
    bot.add_cog(Core(bot))
