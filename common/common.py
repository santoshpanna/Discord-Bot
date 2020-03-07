import configparser
from datetime import datetime
import pytz
from dateutil.tz import tz

dtf_ist = "%d:%m:%Y %H:%M:%S"


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
    config = getConfig
    return int(config['COMMON']['masterlog'])