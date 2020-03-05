from discord.ext import commands
from common import common
from .helpers import guild


class Moderation(commands.Cog):
    bot = None

    def __init__(self, bot):
        self.bot = bot
        config = common.getConfig()
        self.masterLog = int(config['COMMON']['logging'])

    @commands.group(pass_context=True)
    @commands.has_permissions(manage_messages=True)
    async def remove(self, ctx):
        pass

    @remove.command(pass_context=True)
    @commands.has_permissions(manage_roles=True)
    async def message(self, ctx, number:int):
        if number > 50:
            await ctx.send('Max number of message removal supported = 50.')

        async for message in self.bot.get_channel(ctx.message.channel.id).history(limit=number):
            await message.delete()

        logChannel = guild.getChannel(ctx.message.guild.id)

        await self.bot.get_channel(logChannel["channel_id"]).send(f'{ctx.message.author.name} deleted {number} messages.')


def setup(bot):
    bot.add_cog(Moderation(bot))
