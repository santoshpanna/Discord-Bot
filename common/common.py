import configparser
from datetime import datetime
import pytz
from dateutil.tz import tz

dtf_ist = "%d:%m:%Y %H:%M:%S"


def getDatetimeIST(prettify: str = None):
    if prettify:
        return datetime.strftime(datetime.today(), dtf_ist)
    return datetime.today()


def getConfig():
    config = configparser.ConfigParser()
    try:
        config.read('config.cfg')
        return config
    except FileNotFoundError:
        return False


def getTimeFromTimestamp(timestamp):
    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")


def getLocalTime(time, format):
    ist = tz.gettz('IST')
    naive = datetime.strptime(time, format)
    local_dt = pytz.utc.localize(naive, is_dst=None).astimezone(ist)
    time = local_dt.strftime("%Y-%m-%d %H:%M:%S")
    return time