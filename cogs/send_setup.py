from discord.ext import commands
from .helpers.steam import Steam
from .helpers.helpmaker import Help
from .helpers.guild import getChannelByGuild
from common.database import Database


class Send(commands.Cog):
    steam_api_key = None

    def __init__(self, bot):
        self.bot = bot
        self.groupedCommands = {}
        self.groupedCommands['deal'] = {'name': 'deal', 'arguments': 'url', 'description':'sends the url to deals channel'}
        self.groupedCommands['crack'] = {'name': 'crack', 'arguments': 'url', 'description':'sends the url to deals channel'}
        self.groupedCommands['repack'] = {'name': 'repack', 'arguments': 'url', 'description':'sends the url to deals channel'}
        self.help = Help()
        self.db = Database()

    @commands.group(pass_context=True)
    async def send(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send(embed=self.help.make(ctx.author.name, 'send', None, self.groupedCommands))

    @send.command()
    async def help(self, ctx):
        await ctx.send(embed=self.help.make(ctx.author.name, 'send', None, self.groupedCommands))

    @send.command()
    async def deal(self, ctx, url: str):
        channel = getChannelByGuild(ctx.guild.id, 'gamedeals')

        if not channel:
            await ctx.send(f"GameDeals service is not enabled in your guild.")
        else:
            if 'steampowered.com' in url:
                obj = Steam()
                await obj.post(self.bot, channel, {'url': url})
            else:
                await self.bot.get_channel(int(channel['channel_id'])).send(url)

    @send.command()
    async def crack(self, ctx, url: str):
        channel = getChannelByGuild(ctx.guild.id, 'crackwatch')

        if not channel:
            await ctx.send(f"Crack News service is not enabled in your guild.")
        else:
            if 'steampowered.com' in url:
                obj = Steam()
                await obj.post(self.bot, channel, {'url': url})
            else:
                await self.bot.get_channel(int(channel['channel_id'])).send(url)

    @send.command()
    async def repack(self, ctx, url: str):
        channel = getChannelByGuild(ctx.guild.id, 'repacknews')

        if not channel:
            await ctx.send(f"Repack News service is not enabled in your guild.")
        else:
            if 'steampowered.com' in url:
                obj = Steam()
                await obj.post(self.bot, channel, {'url': url})
            else:
                await self.bot.get_channel(int(channel['channel_id'])).send(url)


def setup(bot):
    bot.add_cog(Send(bot))
