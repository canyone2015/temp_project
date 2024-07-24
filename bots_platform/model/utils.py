from typing import Union
from decimal import Decimal
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
