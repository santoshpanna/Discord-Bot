from .reddit.crackwatch import CrackWatch
from .reddit.gamedeals import GameDeals
from discord.ext import tasks, commands
from .helpers import gamedeals


class Reddit(commands.Cog):
    bot = None

    def __init__(self, bot):
        self.bot = bot
        self.cw = CrackWatch()
        self.gd = GameDeals()
        self.gamedeals.start()
        self.crackwatch.start()
        self.cleaner.start()

    def cog_unload(self):
        self.gamedeals.cancel()
        self.crackwatch.cancel()
        self.cleaner.cancel()

    # 1 month, like bots gonna run continuously for 1 month straight
    @tasks.loop(hours = 720.0)
    async def cleaner(self): 
        await gamedeals.cleaner(self.bot)
        await self.cw.cleaner(self.bot)

    @tasks.loop(minutes = 30.0)
    async def gamedeals(self):            
        # r/SteamDeals r/gamedeals r/Freegamefindings
        await self.gd.run(self.bot)

    @tasks.loop(minutes = 60.0)
    async def crackwatch(self):
        await self.cw.run(self.bot)


def setup(bot):
    bot.add_cog(Reddit(bot))
