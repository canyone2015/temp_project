from typing import Union
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from math import ceil
import random


def decimal_number(number):
    if isinstance(number, (int, float, Decimal)):
        return Decimal(f'{number:g}')
    if number is None:
        return Decimal(0)
    return decimal_number(Decimal(number))


class TimeStamp:
    UTC_LOCAL_TIME_DIFFERENCE = int(datetime.now().astimezone(None).utcoffset().total_seconds())

    @staticmethod
    def normalize_timestamp(timestamp):
        k = 1
        if len(str(int(timestamp))) > 10:
            k = 1000
        return timestamp / k

    @staticmethod
    def convert_utc_to_local_dt(utc_dt):
        return utc_dt.replace(tzinfo=timezone.utc).astimezone(tz=None)

    @staticmethod
    def convert_local_to_utc_dt(utc_dt):
        return utc_dt.replace(tzinfo=None).astimezone(tz=timezone.utc)

    @staticmethod
    def get_utc_dt_from_timestamp(timestamp):
        return datetime.utcfromtimestamp(TimeStamp.normalize_timestamp(timestamp))

    @staticmethod
    def get_local_dt_from_timestamp(timestamp):
        return TimeStamp.convert_utc_to_local_dt(TimeStamp.get_utc_dt_from_timestamp(timestamp))

    @staticmethod
    def get_local_dt_from_now():
        return datetime.now(tz=None)

    @staticmethod
    def get_utc_dt_from_now():
        return datetime.now(tz=timezone.utc)

    @staticmethod
    def format_datetime(dt, *, pattern='%Y-%m-%d %H:%M:%S'):
        return dt.strftime(pattern)

    @staticmethod
    def timedelta(*,
                  weeks=0,
                  days=0,
                  hours=0,
                  minutes=0,
                  seconds=0):
        return timedelta(weeks=weeks, days=days, hours=hours, minutes=minutes, seconds=seconds)

    @staticmethod
    def format_date(dt, *, pattern='%Y-%m-%d'):
        return dt.strftime(pattern)

    @staticmethod
    def format_time(dt, *, pattern='%H:%M:%S'):
        return dt.strftime(pattern)

    @staticmethod
    def parse_datetime(string, *, utc=True, pattern='%Y-%m-%d %H:%M:%S'):
        return datetime.strptime(string, pattern).astimezone(timezone.utc if utc else None)

    @staticmethod
    def parse_date(string, *, utc=True, pattern='%Y-%m-%d'):
        return datetime.strptime(string, pattern).astimezone(timezone.utc if utc else None)

    @staticmethod
    def parse_time(string, *, utc=True, pattern='%H:%M:%S'):
        return datetime.strptime(string, pattern).astimezone(timezone.utc if utc else None)

    @staticmethod
    def convert_utc_to_local_timestamp(utc_timestamp):
        k = 1
        if len(str(int(utc_timestamp))) > 10:
            k = 1000
        return utc_timestamp + TimeStamp.UTC_LOCAL_TIME_DIFFERENCE * k

    @staticmethod
    def convert_local_to_utc_timestamp(local_timestamp):
        k = 1
        if len(str(int(local_timestamp))) > 10:
            k = 1000
        return local_timestamp - TimeStamp.UTC_LOCAL_TIME_DIFFERENCE * k

    @staticmethod
    def convert_timeframe_to_seconds(tf):
        q = int(tf[:-1])
        s = (tf[-1] in 'mhdwM' and 60 or 1) * \
            (tf[-1] in 'hdwM' and 60 or 1) * \
            (tf[-1] in 'dwM' and 24 or 1) * \
            (tf[-1] in 'wM' and 7 or 1) * \
            (tf[-1] in 'M' and (365.2425 / 12) or 1)
        return q * s

    @staticmethod
    def get_number_of_candles(tf, date_from_timestamp, date_to_timestamp):
        date_from_timestamp = TimeStamp.normalize_timestamp(date_from_timestamp)
        date_to_timestamp = TimeStamp.normalize_timestamp(date_to_timestamp)
        r = ceil((date_to_timestamp - date_from_timestamp) / TimeStamp.convert_timeframe_to_seconds(tf))
        return r

    @staticmethod
    def adjust_timeframe(*, timeframes, candles, date_from_timestamp, date_to_timestamp):
        timeframes = {timeframe: TimeStamp.convert_timeframe_to_seconds(timeframe) for timeframe in timeframes}
        for tf_str, tf_seconds in sorted(timeframes.items(), key=lambda x: x[1]):
            if TimeStamp.get_number_of_candles(tf_str, date_from_timestamp, date_to_timestamp) <= candles:
                return tf_str
        return min(timeframes, key=lambda x: x[1])[0]

    @staticmethod
    def get_timestamps_range(date_from_timestamp: Union[int, float, ..., None],
                             date_to_timestamp: Union[int, float, ..., None],
                             *,
                             utc: bool = True):
        b11, b12 = date_from_timestamp is None, date_to_timestamp is None
        b21, b22 = date_from_timestamp is ..., date_to_timestamp is ...

        if not b11 and not b21:
            date_from_timestamp = TimeStamp.normalize_timestamp(date_from_timestamp)
            if not utc:  # convert to utc
                date_from_timestamp = TimeStamp.convert_local_to_utc_timestamp(date_from_timestamp)

        if not b12 and not b22:
            date_to_timestamp = TimeStamp.normalize_timestamp(date_to_timestamp)
            if not utc:  # convert to utc
                date_to_timestamp = TimeStamp.convert_local_to_utc_timestamp(date_to_timestamp)

        current_timestamp = int(TimeStamp.get_utc_dt_from_now().timestamp())
        one_day = timedelta(days=1).total_seconds()

        if b11 and b12:  # [None, None]
            date_from_timestamp = current_timestamp
            date_to_timestamp = current_timestamp
        elif b11:  # [None, ?]
            if b22:  # [None, ...]
                date_to_timestamp = current_timestamp
            date_from_timestamp = date_to_timestamp - one_day
        elif b12:  # [?, None]
            if b21:  # [..., None]
                date_from_timestamp = current_timestamp
            date_to_timestamp = date_from_timestamp + one_day
        else:
            if b21:
                date_from_timestamp = current_timestamp
            if b22:
                date_to_timestamp = current_timestamp
        if date_from_timestamp > date_to_timestamp:
            date_from_timestamp, date_to_timestamp = date_to_timestamp, date_from_timestamp
        if not utc:
            date_from_timestamp = TimeStamp.convert_utc_to_local_timestamp(date_from_timestamp)
            date_to_timestamp = TimeStamp.convert_utc_to_local_timestamp(date_to_timestamp)
        return date_from_timestamp, date_to_timestamp


class ArithOHLCVList:
    def __init__(self, lst=None):
        self._list = list() if lst is None else list(lst)

    def __op(self, other, op_func):

        def op(arg1, arg2):
            try:
                return op_func(arg1, arg2)
            except:
                return 0

        if isinstance(other, ArithOHLCVList):
            other = other._list
        if isinstance(other, list):
            this = self._list
            r = []
            s1, s2 = 0, 0
            while s1 < len(this) and s2 < len(other):
                if this[s1][0] < other[s2][0]:
                    s1 += 1
                elif this[s1][0] > other[s2][0]:
                    s2 += 1
                else:
                    r.append([
                        this[s1][0],
                        op(this[s1][1], other[s2][1]),
                        op(this[s1][2], other[s2][2]),
                        op(this[s1][3], other[s2][3]),
                        op(this[s1][4], other[s2][4]),
                        op(this[s1][5], other[s2][5]),
                    ])
                    s1 += 1
                    s2 += 1
            return ArithOHLCVList(r)
        else:
            return ArithOHLCVList([
                [x[0],  # timestamp
                 op(x[1], other),  # open
                 op(x[2], other),  # high
                 op(x[3], other),  # low
                 op(x[4], other),  # close
                 op(x[5], other),  # volume
                 ] for x in self._list])

    def __add__(self, other):
        return self.__op(other, lambda x, y: x + y)

    def __sub__(self, other):
        return self.__op(other, lambda x, y: x - y)

    def __mul__(self, other):
        return self.__op(other, lambda x, y: x * y)

    def __truediv__(self, other):
        return self.__op(other, lambda x, y: x / (y or decimal_number(1e-9)))

    def __floordiv__(self, other):
        return self.__op(other, lambda x, y: x // (y or decimal_number(1e-9)))

    def __mod__(self, other):
        return self.__op(other, lambda x, y: x % (y or decimal_number(1e-9)))

    def __pow__(self, other):
        return self.__op(other, lambda x, y: x ** y)

    def __radd__(self, other):
        return self.__op(other, lambda x, y: y + x)

    def __rsub__(self, other):
        return self.__op(other, lambda x, y: y - x)

    def __rmul__(self, other):
        return self.__op(other, lambda x, y: y * x)

    def __rtruediv__(self, other):
        return self.__op(other, lambda x, y: y / (x or decimal_number(1e-9)))

    def __rfloordiv__(self, other):
        return self.__op(other, lambda x, y: y // (x or decimal_number(1e-9)))

    def __rmod__(self, other):
        return self.__op(other, lambda x, y: y % (x or decimal_number(1e-9)))

    def __rpow__(self, other):
        return self.__op(other, lambda x, y: y ** x)

    def list(self):
        return list(self._list)


quote_coins = frozenset({
    'USDT', 'USD', 'USDC', 'PERP', 'USDE', 'EUR', 'BRL', 'BTC', 'ETH', 'DAI', 'BRZ', 'FDUSD'
})


def get_symbol(contract: str):
    global quote_coins
    market_type = 'spot'
    symbol = ''.join(x for x in contract.upper() if x.isalnum() or x in '/-:').split('/')
    if len(symbol) == 1:
        symbol = symbol[0]
        for coin in quote_coins:
            if symbol.endswith(coin):
                market_type = 'linear'
                return [symbol[:symbol.rfind(coin)] or symbol, coin if coin != 'PERP' else 'USDC', market_type]
        return []
    base_coin = symbol[0]
    quote_base_coin = symbol[1]
    p = quote_base_coin.find(':')
    if p != -1:
        quote_coin = quote_base_coin[p + 1:]
        quote_base_coin = quote_base_coin[:p]
        if quote_coin.startswith(base_coin) and not quote_coin[len(base_coin):len(base_coin)+1].isalnum():
            market_type = 'inverse'
        else:
            market_type = 'linear'
    return [base_coin, quote_base_coin, market_type]


def get_market_type(contract: str):
    return get_symbol(contract)[-1]


def get_trading_view_url(contract: str):
    try:
        base_coin, quote_coin, market_type = get_symbol(contract)
    except:
        return ''
    if market_type == 'spot':
        return f"https://ru.tradingview.com/symbols/{base_coin}{quote_coin}/?exchange=BYBIT"
    elif market_type == 'linear' or market_type == 'inverse':
        return f"https://ru.tradingview.com/symbols/{base_coin}{quote_coin}.P/?exchange=BYBIT"
    return ''


def get_exchange_trade_url(contract: str):
    global quote_coins
    try:
        base_coin, quote_coin, market_type = get_symbol(contract)
    except:
        return ''
    if market_type == 'spot':
        return f"https://www.bybit.com/trade/spot/{base_coin}/{quote_coin}"
    elif market_type == 'linear':
        if quote_coin == 'USDT':
            return f"https://www.bybit.com/trade/usdt/{base_coin}{quote_coin}"
        for coin in quote_coins:
            if coin == quote_coin:
                if quote_coin == 'USDC':
                    quote_coin = 'PERP'
                return f"https://www.bybit.com/trade/futures/{coin.lower()}/{base_coin}-{quote_coin}"
    elif market_type == 'inverse':
        return f"https://www.bybit.com/trade/inverse/{base_coin}{quote_coin}"
    return ''


def strip_tags(string: str):
    in_tag = False
    result = ''
    prev = ''
    for x in string:
        if prev != '\\' and x == '>':
            in_tag = False
        elif prev != '\\' and x == '<':
            in_tag = True
        elif not in_tag:
            result += x
        prev = x
    return result


def format_si_number(number: Union[int, float, Decimal], *,
                     multiple_min: Union[int, float, Decimal, None, ...] = ...,
                     submultiple_max: Union[int, float, Decimal, None, ...] = ...,
                     allowed: Union[set, None] = None,
                     ignored: Union[set, None] = None):
    values = [
        (10 ** 30, 'Q'), (10 ** 27, 'R'), (10 ** 24, 'Y'),
        (10 ** 21, 'Z'), (10 ** 18, 'E'), (10 ** 15, 'P'),
        (10 ** 12, 'T'), (10 ** 9, 'G'), (10 ** 6, 'M'),
        (10 ** 3, 'k'), (10 ** 2, 'h'), (10 ** 1, 'da'),
        (10 ** (-30), 'q'), (10 ** (-27), 'r'), (10 ** (-24), 'y'),
        (10 ** (-21), 'z'), (10 ** (-18), 'a'), (10 ** (-15), 'f'),
        (10 ** (-12), 'p'), (10 ** (-9), 'n'), (10 ** (-6), 'μ'),
        (10 ** (-3), 'm'), (10 ** (-2), 'c'), (10 ** (-1), 'd'),
    ]
    if multiple_min is ...:
        multiple_min = 1
    elif multiple_min is None:
        multiple_min = max(values, key=lambda x: x[0])[0] * 10
    if submultiple_max is ...:
        submultiple_max = 1
    elif submultiple_max is None:
        submultiple_max = min(values, key=lambda x: x[0])[0] / 10
    if allowed is None:
        allowed = {v for k, v in values}
    if ignored is None:
        ignored = set()
    for value, symbol in values:
        if symbol not in allowed or symbol in ignored:
            continue
        if 1 <= multiple_min <= value <= abs(number) or 1 >= submultiple_max >= value >= abs(number):
            number /= value
            return number, symbol
    return number, ''


def make_brownian_motion(*,
                         date_from_ts,
                         timeframe,
                         count,
                         mu=0.,
                         sigma=1.):
    timeframe_seconds = int(TimeStamp.convert_timeframe_to_seconds(timeframe))
    if count <= 1:
        return []
    m = 60 if count < 10000 else 6
    n_points = m * (count - 1)
    interval = [0, 10]
    dt = (interval[1] - interval[0]) / (n_points - 1)
    z = [[random.normalvariate(mu, sigma) for _ in range(n_points)] for _ in range(2)]
    w = [[0 for _ in range(n_points)] for _ in range(2)]
    for idx in range(len(w[0]) - 1):
        real_idx = idx + 1
        for i in range(len(w)):
            w[i][real_idx] = w[i][real_idx - 1] + (dt ** 0.5) * z[i][idx]
    min_value = abs(min(w[i][j] for i in range(len(w)) for j in range(len(w[i])))) + 1
    for i in range(len(w)):
        for j in range(len(w[i])):
            w[i][j] += min_value
    timestamp = int(date_from_ts)
    tohlcv = []
    for j in range(0, len(w[0]), m):
        ohlc_numbers = w[0][j:j + m]
        volume_numbers = w[1][j:j + m]
        open = ohlc_numbers[0] if not tohlcv else tohlcv[-1][4]
        high = max(ohlc_numbers)
        low = min(ohlc_numbers)
        close = ohlc_numbers[-1]
        volume = sum(volume_numbers)
        tohlcv.append([
            timestamp,
            open,
            high,
            low,
            close,
            volume
        ])
        timestamp += timeframe_seconds * 1000
    return tohlcv
