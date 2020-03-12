from discord.ext import commands
from .helpers.steam import Steam
from .helpers.helpmaker import Help
from .helpers.guild import getChannelByGuild
from common.database import Database
from .core_setup import Core
from common.common import getServiceList


class Service(commands.Cog):
    steam_api_key = None

    def __init__(self, bot):
        self.bot = bot
        self.core = Core(bot)
        self.db = Database()

    @commands.group(pass_context=True)
    async def service(self, ctx):
        if ctx.invoked_subcommand is None:
            self.core.service(ctx)

    @service.command(pass_context=True)
    async def help(self, ctx):
        self.core.service(ctx)

    @service.command(pass_context=True)
    @commands.has_permissions(manage_guild=True)
    async def init(self, ctx, name: str):
        # get the service list
        servicelist = getServiceList()

        flag = False
        # check if servicename entered is real service or not
        for service in servicelist:
            if service == name:
                flag = True
                break

        if flag:
            data = {}
            data['guild_id'] = ctx.guild.id
            data['channel_id'] = ctx.channel.id
            data['channel_name'] = ctx.channel.name
            data['service_name'] = name
            res = self.db.createChannelMapping(data)
            if res == 1:
                await ctx.send(f"service ***{name}*** is now activated.")
            elif res == 2:
                await ctx.send(f"service ***{name}*** is already active for this channel.")
            else:
                await ctx.send(f"service ***{name}*** could not be activated for this channel.")

        else:
            await ctx.send(f"{name} service not found, see `!help service` for list of available services.")

    @service.command(pass_context=True)
    @commands.has_permissions(manage_guild=True)
    async def deinit(self, ctx, name: str):
        # get the service list
        servicelist = getServiceList()

        flag = False
        # check if servicename entered is real service or not
        for service in servicelist:
            if service == name:
                flag = True
                break

        if flag:
            data = {}
            data['guild_id'] = ctx.guild.id
            data['channel_id'] = ctx.channel.id
            data['channel_name'] = ctx.channel.name
            data['service_name'] = name
            res = self.db.deleteChannelMapping(data)
            if res == 1:
                await ctx.send(f"service ***{name}*** is now deactivated.")
            elif res == 2:
                await ctx.send(f"service ***{name}*** is already deactivated for this channel.")
            else:
                await ctx.send(f"service ***{name}*** could not be deactivated for this channel.")

        else:
            await ctx.send(f"{name} service not found, see `!help service` for list of available services.")


def setup(bot):
    bot.add_cog(Service(bot))
