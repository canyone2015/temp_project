from datetime import datetime, timezone
from math import log10


class TimeStamp:
    @staticmethod
    def get_dt_from_timestamp(timestamp):
        if timestamp <= 0:
            return datetime.now(tz=None)
        if int(log10(timestamp) + 1) > 10:
            timestamp /= 1000.0
        return datetime.utcfromtimestamp(timestamp)

    @staticmethod
    def convert_utc_to_local_dt(utc_dt):
        return utc_dt.replace(tzinfo=timezone.utc).astimezone(tz=None)

    @staticmethod
    def get_local_dt_from_timestamp(timestamp):
        return TimeStamp.convert_utc_to_local_dt(TimeStamp.get_dt_from_timestamp(timestamp))

    @staticmethod
    def get_local_dt_from_now():
        return datetime.now(tz=None)

    @staticmethod
    def format_time(dt):
        return dt.strftime('%Y-%m-%d %H:%M:%S')

    @staticmethod
    def format_date(dt):
        return dt.strftime('%Y-%m-%d')
