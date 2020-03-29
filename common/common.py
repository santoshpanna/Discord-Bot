import configparser
from datetime import datetime
import pytz
from dateutil.tz import tz
from hashids import Hashids
from enum import Enum

dtf_ist = "%d:%m:%Y %H:%M:%S"


class STATUS(Enum):
    PARAMETER = -6
    NOT_FOUND = -5
    DUPLICATE = -4
    DELETE = -3
    UPDATE = -2
    INSERT = -1
    FAIL = [INSERT, UPDATE, DELETE, NOT_FOUND, DUPLICATE, PARAMETER]
    SUCCESS = 1
    REDUNDANT = 2
    INSERTED = 2
    UPDATED = 2


# time <- str to parsed time
def getDatetimeIST(prettify: str = None):
    if prettify:
        return datetime.strftime(datetime.today(), dtf_ist)
    return datetime.today()


# get the config
def getConfig():
    config = configparser.ConfigParser()
    try:
        config.read('config.cfg')
        return config
    except FileNotFoundError:
        return False


# time <- timestamp
def getTimeFromTimestamp(timestamp):
    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")


# converts utc to localtime, which is IST for me
def getLocalTime(time, format):
    ist = tz.gettz('IST')
    naive = datetime.strptime(time, format)
    local_dt = pytz.utc.localize(naive, is_dst=None).astimezone(ist)
    time = local_dt.strftime("%Y-%m-%d %H:%M:%S")
    return time


# get the environment
def getEnvironment():
    config = getConfig()
    return config['COMMON']['environment']


# this is not the normal logging channel
# used to track status of cogs in dev server
# for normal bot logging use logging service
def getMasterLog():
    config = getConfig()
    return int(config['COMMON']['masterlog'])


def getServiceList():
    service = {}
    service['csgoupdates'] = 'CSGO update news'
    service['destinyupdates'] = 'Destiny 2 update news'
    service['crackwatch'] = 'Game crack news'
    service['repacknews'] = 'Game repack news'
    service['gamedeals'] = 'Game deal news'
    service['roles'] = 'Automatic role allocation service'
    service['logging'] = 'Logging service for your guild'
    return service


def getCommands():
    commands = []
    commands.append('service')
    commands.append('status')
    commands.append('mod')
    commands.append('fun')
    commands.append('pricetracker')
    commands.append('roles')
    return commands


def getUID(id):
    config = getConfig()
    hashids = Hashids(salt = config['COMMON']['salt'], alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890")
    return hashids.encode(int(datetime.today().timestamp())+id)
