from common.database import Database


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
    db = Database()
    db.upsertGuidInfo(data)


def getLogChannel(guildid):
    db = Database()
    query = {}
    query["guild_id"] = guildid
    service = db.getService("logging")
    query["service_ids"] = str(service["_id"])
    return db.getChannelByService(query)


def getChannels(servicename):
    db = Database()

    # get all the guilds with required service
    guilds = db.getGuildsByService(servicename)

    # container
    channels = []

    # if guilds is not empty then there are guilds with service
    if guilds:
        for guild in guilds:
            # get the service id and information
            service = db.getService(servicename)
            # form search query
            query = {}
            query["guild_id"] = guild["id"]
            query["service_ids"] = str(service["_id"])
            gcs = db.getChannelsByService(query)

            for channel in gcs:
                service = db.getService("logging")
                query["service_ids"] = str(service["_id"])
                logging = db.getChannelsByService(query)
                if logging:
                    channel["logging"] = logging.next()["channel_id"]
                # append to get the final list
                channels.append(channel)

    return channels


def getChannelByGuild(guildid, servicename):
    db = Database()
    query = {}
    query["guild_id"] = guildid
    service = db.getService(servicename)
    query["service_ids"] = str(service["_id"])
    return db.getChannelByService(query)
