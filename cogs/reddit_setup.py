from .reddit.crackwatch import CrackWatch
from .reddit.gamedeals import GameDeals
from discord.ext import tasks, commands
from .helpers import gamedeals


class Reddit(commands.Cog):
    bot = None

    def __init__(self, bot):
        self.bot = bot
        self.job.start()
        self.cleaner.start()

    def cog_unload(self):
        self.job.cancel()
        self.cleaner.cancel()

    # 1 month, like bots gonna run continously for 1 month straight
    @tasks.loop(hours = 720.0)
    async def cleaner(self): 
        await gamedeals.cleaner(self.bot)

    @commands.group(pass_context=True)
    async def clean(self):
        await gamedeals.cleaner(self.bot)

    @tasks.loop(minutes = 30.0)
    async def job(self):     
        # r/CrackWatch
        cw = CrackWatch()
        await cw.run(self.bot)
        
        # r/SteamDeals r/gamedeals r/Freegamefindings
        gd = GameDeals()
        await gd.run(self.bot)

def setup(bot):
    bot.add_cog(Reddit(bot))
