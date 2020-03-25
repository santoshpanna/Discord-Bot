import discord
from discord.ext import commands
from .helpers.helpmaker import Help
from .helpers.guild import getChannelByGuild
from common import common
from common.database import Database


class Roles(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.groupedCommands = {}
        self.groupedCommands['init'] = {'name': 'init', 'arguments': 'rolename description', 'description':'initializes the channel to be specific to rolename and role description'}
        self.groupedCommands['deinit'] = {'name': 'deinit', 'arguments': 'rolename', 'description':'de-initializes the channel to be specific to rolename'}
        self.groupedCommands['create'] = {'name': 'create', 'arguments': 'rolename', 'description':'creates a new role'}
        self.groupedCommands['delete'] = {'name': 'delete', 'arguments': 'rolename', 'description':'delete the role'}
        self.help = Help()
        self.db = Database()
        self.masterLogger = common.getMasterLog()

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        # get channel
        channel = self.bot.get_channel(payload.channel_id)
        # get message
        message = await channel.fetch_message(payload.message_id)
        # check if bot was the poster and check emoji for further action
        if self.bot.user.id == message.author.id and (payload.emoji.name == '❤️' or payload.emoji.name == '💔'):
            # get role from message
            role = message.content[message.content.find('@') + 1: message.content.find(' ', message.content.find('@'))]
            # check if any role was found
            if role != message.content and role != "":
                # get guild, user and role
                guild = self.bot.get_guild(payload.guild_id)
                author = guild.get_member(payload.member.id)
                role = discord.utils.get(guild.roles, name=role)
                if payload.emoji.name == '💔':
                    # remove role
                    await author.remove_roles(role)
                else:
                    # add role
                    await author.add_roles(role)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        # get channel
        channel = self.bot.get_channel(payload.channel_id)
        # get message
        message = await channel.fetch_message(payload.message_id)
        # check if bot was the poster and check the emoji
        if self.bot.user.id == message.author.id and (payload.emoji.name == '❤️' or payload.emoji.name == '💔'):
            # get role
            role = message.content[message.content.find('@') + 1: message.content.find(' ', message.content.find('@'))]
            if role != message.content and role != "":
                # if correct emoji was found and also role exists in message
                guild = self.bot.get_guild(payload.guild_id)
                author = guild.get_member(payload.member.id)
                role = discord.utils.get(guild.roles, name=role)
                # remove role
                await author.remove_roles(role)
        
    @commands.group(pass_context=True)
    async def roles(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send(embed=self.help.make(ctx.author.name, 'roles', None, self.groupedCommands, None))

    @roles.command()
    async def help(self, ctx):
        await ctx.send(embed=self.help.make(ctx.author.name, 'roles', None, self.groupedCommands, None))

    @roles.command()
    @commands.has_permissions(manage_channels=True)
    async def init(self, ctx, name: str, message: str):
        # get the role, case sensitive
        role = discord.utils.get(ctx.guild.roles, name=name)
        logChannel = getChannelByGuild(ctx.guild.id, 'logging')
        rolesChannel = getChannelByGuild(ctx.guild.id, 'roles')

        if rolesChannel:
            # role does not exists
            if not role:
                # create new role
                await ctx.guild.create_role(name=name)
                # get the new role
                role = discord.utils.get(ctx.guild.roles, name=name)
                if logChannel:
                    await self.bot.get_channel(logChannel['channel_id']).send(f'**Role created** : **{ctx.author.name}** created role **{name}**.')

            # update default role permission
            await ctx.channel.set_permissions(ctx.guild.default_role, view_channel=False)
            # add new permission
            await ctx.channel.set_permissions(role, view_channel=True)

            # post a log in log channel
            if logChannel:
                await self.bot.get_channel(logChannel['channel_id']).send(f'**Channel permission change** : **{ctx.author.name}** changed **{ctx.channel.name}** permission visible only to role **{name}**.')

            # post a general message in current channel
            await ctx.send(f"Channel permission updated for **{ctx.channel.name}** by **{ctx.author.name}**.")

            # add a new message to roles channel so that users can react and subscribe to roles
            await self.bot.get_channel(rolesChannel['channel_id']).send(f'To subscribe to @{name} react with :heart:, to un-subscribe react with :broken_heart:. **{name}** give you access to {message}.')
        else:
            # the role service was enabled in current guild
            await ctx.send("Roles channel is not initialized, please do so by issuing `!service init roles` in roles channel. Then re-issue roles command.")

    @roles.command()
    @commands.has_permissions(manage_channels=True)
    async def deinit(self, ctx, name: str):
        # get the role, case sensitive
        role = discord.utils.get(ctx.guild.roles, name=name)

        # role exists
        if role:
            # reset the view permission for default role
            await ctx.channel.set_permissions(ctx.guild.default_role, view_channel=True)
            # post a general message in current channel
            await ctx.send("Channel permission updated for **{ctx.channel.name}** by **{ctx.author.name}**.")
            # post detailed message in logging channel
            logChannel = getChannelByGuild(ctx.guild.id, 'logging')
            if logChannel:
                await self.bot.get_channel(logChannel['channel_id']).send(f'**Channel permission change** : **{ctx.author.name}** changed **{ctx.channel.name}** permission visible only to default role **{ctx.guild.default_role.name.replace("@", "")}**.')
        else:
            # role does not exist
            await ctx.send(f'Role ***{name}*** does not exist.')

    @roles.command()
    @commands.has_permissions(manage_roles=True)
    async def create(self, ctx, name: str):
        # get the role, case sensitive
        role = discord.utils.get(ctx.guild.roles, name=name)
        logChannel = getChannelByGuild(ctx.guild.id, 'logging')
        # role does not exists
        if not role:
            # create new role
            await ctx.guild.create_role(name=name)
            # post log in logging channel
            if logChannel:
                await self.bot.get_channel(logChannel['channel_id']).send(f'**Role created** : **{ctx.author.name}** created role **{name}**.')
        else:
            await ctx.send(f'Role ***{name}*** already exists.')

    @roles.command()
    @commands.has_permissions(manage_roles=True)
    async def delete(self, ctx, name: str):
        # get the role, case sensitive
        role = discord.utils.get(ctx.guild.roles, name=name)

        # role does not exists
        if role:
            await role.delete(reason=f"{ctx.channel.name} issued delete command in channel {ctx.channel.name}")
            # await ctx.guild.delete_role(role_id=role.id)
            await ctx.send(f'Role ***{name}*** has been deleted.')
            logChannel = getChannelByGuild(ctx.guild.id, 'logging')
            if logChannel:
                await self.bot.get_channel(logChannel['channel_id']).send(f'**Role deleted** : **{ctx.author.name}** deleted role **{name}**.')
        else:
            await ctx.send(f'Role ***{name}*** does not exist.')


def setup(bot):
    bot.add_cog(Roles(bot))
