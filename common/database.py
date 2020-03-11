import time
from . import common
from datetime import datetime
from pymongo import MongoClient
from _datetime import timedelta


class Database:
    def __init__(self):
        # getting the configuration
        config = common.getConfig()
        client = MongoClient(config['DATABASE']['uri'])
        self.db = client.discordbot

    # services
    def getService(self, service):
        # returns the specified module data
        return self.db.services.find_one({'name': service})

    def updateService(self, data):
        # updates specified module
        obj = self.db.services.find_one({'name': data["name"]})

        data['timeupdated'] = common.getDatetimeIST()

        return self.db.services.update_one(
            {'_id': obj['_id']},
            {'$set': data}
        ).acknowledged

    def insertService(self, service):
        # insert a module
        obj = self.db.services.find_one({"name": service["name"]})
        # if its a new module
        if not obj:
            return self.db.services.insert_one(service).acknowledged
        return False

    # steam
    def insertUserSteam(self, steam):
        # inserts a new user for a steam related services 
        data = {
            'steam64': steam.as_64,
            'url': steam.community_url
        }
        return self.db.steam.insert_one(data).acknowledged

    # status
    def updateBotStartTime(self):
        # updates the time when the bot starts

        status = self.db.status.find_one({})
        if status:
            return self.db.status.update_one(
                {'_id': status['_id']},
                {'$set': {
                    'botStartTime': common.getDatetimeIST()
                }}
            ).acknowledged
        else:
            return self.db.status.insert_one(
                {'botStartTime': common.getDatetimeIST()}
            ).acknowledged

    def getStatus(self):
        # get stats
        return self.db.status.find_one({})

    # guilds
    def getGuildsByService(self, service):
        return self.db.guilds.find({"services_activated": service})

    def getChannelsByService(self, query):
        result = self.db.guild_channel_mapping.find(query)
        return result

    def upsertGuidInfo(self, data):
        # find if guild exists in database
        guild = self.db.guilds.find_one({'id': data['id']})
        # if guild is present update the info
        if guild:
            return self.db.guilds.update_one(
                {'_id': guild['_id']},
                {'$set': data}
            ).acknowledged
        # if its a new guild simply insert
        else:
            return self.db.guilds.insert_one(data).acknowledged

    # Game deals
    def getDeal(self, deal):
        return self.db.gamedeals.find_one({'url': deal['url']})

    def upsertDeal(self, deal):
        # add time to live
        deal['ttl'] = common.getDatetimeIST() + timedelta(days=30)

        exists = self.db.gamedeals.find_one({'url': deal['url']})

        if exists:
            deal['updated_at'] = common.getDatetimeIST()
            status = self.db.gamedeals.update_one(
                {'_id': exists['_id']},
                {'$set': deal}
            ).acknowledged

            if status:
                return 1

        else:
            deal['created_at'] = common.getDatetimeIST()
            status = self.db.gamedeals.insert_one(deal).acknowledged

            if status:
                return 2

        return -1

    def checkGetDeal(self, deal):
        exists = self.db.gamedeals.find_one({'url': deal['url']})
        if exists:
            return exists
        else:
            return False

    # function to remove older records
    def cleanDeals(self):
        return self.db.gamedeals.delete_many({'ttl': {'$lte': common.getDatetimeIST()}}).deleted_count
