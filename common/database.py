import time
from . import common
from datetime import datetime
from pymongo import MongoClient, ASCENDING, errors
from _datetime import timedelta

# TODO
# - More error handling
# - Refactor

class Database:
    def __init__(self):
        # getting the configuration
        config = common.getConfig()
        client = MongoClient(config['DATABASE']['uri'])
        self.db = client.discordbot
        self.STATUS = common.STATUS

    ''' Services Start '''
    def getService(self, service):
        # returns the specified module data
        return self.db.services.find_one({'name': service})

    def upsertService(self, data):
        service = self.getService(data['name'])

        if service:
            data['date_updated'] = common.getDatetimeIST()
            count = self.db.services.update_one({'_id': service['_id']}, {'$set': data}).modified_count
            return self.STATUS.SUCCESS.UPDATED if count > 0 else self.STATUS.FAIL.UPDATE
        else:
            data['date_created'] = common.getDatetimeIST()
            data['date_updated'] = common.getDatetimeIST()
            try:
                status = self.db.services.insert_one(data).acknowledged
                return self.STATUS.SUCCESS.INSERTED if status else self.STATUS.FAIL.INSERT
            except errors.DuplicateKeyError:
                return self.STATUS.FAIL.DUPLICATE

    def getChannelByQuery(self, query):
        return self.db.guild_channel_mapping.find_one(query)
    ''' Service End '''

    ''' Steam Start '''
    def insertUserSteam(self, steam):
        # inserts a new user for a steam related services 
        data = {}
        data['steam64'] = steam.as_64
        data['url'] = steam.community_url
        data['date_created'] = common.getDatetimeIST()
        data['date_updated'] = common.getDatetimeIST()
        try:
            status = self.db.steam.insert_one(data).acknowledged
            return self.STATUS.SUCCESS if status else self.STATUS.FAIL.INSERT
        except errors.DuplicateKeyError:
            return self.STATUS.FAIL.DUPLICATE
    ''' Steam End '''

    ''' Status Start '''
    def getCountEstimates(self):
        data = {}
        data['gamedeals'] = self.db.gamedeals.estimated_document_count()
        data['cracks'] = self.db.crackwatch.count_documents({'type': 'crack'})
        data['repacks'] = self.db.crackwatch.count_documents({'type': 'repack'})
        data['prices'] = self.db.price_deal_mapping.estimated_document_count()
        data['members'] = self.db.members.estimated_document_count()
        data['services'] = self.db.services.estimated_document_count()
        data['guilds'] = self.db.guilds.estimated_document_count()
        return data

    def updateBotStartTime(self):
        # updates the time when the bot starts
        status = self.db.status.find_one()
        if status:
            count = self.db.status.update_one(
                {'_id': status['_id']},
                {'$set': {
                    'botStartTime': common.getDatetimeIST()
                }}
            ).modified_count
            return self.STATUS.SUCCESS if count > 0 else self.STATUS.FAIL.UPDATE
        else:
            status = self.db.status.insert_one({'botStartTime': common.getDatetimeIST()}).acknowledged
            return self.STATUS.SUCCESS if status else self.STATUS.FAIL.INSERT

    def getStatus(self):
        # get stats
        return self.db.status.find_one()
    ''' Status End '''

    ''' Guild Start '''
    def getGuildsByService(self, service):
        return self.db.guilds.find({"services_activated": service})

    def getChannelsByService(self, query):
        return self.db.guild_channel_mapping.find(query)

    def upsertGuidInfo(self, data):
        # find if guild exists in database
        guild = self.db.guilds.find_one({'id': data['id']})
        # if guild is present update the info
        if guild:
            data['date_updated'] = common.getDatetimeIST()
            count = self.db.guilds.update_one({'_id': guild['_id']}, {'$set': data}).modified_count
            return self.STATUS.SUCCESS if count > 0 else self.STATUS.FAIL.UPDATE
        # if its a new guild simply insert
        else:
            data['date_created'] = common.getDatetimeIST()
            data['date_updated'] = common.getDatetimeIST()
            try:
                status = self.db.guilds.insert_one(data).acknowledged
                return self.STATUS.SUCCESS if status else self.STATUS.FAIL.INSERT
            except errors.DuplicateKeyError:
                return self.STATUS.FAIL.DUPLICATE

    def createChannelMapping(self, data):
        # get the service
        service = self.db.services.find_one({'name': data['service_name']})

        # get the channel mapping
        mapping = self.db.guild_channel_mapping.find_one({'guild_id': data['guild_id'], 'channel_id': data['channel_id']})

        # there exists no mapping for current channel
        if not mapping:
            insert = {}
            insert['guild_id'] = data['guild_id']
            insert['channel_id'] = data['channel_id']
            insert['channel_name'] = data['channel_name']
            insert['service_ids'] = []
            insert['service_ids'].append(str(service['_id']))
            insert['date_created'] = common.getDatetimeIST()
            insert['date_updated'] = common.getDatetimeIST()
            status = self.db.guild_channel_mapping.insert_one(insert).acknowledged
            return self.STATUS.SUCCESS if status else self.STATUS.FAIL.INSERT

        else:
            # mapping is already created
            if str(service['_id']) in mapping['service_ids']:
                return self.STATUS.REDUNDANT
            else:
                update = {}
                update['service_ids'] = mapping['service_ids']
                update['service_ids'].append(str(service['_id']))
                update['date_updated'] = common.getDatetimeIST()
                count = self.db.guild_channel_mapping.update_one({'_id': mapping['_id']}, {'$set': update}).modified_count
                return self.STATUS.SUCCESS if count > 0 else self.STATUS.FAIL.UPDATE

    def deleteChannelMapping(self, data):
        # get the service
        service = self.db.services.find_one({'name': data['service_name']})

        # get the channel mapping
        mapping = self.db.guild_channel_mapping.find_one({'guild_id': data['guild_id'], 'channel_id': data['channel_id'], 'service_ids': str(service['_id'])})

        # there exists no mapping for current channel
        if not mapping:
            return self.STATUS.FAIL.NOT_FOUND
        else:
            if len(mapping['service_ids']) == 1:
                count = self.db.guild_channel_mapping.delete_one({'guild_id': mapping['guild_id'], 'channel_id': mapping['channel_id']}).deleted_count
                return self.STATUS.SUCCESS if count > 0 else self.STATUS.FAIL.DELETE
            else:
                update = {}
                update['service_ids'] = mapping['service_ids']
                update['service_ids'].remove(str(service['_id']))
                update['date_updated'] = common.getDatetimeIST()
                count = self.db.guild_channel_mapping.update_one({'_id': mapping['_id']}, {'$set': update}).modified_count
                return self.STATUS.SUCCESS if count > 0 else self.STATUS.FAIL.UPDATE
    ''' Guild End '''

    ''' Game Deals Start '''
    def getGameDeal(self, data):
        if isinstance(data, str):
            return self.db.gamedeals.find_one({'url': data})
        elif isinstance(data, dict) and 'url' in data:
            return self.db.gamedeals.find_one({'url': data['url']})
        else:
            return self.STATUS.FAIL.PARAMETER

    def upsertGameDeal(self, data):
        # add time to live
        deal = self.getGameDeal(data['url'])
        if deal:
            data['date_updated'] = common.getDatetimeIST()
            count = self.db.gamedeals.update_one({'_id': deal['_id']}, {'$set': data}).modified_count
            return self.STATUS.SUCCESS.UPDATED if count > 0 else self.STATUS.FAIL.UPDATE
        else:
            data['date_created'] = common.getDatetimeIST()
            data['date_updated'] = common.getDatetimeIST()
            try:
                status = self.db.gamedeals.insert_one(data).acknowledged
                return self.STATUS.SUCCESS.INSERTED if status else self.STATUS.FAIL.INSERT
            except errors.DuplicateKeyError:
                return self.STATUS.FAIL.DUPLICATE

    # function to remove older records
    def cleanGameDeal(self):
        count = self.db.gamedeals.delete_many({'ttl': {'$lte': common.getDatetimeIST()}}).deleted_count
        return self.STATUS.SUCCESS if count > 0 else self.STATUS.FAIL.DELETE
    ''' Game Deals End '''

    ''' Member Start '''
    def getMember(self, obj):
        member_id = None

        if isinstance(obj, object):
            member_id = obj.author.id
        elif isinstance(obj, str):
            member_id = int(obj)
        elif isinstance(obj, int):
            member_id = obj

        # if member is registered
        member = self.db.members.find_one({'id': member_id})

        if member:
            return member

        # member is not registered
        else:
            data = {}
            data['id'] = member_id
            data['name'] = obj.author.name
            data['priceTrackerLimit'] = 5
            data['isPremium'] = False
            data['date_created'] = common.getDatetimeIST()
            data['date_updated'] = common.getDatetimeIST()
            try:
                status = self.db.members.insert_one(data)
                return self.db.members.find_one({"_id": status.inserted_id}) if status.acknowledged else self.STATUS.FAIL.INSERT
            except errors.DuplicateKeyError:
                return self.STATUS.FAIL.DUPLICATE
    ''' Member End '''

    ''' Price Alert Start '''
    def insertPriceAlert(self, data):
        data['date_created'] = common.getDatetimeIST()
        data['date_updated'] = common.getDatetimeIST()
        data['cooldown'] = common.getDatetimeIST()
        try:
            status = self.db.price_deal_mapping.insert_one(data).acknowledged
            return self.STATUS.SUCCESS if status else self.STATUS.FAIL.INSERT
        except errors.DuplicateKeyError:
            return self.STATUS.FAIL.DUPLICATE

    def updatePriceAlerts(self, url, price):
        status = self.db.price_deal_mapping.update_many(
            {'url': url},
            {'$set': {
                'current_price': price,
                'cooldown': common.getDatetimeIST() + timedelta(hours=12),
                'date_updated': common.getDatetimeIST()
            }}
        ).acknowledged
        return self.STATUS.SUCCESS if status else self.STATUS.FAIL.UPDATE

    def updatePriceAlert(self, data):
        deal = self.db.price_deal_mapping.find_one({'member_id': data['member_id'], 'uuid': data['uuid']})

        if deal:
            update = None
            if 'alert_at' in data:
                update = self.db.price_deal_mapping.update_one({'_id': deal['_id']}, {'$set': {'alert_at': data['alert_at'], 'date_updated': common.getDatetimeIST()}}).acknowledged
            if 'currency' in data:
                update = self.db.price_deal_mapping.update_one({'_id': deal['_id']}, {'$set': {'currency': data['currency'], 'date_updated': common.getDatetimeIST()}}).acknowledged
            if 'cooldown' in data:
                update = self.db.price_deal_mapping.update_one({'_id': deal['_id']}, {'$set': {'cooldown': data['cooldown'], 'date_updated': common.getDatetimeIST()}}).acknowledged
            return self.STATUS.SUCCESS if update else self.STATUS.FAIL.UPDATE
        return self.STATUS.FAIL.NOT_FOUND

    def deletePriceAlert(self, data):
        count = self.db.price_deal_mapping.delete_one({'member_id': data['member_id'], 'uuid': data['uuid']}).deleted_count
        return self.STATUS.SUCCESS if count > 0 else self.STATUS.FAIL.DELETE

    def getPriceAlert(self, data=None):
        if not data:
            return self.db.price_deal_mapping.find()
        if isinstance(data, int):
            return self.db.price_deal_mapping.find({'member_id': data})
        elif isinstance(data, dict) and 'limit' in data and 'offset' in data:
            self.db.price_deal_mapping.find().limit(data['limit']).skip(data['offset'])
    ''' Price Alert End '''

    ''' Crack Watch Start '''
    def getCrackwatch(self, data):
        if isinstance(data, str):
            return self.db.crackwatch.find_one({'id': data})
        elif isinstance(data, dict) and 'id' in data:
            return self.db.crackwatch.find_one({'id': data['id']})
        else:
            return self.STATUS.FAIL.PARAMETER

    def upsertCrackwatch(self, data):
        crack = self.getCrackwatch(data)

        if crack or crack != self.STATUS.FAIL.PARAMETER:
            data['date_updated'] = common.getDatetimeIST()
            count = self.db.crackwatch.update_one({'_id': crack['_id']}, {'$set': data}).modified_count
            return self.STATUS.SUCCESS.UPDATED if count > 0 else self.STATUS.FAIL.UPDATE
        else:
            data['date_created'] = common.getDatetimeIST()
            data['date_updated'] = common.getDatetimeIST()
            try:
                status = self.db.crackwatch.insert_one(data).acknowledged
                return self.STATUS.SUCCESS.INSERTED if status else self.STATUS.FAIL.INSERT
            except errors.DuplicateKeyError:
                return self.STATUS.FAIL.DUPLICATE

    def cleanCrackwatch(self):
        count = self.db.crackwatch.delete_many({'ttl': {'$lte': common.getDatetimeIST()}}).deleted_count
        return self.STATUS.SUCCESS if count > 0 else self.STATUS.FAIL.DELETE
    ''' Crack Watch End '''

    ''' Patch Notes Start '''
    def getPatchnotes(self, data):
        if 'id' in data:
            data['id'] = data['service_name'] + str(data['id'])
            return self.db.patchnotes.find_one({'service_id': data['service_id'], 'id': data['id']})
        else:
            return self.db.patchnotes.find_one({'service_id': data['service_id']}).sort('date', ASCENDING)

    def upsertPatchnotes(self, data):
        patch = self.getPatchnotes(data)
        data['id'] = data['service_name'] + str(data['id'])
        if patch:
            count = self.db.patchnotes.update_one({'_id': patch['_id']}, {'$set': data}).modified_count
            return self.STATUS.SUCCESS.UPDATED if count > 0 else self.STATUS.FAIL.UPDATE
        else:
            status = self.db.patchnotes.insert_one(data).acknowledged
            return self.STATUS.SUCCESS.INSERTED if status else self.STATUS.FAIL.INSERT
    ''' Patch Notes End '''
