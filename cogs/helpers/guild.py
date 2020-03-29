from common.database import Database

db = Database()


def getOwnerInfo(member):
    data = {}
    data['id'] = member.id
    data['name'] = member.name
    data['bot'] = member.bot
    data['nick'] = member.nick
    data['guild'] = {}
    data['guild']['id'] = member.guild.id
    data['guild']['name'] = member.guild.name
    data['guild']['shard_id'] = member.guild.shard_id
    data['guild']['chunked'] = member.guild.chunked
    return data


def getChannel(channel):
    data = {}
    data['id'] = channel.id
    data['name'] = channel.name
    data['position'] = channel.position
    try:
        data['nsfw'] = channel.nsfw
    except AttributeError:
        pass

    try:
        data['bitrate'] = channel.bitrate
    except AttributeError:
        pass

    try:
        data['category_id'] = channel.category_id
    except AttributeError:
        pass

    return data


def updateGuidInfo(guild):
    data = {}
    data["name"] = guild.name
    data["region"] = guild.region.name
    data["id"] = guild.id
    data["afk_channel "] = getChannel(guild.afk_channel)
    data["owner"] = getOwnerInfo(guild.owner)
    data["description"] = guild.description
    data["default_notifications"] = guild.default_notifications.name
    data["premium_subscription_count"] = guild.premium_subscription_count
    data["large"] = guild.large
    data["member_count"] = guild.member_count
    data["created_at"] = guild.created_at
    db.upsertGuidInfo(data)


def getLogChannel(guild_id):
    query = {}
    query["guild_id"] = guild_id
    service = db.getService("logging")
    query["service_ids"] = str(service["_id"])
    return db.getChannelByQuery(query)


def getChannels(service_name):
    # get all the guilds with required service
    guilds = db.getGuildsByService(service_name)

    # container
    channels = []

    # if guilds is not empty then there are guilds with service
    if guilds:
        for guild in guilds:
            # get the service id and information
            service = db.getService(service_name)
            # form search query
            query = {}
            query["guild_id"] = guild["id"]
            query["service_ids"] = str(service["_id"])
            gcs = db.getChannelsByService(query)

            for channel in gcs:
                logging = getLogChannel(query["guild_id"])
                if logging:
                    channel["logging"] = logging["channel_id"]
                # append to get the final list
                channels.append(channel)

    return channels


def getChannelByService(guild_id, service_name):
    query = {}
    query["guild_id"] = guild_id
    service = db.getService(service_name)
    query["service_ids"] = str(service["_id"])
    return db.getChannelByQuery(query)


def getServiceByChannel(guild_id, channel_id):
    query = {}
    query["channel_id"] = channel_id
    if guild_id:
        query["guild_id"] = guild_id
    return db.getChannelByQuery(query)

