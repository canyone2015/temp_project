from typing import Union
from threading import RLock
from collections import defaultdict
from decimal import Decimal
import traceback
import json
import re

from bots_platform.model.utils import TimeStamp, decimal_number, format_si_number, get_symbol
from bots_platform.model.workers import Worker
import ccxt


class MarketsWorker(Worker):
    def __init__(self):
        super().__init__()
        self._global_market_lock: RLock = RLock()
        self._global_market_cache: dict = dict()
        self._global_market_cache_ts: float = 0.
        self._exchange_market_lock: RLock = RLock()
        self._exchange_market_cache: list = list()
        self._exchange_market_cache_ts: float = 0.
        self._contracts_lock: RLock = RLock()
        self._contracts_cache: set = set()
        self._contracts_cache_ts: float = 0.
        self.__alt_coin_index_regex = re.compile(r'>\s*?(\d+?)\s*?<')

    async def force_update_global_market_info(self, *, only_reset=False):

        def parse_json_line(string: str, *, is_array: bool = False) -> str:
            b_start = '{['[is_array]
            b_end = '}]'[is_array]
            depth = 0
            json_line = ''
            for x in string:
                if depth > 0 or x == b_start and depth == 0:
                    json_line += x
                if x == b_start:
                    depth += 1
                elif x == b_end:
                    depth -= 1
                    if depth == 0:
                        break
            return json_line

        def Fn(number: Union[int, float, Decimal]) -> str:  # number
            number = float(number)
            number, prefix = format_si_number(number, multiple_min=1_000_000, submultiple_max=None)
            number = int(number) if number % 1 == 0 else round(number, 2)
            return f"{number}{prefix}"

        def Fd(number: Union[int, float, Decimal]) -> str:  # dollars
            number = float(number)
            number, prefix = format_si_number(number, multiple_min=1_000_000, submultiple_max=None)
            number = int(number) if number % 1 == 0 else round(number, 2)
            return f"${number}{prefix}"

        def Fp(number: Union[int, float, Decimal]) -> str:  # percent
            number = float(number)
            number, prefix = format_si_number(number, multiple_min=1_000_000, submultiple_max=5e-4)
            number = int(number) if number % 1 == 0 else round(number, 2)
            return f"{number}{prefix}%"

        def Fps(number: Union[int, float, Decimal]) -> str:  # +/- percent
            number = float(number)
            number, prefix = format_si_number(number, multiple_min=1_000_000, submultiple_max=5e-4)
            number = int(number) if number % 1 == 0 else round(number, 2)
            sign = number > 0 and '+' or '-'
            return f"{sign}{abs(number)}{prefix}%"

        self.check()
        headers = {"User-Agent": "Mozilla/5.0"}
        statistics: defaultdict = defaultdict(str)
        try:
            if only_reset:
                with self._global_market_lock:
                    self._global_market_cache_ts = 0
                return
            text = ''
            try:
                main_statistics_url = 'https://coinmarketcap.com/charts/'
                text = await self._load_text(main_statistics_url, headers)
                start_text = '"topCryptos"'
                p = text.find(start_text)
                p_text = text[p + len(start_text):]
                data = [x['symbol']
                        for x in json.loads(parse_json_line(p_text, is_array=True))
                        if not x['symbol'].lower().startswith('other')]
                statistics['top_cryptos'] = data
            except:
                pass

            try:
                start_text = '"globalMetrics"'
                p = text.find(start_text)
                p_text = text[p + len(start_text):]
                data = json.loads(parse_json_line(p_text))
                statistics.update({
                    'cryptocurrencies': data.get('numCryptocurrencies', 0),
                    'markets': data.get('numMarkets', 0),
                    'active_exchanges': data.get('activeExchanges', 0),
                    'market_cap': data.get('marketCap', 0.),  # dollars,
                    'market_cap_24h_change': data.get('marketCapChange', 0.),  # percents,
                    'defi_market_cap': data.get('defiMarketCap', 0.),  # dollars,
                    'stablecoin_volume_24h': data.get('stablecoinVol', 0.),  # dollars,
                    'stablecoin_volume_24h_change': data.get('stablecoinChange', 0.),  # percents,
                    'defi_volume_24h': data.get('defiVol', 0.),  # dollars,
                    'defi_volume_24h_change': data.get('defiChange', 0.),  # percents,
                    'derivatives_volume_24h': data.get('derivativesVol', 0.),  # dollars
                    'derivatives_volume_24h_change': data.get('derivativeChange', 0.),  # percents
                    'volume_24h': data.get('totalVol', 0.),  # dollars
                    'volume_24h_change': data.get('totalVolChange', 0.),  # percents
                    'btc_dominance': data.get('btcDominance', 0.),  # percents
                    'btc_dominance_24h_change': data.get('btcDominanceChange', 0.),  # percents
                    'eth_dominance': data.get('ethDominance', 0.),  # percents
                })
                start_text = '"fearGreedIndexData"'
                p = text.find(start_text)
                p_text = text[p + len(start_text):]
                data = json.loads(parse_json_line(p_text))
                statistics.update({
                    'fear_greed_index_value': data.get('currentIndex', dict()).get('score', 0.),
                    'fear_greed_index_name': data.get('currentIndex', dict()).get('name', 0.),
                    'fear_greed_index_date': data.get('currentIndex', dict()).get('updateTime', 0.)[:10],
                })
            except:
                pass

            try:
                alt_coin_index_url = 'https://www.blockchaincenter.net/en/altcoin-season-index/'
                text = await self._load_text(alt_coin_index_url, headers)
                p = text.find('tab-content altseasoncontent')
                text = text[p:]
                t1 = self.__alt_coin_index_regex.search(text)
                alt_coin_season_index = t1.group(1)
                t2 = self.__alt_coin_index_regex.search(text, t1.end(0))
                alt_coin_month_index = t2.group(1)
                t3 = self.__alt_coin_index_regex.search(text, t2.end(0))
                alt_coin_year_index = t3.group(1)
                statistics.update({
                    'alt_coin_season_index': alt_coin_season_index,
                    'alt_coin_month_index': alt_coin_month_index,
                    'alt_coin_year_index': alt_coin_year_index,
                })
            except:
                pass

            local_dt = TimeStamp.get_local_dt_from_now()
            datetime_timestamp = int(local_dt.timestamp())
            datetime_fstring = TimeStamp.format_datetime(local_dt)
            cryptocurrencies_fstring = f"{Fn(statistics['cryptocurrencies'])}"
            markets_fstring = f"{Fn(statistics['markets'])}"
            active_exchanges_fstring = f"{Fn(statistics['active_exchanges'])}"
            market_cap_fstring = f"{Fd(statistics['market_cap'])} ({Fps(statistics['market_cap_24h_change'])}); " +\
                                 f"{Fd(statistics['defi_market_cap'])}"
            volume_24h_fstring = f"{Fn(statistics['volume_24h'])} ({Fps(statistics['volume_24h_change'])}); " +\
                                 f"{Fn(statistics['stablecoin_volume_24h'])} " +\
                                 f"({Fps(statistics['stablecoin_volume_24h_change'])}); " +\
                                 f"{Fn(statistics['defi_volume_24h'])} " +\
                                 f"({Fps(statistics['defi_volume_24h_change'])}); " +\
                                 f"{Fn(statistics['derivatives_volume_24h'])} " +\
                                 f"({Fps(statistics['derivatives_volume_24h_change'])})"
            dominance_fstring = f"{Fp(statistics['btc_dominance'])} " +\
                                f"({Fps(statistics['btc_dominance_24h_change'])}); " +\
                                f"{Fp(statistics['eth_dominance'])}"
            fear_greed_index_fstring = f"{Fn(statistics['fear_greed_index_value'])} " +\
                                       f"({statistics['fear_greed_index_name']})"
            alt_coin_index_fstring = f"{statistics['alt_coin_season_index']}, " +\
                                     f"{statistics['alt_coin_month_index']}, " +\
                                     f"{statistics['alt_coin_year_index']}"
            top_cryptos_fstring = ', '.join(statistics['top_cryptos'])
            statistics.update({
                'datetime_timestamp': datetime_timestamp,
                'datetime_fstring': datetime_fstring,
                'cryptocurrencies_fstring': cryptocurrencies_fstring,
                'markets_fstring': markets_fstring,
                'active_exchanges_fstring': active_exchanges_fstring,
                'market_cap_fstring': market_cap_fstring,
                'volume_24h_fstring': volume_24h_fstring,
                'dominance_fstring': dominance_fstring,
                'fear_greed_index_fstring': fear_greed_index_fstring,
                'alt_coin_index_fstring': alt_coin_index_fstring,
                'top_cryptos_fstring': top_cryptos_fstring,
            })
            with self._global_market_lock:
                self._global_market_cache = dict(statistics)
                self._global_market_cache_ts = datetime_timestamp
        except BaseException as e:
            traceback.print_exc()
            self._logger.log(*e.args)
            raise

    async def force_update_exchange_market_info(self, *, only_reset=False):

        async def fetch_tickers(source_symbols: Union[list, set, tuple]) -> tuple[dict, set]:
            source_symbols = set(source_symbols)
            while True:
                try:
                    tickers = await self._async_run(self._connection.fetch_tickers, list(source_symbols))
                    break
                except ccxt.BadSymbol as e:
                    s = f'{e}'
                    p = 'market symbol'
                    if p in s:
                        source_symbols.discard(s[s.rfind(p) + len(p):].strip())
            return tickers, source_symbols

        self.check()
        markets_data = []
        try:
            if only_reset:
                with self._exchange_market_lock:
                    self._exchange_market_cache_ts = 0
                return
            contracts = set()
            spot_source_symbols = set()
            swap_linear_source_symbols = set()
            swap_inverse_source_symbols = set()
            future_linear_source_symbols = set()
            future_inverse_source_symbols = set()
            markets = await self._async_run(self._connection.fetch_markets)
            markets_info: dict = dict()
            for x in markets:
                if x['active'] and not x['option'] and (x['spot'] or x['linear'] or x['inverse']):
                    source_symbol = x['symbol']
                    contracts.add(source_symbol)
                    if x['type'] == 'spot':
                        spot_source_symbols.add(source_symbol)
                    elif x['type'] == 'swap' and x['linear']:
                        swap_linear_source_symbols.add(source_symbol)
                    elif x['type'] == 'swap' and x['inverse']:
                        swap_inverse_source_symbols.add(source_symbol)
                    elif x['type'] == 'future' and x['linear']:
                        future_linear_source_symbols.add(source_symbol)
                    elif x['type'] == 'future' and x['inverse']:
                        future_inverse_source_symbols.add(source_symbol)
                    launch_timestamp = int(x['info'].get('launchTime', 0) or 0)
                    min_leverage = decimal_number(
                        x['info'].get('leverageFilter', dict()).get('minLeverage', 0) or 0)
                    max_leverage = decimal_number(
                        x['info'].get('leverageFilter', dict()).get('maxLeverage', 0) or 0)
                    min_qty = decimal_number(x['info'].get('lotSizeFilter', dict()).get('minOrderQty', 0) or 0)
                    min_notional = decimal_number(
                        x['info'].get('lotSizeFilter', dict()).get('minNotionalValue', 0) or 0)
                    maker = decimal_number(str(x.get('maker', 0)) or 0)
                    taker = decimal_number(str(x.get('taker', 0)) or 0)
                    markets_info[source_symbol] = {
                        'launch_timestamp': launch_timestamp,
                        'min_leverage': min_leverage,
                        'max_leverage': max_leverage,
                        'min_qty': min_qty,
                        'min_notional': min_notional,
                        'maker': maker,
                        'taker': taker,
                    }
            if spot_source_symbols or swap_linear_source_symbols or swap_inverse_source_symbols or \
                    future_linear_source_symbols or future_inverse_source_symbols:
                tickers = dict()
                if spot_source_symbols:
                    tickers, spot_source_symbols = await fetch_tickers(
                        spot_source_symbols)
                if swap_linear_source_symbols:
                    tmp_tickers, swap_linear_source_symbols = await fetch_tickers(
                        swap_linear_source_symbols)
                    tickers.update(tmp_tickers)
                if swap_inverse_source_symbols:
                    tmp_tickers, swap_inverse_source_symbols = await fetch_tickers(
                        swap_inverse_source_symbols)
                    tickers.update(tmp_tickers)
                if future_linear_source_symbols:
                    tmp_tickers, future_linear_source_symbols = await fetch_tickers(
                        future_linear_source_symbols)
                    tickers.update(tmp_tickers)
                if future_inverse_source_symbols:
                    tmp_tickers, future_inverse_source_symbols = await fetch_tickers(
                        future_inverse_source_symbols)
                    tickers.update(tmp_tickers)
                for symbol, ticker in tickers.items():
                    symbol_tuple = get_symbol(symbol)
                    close_price_24h = decimal_number(ticker['info'].get('lastPrice') or 0)
                    open_price_24h = decimal_number(ticker['info'].get('prevPrice24h') or 0)
                    high_price_24h = decimal_number(ticker['info'].get('highPrice24h') or 0)
                    low_price_24h = decimal_number(ticker['info'].get('lowPrice24h') or 0)
                    open_close_percent = round((close_price_24h / open_price_24h - 1) * 100, 6)
                    low_high_percent = round((high_price_24h / low_price_24h - 1) * 100, 6)
                    volume_24h = decimal_number(ticker['info'].get('turnover24h') or 0)
                    vwap = decimal_number(ticker.get('vwap', 0) or close_price_24h)
                    last_trend = round((close_price_24h / vwap - 1) * 100, 6)
                    launch_timestamp = 0
                    min_leverage = decimal_number(0)
                    max_leverage = decimal_number(0)
                    min_qty = decimal_number(0)
                    min_notional = decimal_number(0)
                    maker = decimal_number(0)
                    taker = decimal_number(0)
                    if symbol in markets_info:
                        symbol_info = markets_info[symbol]
                        launch_timestamp = int(symbol_info['launch_timestamp'])
                        min_leverage = decimal_number(symbol_info['min_leverage'])
                        max_leverage = decimal_number(symbol_info['max_leverage'])
                        min_qty = decimal_number(symbol_info['min_qty'])
                        min_notional = decimal_number(symbol_info['min_notional'])
                        maker = decimal_number(symbol_info['maker'])
                        taker = decimal_number(symbol_info['taker'])
                    launch_datetime = ''
                    if launch_timestamp:
                        launch_datetime = TimeStamp.format_datetime(
                            TimeStamp.get_local_dt_from_timestamp(launch_timestamp))
                    leverage = ''
                    if min_leverage and max_leverage:
                        leverage = f'{min_leverage}-{max_leverage}'
                    min_size = ''
                    if min_qty and min_notional:
                        min_size = f'{min_qty} {symbol_tuple[0]}/{min_notional} {symbol_tuple[1]}'
                    maker_taker = ''
                    if maker and taker:
                        maker_taker = f'{maker}/{taker}'
                    volume_24h_fstring = '{0:.2f}{1}'.format(*format_si_number(volume_24h,
                                                                               multiple_min=1000,
                                                                               submultiple_max=None))
                    markets_data.append({
                        'type': symbol_tuple[2],
                        'symbol': symbol,
                        'last_trend': last_trend,
                        'open_price_24h': open_price_24h,
                        'high_price_24h': high_price_24h,
                        'low_price_24h': low_price_24h,
                        'close_price_24h': close_price_24h,
                        'open_close_percent': open_close_percent,
                        'low_high_percent': low_high_percent,
                        'volume_24h_fstring': volume_24h_fstring,
                        'volume_24h': volume_24h,
                        'launch_timestamp': launch_timestamp,
                        'launch_datetime': launch_datetime,
                        'min_leverage': min_leverage,
                        'max_leverage': max_leverage,
                        'leverage': leverage,
                        'min_qty': min_qty,
                        'min_notional': min_notional,
                        'min_size': min_size,
                        'maker': maker,
                        'taker': taker,
                        'maker_taker': maker_taker,
                    })
            now_timestamp = TimeStamp.get_local_dt_from_now().timestamp()
            with self._exchange_market_lock:
                self._exchange_market_cache = markets_data
                self._exchange_market_cache_ts = now_timestamp
            with self._contracts_lock:
                self._contracts_cache = contracts
                self._contracts_cache_ts = now_timestamp
        except ccxt.NetworkError as e:
            traceback.print_exc()
            self._logger.log(*e.args)
            await self._connection_aborted_callback()
            return
        except BaseException as e:
            traceback.print_exc()
            self._logger.log(*e.args)
            raise

    async def force_update_contracts_info(self, *, only_reset=False):
        self.check()
        try:
            if only_reset:
                with self._contracts_lock:
                    self._contracts_cache_ts = 0
                return
            markets = await self._async_run(self._connection.fetch_markets)
            contracts = set()
            for x in markets:
                if x['active'] and not x['option'] and (x['spot'] or x['linear'] or x['inverse']):
                    source_symbol = x['symbol']
                    contracts.add(source_symbol)
            now_timestamp = TimeStamp.get_local_dt_from_now().timestamp()
            with self._contracts_lock:
                self._contracts_cache = contracts
                self._contracts_cache_ts = now_timestamp
        except ccxt.NetworkError as e:
            traceback.print_exc()
            self._logger.log(*e.args)
            await self._connection_aborted_callback()
            return
        except BaseException as e:
            traceback.print_exc()
            self._logger.log(*e.args)
            raise

    async def fetch_global_market_info(self, *, force=False, number_of_seconds_to_update=5*60):
        with self._global_market_lock:
            if not force and self._global_market_cache:
                now_timestamp = TimeStamp.get_local_dt_from_now().timestamp()
                n_seconds = number_of_seconds_to_update
                if now_timestamp < self._global_market_cache_ts + n_seconds:
                    return self._global_market_cache
            try:
                await self.force_update_global_market_info()
            except:
                pass
            return self._global_market_cache

    async def fetch_exchange_market_info(self, *, force=False, number_of_seconds_to_update=5*60):
        with self._exchange_market_lock:
            if not force and self._exchange_market_cache:
                now_timestamp = TimeStamp.get_local_dt_from_now().timestamp()
                n_seconds = number_of_seconds_to_update
                if now_timestamp < self._exchange_market_cache_ts + n_seconds:
                    return self._exchange_market_cache
            try:
                await self.force_update_exchange_market_info()
            except:
                pass
            return self._exchange_market_cache

    async def fetch_exchange_contracts(self, *, force=False, number_of_seconds_to_update=5*60) -> set:
        with self._contracts_lock:
            if not force and self._contracts_cache:
                now_timestamp = TimeStamp.get_local_dt_from_now().timestamp()
                n_seconds = number_of_seconds_to_update
                if now_timestamp < self._contracts_cache_ts + n_seconds:
                    return self._contracts_cache
            try:
                await self.force_update_contracts_info()
            except:
                pass
            return self._contracts_cache

    def get_contracts(self):
        with self._contracts_lock:
            return self._contracts_cache


