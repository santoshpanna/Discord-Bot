from .scrape.csgoupdates import CsgoUpdates
from .scrape.destinyupdates import DestinyUpdates
from discord.ext import tasks, commands


class Scrape(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.job.start()
        
    def cog_unload(self):
        self.job.cancel()

    @tasks.loop(hours = 6.0)
    async def job(self):
        # scrape for csgo updates
        cs = CsgoUpdates()
        await cs.run(self.bot)

        # scrape for destiny 2 updates
        ds = DestinyUpdates()
        await ds.run(self.bot)


def setup(bot):
    bot.add_cog(Scrape(bot))