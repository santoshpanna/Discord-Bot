import discord
from discord.ext import commands
from cogs.helpers import steam, guild, gamedeals
from common import database, common

config = common.getConfig()
token = config['DISCORD']['token']

bot = commands.Bot(command_prefix=config['DISCORD']['prefix'])

formatter = commands.HelpCommand(show_check_failure=False)

modules = [
    'cogs.status_setup',
    'cogs.core_setup',
    'cogs.moderation_setup',
    'cogs.csgo_setup',
    'cogs.scrape_setup',
    'cogs.reddit_setup',
    'cogs.services_setup',
    'cogs.fun_setup',
    'cogs.price_setup',
    'cogs.cleaner_setup',
    'cogs.send_setup',
    'cogs.roles_setup'
]


@bot.event
async def on_ready():
    db = database.Database()

    db.updateBotStartTime()

    print(f'Logged in as {bot.user.name} - {bot.user.id}')
    # guild
    for guilds in bot.guilds:
        guild.updateGuidInfo(guilds)

    for module in modules:
        bot.load_extension(module)
    await bot.change_presence(status=discord.Status.online, activity=discord.CustomActivity(name='Testing mode >.<'))


bot.remove_command('help')
bot.run(token)
