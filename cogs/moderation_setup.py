from discord.ext import commands
from common import common
from .helpers import guild
from .helpers.helpmaker import Help

class Moderation(commands.Cog):
    bot = None

    def __init__(self, bot):
        self.bot = bot
        self.masterLog = common.getMasterLog()
        self.groupedCommands = {}
        self.groupedCommands['remove'] = {'name': 'remove', 'description': 'helps in mass removal.'}
        self.groupedCommands['remove']['subcommand'] = {}
        self.groupedCommands['remove']['subcommand']['message'] = {'name': 'remove', 'arguments': 'number', 'description': 'remove <number> messages.'}
        self.help = Help()

    @commands.group(pass_context=True)
    @commands.has_permissions(manage_messages=True)
    async def mod(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send(embed=self.help.make(ctx.author.name, 'mod', None, self.groupedCommands, None))

    @mod.command()
    async def help(self, ctx):
        await ctx.send(embed=self.help.make(ctx.author.name, 'mod', None, self.groupedCommands, None))

    @mod.group(pass_context=True)
    @commands.has_permissions(manage_messages=True)
    async def remove(self, ctx):
        pass

    @remove.command()
    @commands.has_permissions(manage_messages=True)
    async def message(self, ctx, number:int):
        if number > 50:
            await ctx.send('Max number of message removal supported = 50.')

        async for message in self.bot.get_channel(ctx.message.channel.id).history(limit=number):
            await message.delete()

        logChannel = guild.getLogChannel(ctx.message.guild.id)
        if logChannel:
            await self.bot.get_channel(logChannel["channel_id"]).send(f'**Message Delete**: {ctx.message.author.name} deleted {number} messages from {ctx.channel.name}.')


def setup(bot):
    bot.add_cog(Moderation(bot))
