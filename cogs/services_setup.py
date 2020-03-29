import discord
from discord.ext import commands
from common.database import Database
from .core_setup import Core
from common.common import getServiceList, STATUS, getMasterLog
from .helpers.guild import getLogChannel


class Service(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.core = Core(bot)
        self.db = Database()

    @commands.group(pass_context=True)
    async def service(self, ctx):
        if ctx.invoked_subcommand is None:
            description = 'To subscribe to a service type `!service init <servicename>`\n'
            description = description + 'To unsubscribe to a service type `!service deinit <servicename>`\n'
            description = description + 'Available services are : \n'
            servicelist = getServiceList()
            for service in servicelist:
                description = description + f'**{service : <30}** - {servicelist[service]}\n'
            description = description + '\n'
            description = description + 'Type the ***init*** and ***deinit*** command in channel you want to subscribe service in.'
            description = description + ' Multiple service can be subscribed to in one channel.'
            embed = discord.Embed(title='Service List', description=description)
            await ctx.send(embed=embed)

    @service.command()
    async def help(self, ctx):
        description = 'To subscribe to a service type `!service init <servicename>`\n'
        description = description + 'To unsubscribe to a service type `!service deinit <servicename>`\n'
        description = description + 'Available services are : \n'
        servicelist = getServiceList()
        for service in servicelist:
            description = description + f'**{service : <30}** - {servicelist[service]}\n'
        description = description + '\n'
        description = description + 'Type the ***init*** and ***deinit*** command in channel you want to subscribe service in.'
        description = description + ' Multiple service can be subscribed to in one channel.'
        embed = discord.Embed(title='Service List', description=description)
        await ctx.send(embed=embed)

    @service.command()
    @commands.has_permissions(manage_guild=True)
    async def init(self, ctx, name: str):
        # get the service list
        servicelist = getServiceList()

        flag = False
        # check if service name entered is real service or not
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
            if res == STATUS.SUCCESS:
                await ctx.send(f'Service *{name}* is now activated.')
                logging = getLogChannel(ctx.guild.id)
                if logging:
                    await self.bot.get_channel(logging).send(f'**Service activated**: *{ctx.author.name}* activated service *{name}* for channel *{ctx.channel.name}*.')
            elif res == STATUS.REDUNDANT:
                await ctx.send(f'Service *{name}* is already active for this channel.')
            else:
                await ctx.send(f'Service *{name}* could not be activated for this channel.')
        # service doesn't exist
        else:
            await ctx.send(f'Service*{name}* not found, see `!help service` for list of available services.')

    @service.command()
    @commands.has_permissions(manage_guild=True)
    async def deinit(self, ctx, name: str):
        # get the service list
        servicelist = getServiceList()

        flag = False
        # check if service name entered is real service or not
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
            if res == STATUS.SUCCESS:
                await ctx.send(f'service *{name}* is now deactivated.')
                logging = getLogChannel(ctx.guild.id)
                if logging:
                    await self.bot.get_channel(logging).send(f'**Service de-activated**: *{ctx.author.name}* de-activated service *{name}* for channel *{ctx.channel.name}*.')
            elif res == STATUS.FAIL.NOT_FOUND:
                await ctx.send(f'Service *{name}* is already deactivated for this channel.')
            else:
                await ctx.send(f'Service *{name}* could not be deactivated for this channel.')
        else:
            await ctx.send(f'Service *{name}* not found, see `!help service` for list of available services.')

    @service.command()
    @commands.is_owner()
    async def register(self, ctx, name: str, display_name: str):
        data = {'name': name, 'service_name': display_name}
        status = self.db.upsertService(data)
        if status == STATUS.SUCCESS:
            await self.bot.get_channel(getMasterLog()).send(f'**Service created**: *{name}* with display name as *{display_name}*.')
        else:
            await self.bot.get_channel(getMasterLog()).send(f'**Error**: Unable to create service *{name}* with display name as *{display_name}*.')


def setup(bot):
    bot.add_cog(Service(bot))
