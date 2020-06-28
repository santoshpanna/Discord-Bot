import discord
from discord.ext import commands
from cogs.helpers import steam, guild, gamedeals
from common import database, common

config = common.getConfig()
token = config['DISCORD']['token']

bot = commands.Bot(command_prefix=config['DISCORD']['prefix'])

formatter = commands.HelpCommand(show_check_failure=False)

modules_prod = [
    'cogs.youtube_setup',
    'cogs.core_setup'
    #'cogs.status_setup',
    #'cogs.moderation_setup',
    #'cogs.csgo_setup',
    #'cogs.scrape_setup',
    #'cogs.reddit_setup',
    #'cogs.services_setup',
    #'cogs.fun_setup',
    #'cogs.price_setup',
    #'cogs.cleaner_setup',
    #'cogs.send_setup',
    #'cogs.roles_setup'
]

modules_dev = [
    'cogs.status_setup',
    'cogs.core_setup',
    'cogs.moderation_setup',
    'cogs.services_setup',
    'cogs.roles_setup'
    'cogs.send_setup'
]


@bot.event
async def on_connect():
    db = database.Database()

    # update bot start time
    db.updateBotStartTime()


@bot.event
async def on_ready():
    # if env is not dev the load regular cogs
    if common.getEnvironment() != 'dev':
        # # guild
        # for guilds in bot.guilds:
        #     guild.updateGuidInfo(guilds)

        for module in modules_prod:
            bot.load_extension(module)
    # load cogs which are are development
    else:
        for module in modules_dev:
            bot.load_extension(module)

    await bot.change_presence(status=discord.Status.online, activity=discord.CustomActivity(name='Testing mode >.<'))

# remove default help
# see cogs/core for new help
bot.remove_command('help')
bot.run(token)
