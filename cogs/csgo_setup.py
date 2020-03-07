from discord.ext import commands
from .csgo import server_status
from .helpers.steam import Steam
from common.database import Database


class CSGO(commands.Cog):
    steam_api_key = None

    def __init__(self, bot):
        self.bot = bot
    
    @commands.group(pass_context=True)
    async def csgo(self, ctx):
        # commands for csgo
        # if no sub commands is passed display the current no of searching players and players online instead
        if ctx.invoked_subcommand is None:
            if ctx.message.channel.name == 'lobby' or ctx.message.channel.name == 'csgo':
                await server_status.serverStatus(ctx)
            else:
                await ctx.send("Command not enabled for this channel.")

    @csgo.command(pass_context=True)
    async def register(self, ctx, username: str):
        # register member for csgo related services

        if ctx.message.channel.name == 'csgo':
            obj = Steam()

            await obj.register(self.bot, ctx, username)
        else:
            await ctx.send(f"{ctx.message.author}, command is not enabled for this channel.")


def setup(bot):
    bot.add_cog(CSGO(bot))
