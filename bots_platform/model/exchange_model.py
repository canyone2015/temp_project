from decimal import Decimal
from typing import Union
from urllib.request import Request, urlopen
from threading import RLock
from collections import defaultdict
import ccxt
import asyncio
import traceback
import json
import re

from bots_platform.model.logger import Logger
from bots_platform.model.utils import TimeStamp, get_symbol, format_si_number


class MarginModes:
    ISOLATED = 'isolated'
    CROSS = 'cross'
    PORTFOLIO = 'portfolio'


class ExchangeModel:
    def __init__(self):
        self.logger = Logger()
        self._exchange = None
        self._config = None
        self._api_key = None
        self._api_secret = None
        self._is_testnet = None
        self._connection: Union[ccxt.bybit, None] = None
        self._base_fee = Decimal('0.001')
        self._margin_mode = ''
        self._unified_account = False
        self._ms_index_cache = dict()
        self._ms_index_cache_ts = 0
        self._stop_types = frozenset({'Close', 'Settle', 'Stop', 'Take', 'Liq', 'TakeOver', 'Adl'})
        self._positions_markers = None
        self._closed_orders_data = None
        self.__lock = RLock()
        self.__alt_coin_index_regex = re.compile(r'>\s*?(\d+?)\s*?<')

    async def connect(self,
                      exchange: str,
                      api_key: str,
                      api_secret: str,
                      is_testnet: bool,
                      **config_parameters):
        with self.__lock:
            try:
                self._exchange = exchange
                self._api_key = api_key
                self._api_secret = api_secret
                self._is_testnet = is_testnet
                self._config = {
                    'apiKey': self._api_key,
                    'secret': self._api_secret,
                }
                self._config.update(config_parameters)
                self._connection = getattr(ccxt, self._exchange)(self._config)
                if self._is_testnet:
                    self._connection.enable_demo_trading(True)
                await self._async_run(self._connection.fetch_balance)
            except BaseException as e:
                self._exchange = None
                self._connection = None
                traceback.print_exc()
                self.logger.log(*e.args)
                raise
            self.logger.log('Connected!')

    def reconnect(self):
        with self.__lock:
            self.disconnect()
            self.connect(exchange=self._exchange,
                         api_key=self._api_key,
                         api_secret=self._api_secret,
                         is_testnet=self._is_testnet)
            self.logger.log('Reconnected!')

    def disconnect(self):
        with self.__lock:
            self._exchange = None
            self._config = dict()
            self._api_key = ''
            self._api_secret = ''
            self._is_testnet = False
            self._margin_mode = ''
            self._unified_account = False
            self._ms_index_cache = dict()
            self._ms_index_cache_ts = 0
            self.logger.log('Disconnected!')

    async def _async_run(self, func, *args):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, func, *args)

    def check_connection(self):
        with self.__lock:
            if self._connection is None or self._exchange is None:
                raise Exception('There is no connection.')

    def get_base_fee(self):
        return self._base_fee

    def get_margin_mode(self):
        return self._margin_mode

    @staticmethod
    def get_margin_modes():
        return [MarginModes.ISOLATED, MarginModes.CROSS, MarginModes.PORTFOLIO]

    def is_unified_account(self):
        return self._unified_account

    async def switch_margin_mode(self, *, new_margin_mode=None):
        self.check_connection()
        try:
            if new_margin_mode is None:
                if self._margin_mode == MarginModes.ISOLATED:
                    self._connection.set_margin_mode(MarginModes.CROSS)
                    return MarginModes.CROSS
                elif self._margin_mode == MarginModes.CROSS:
                    self._connection.set_margin_mode(MarginModes.ISOLATED)
                    return MarginModes.ISOLATED
                elif self._margin_mode == MarginModes.PORTFOLIO:
                    self._connection.set_margin_mode(MarginModes.CROSS)
                    return MarginModes.CROSS
            else:
                self._connection.set_margin_mode(new_margin_mode)
            self.logger.log(f'Margin mode switched to \"{new_margin_mode}\"!')
        except BaseException as e:
            traceback.print_exc()
            self.logger.log(*e.args)
            raise
        return new_margin_mode

    async def upgrade_unified_trade_account(self):
        self.check_connection()
        try:
            self._connection.upgrade_unified_trade_account()
            self.logger.log(f'Unified trade account is upgraded, wait a minute!')
        except BaseException as e:
            traceback.print_exc()
            self.logger.log(*e.args)
            raise

    async def fetch_market_statistics(self, use_cache=True):

        async def load(url: str, headers: dict):
            request_site = Request(url, headers=headers)
            data = await self._async_run(urlopen, request_site)
            return data.read().decode('utf-8')

        def parse_json_line(string: str, *, is_array: bool = False):
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

        def Fn(number):
            number, prefix = format_si_number(number, multiple_min=1_000_000, submultiple_max=None)
            format_string = '{0' + ':.2f' * bool(number % 1 != 0) + '}{1}'
            return format_string.format(number, prefix)

        def Fd(number):
            number, prefix = format_si_number(number, multiple_min=1_000_000, submultiple_max=None)
            format_string = '${0' + ':.2f' * bool(number % 1 != 0) + '}{1}'
            return format_string.format(number, prefix)

        def Fp(number):
            number, prefix = format_si_number(number, multiple_min=1_000_000, submultiple_max=5e-4)
            format_string = '{0' + ':.2f' * bool(number % 1 != 0) + '}{1}%'
            return format_string.format(number, prefix)

        def Fps(number):
            number, prefix = format_si_number(number, multiple_min=1_000_000, submultiple_max=5e-4)
            format_string = '{0' + ':+.2f' * bool(number % 1 != 0) + '}{1}%'
            return format_string.format(number, prefix)

        headers = {"User-Agent": "Mozilla/5.0"}
        statistics: defaultdict = defaultdict(lambda: '')
        try:
            if use_cache and self._ms_index_cache:
                now_timestamp = TimeStamp.get_local_dt_from_now().timestamp()
                n_seconds = 30
                if now_timestamp < self._ms_index_cache_ts + n_seconds:
                    return self._ms_index_cache

            try:
                main_statistics_url = 'https://coinmarketcap.com/charts/'
                text = await load(main_statistics_url, headers)
                start_text = '"topCryptos"'
                p = text.find(start_text)
                p_text = text[p + len(start_text):]
                data = [x['symbol']
                        for x in json.loads(parse_json_line(p_text, is_array=True))
                        if not x['symbol'].lower().startswith('other')]
                statistics['top_cryptos'] = data
            except:
                statistics['top_cryptos'] = []

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
                text = await load(alt_coin_index_url, headers)
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
            datetime_fstring = TimeStamp.format_time(local_dt)
            cryptocurrencies_fstring = f"{Fn(statistics['cryptocurrencies'])}"
            markets_fstring = f"{Fn(statistics['markets'])}"
            active_exchanges_fstring = f"{Fn(statistics['active_exchanges'])}"
            market_cap_fstring = f"{Fd(statistics['market_cap'])} ({Fps(statistics['market_cap_24h_change'])}); " +\
                                 f"{Fd(statistics['defi_market_cap'])}"
            volume_24h_fstring = f"{Fn(statistics['volume_24h'])} ({Fps(statistics['volume_24h_change'])}); " +\
                                 f"{Fn(statistics['stablecoin_volume_24h'])} ({Fps(statistics['stablecoin_volume_24h_change'])}); " +\
                                 f"{Fn(statistics['defi_volume_24h'])} ({Fps(statistics['defi_volume_24h_change'])}); " +\
                                 f"{Fn(statistics['derivatives_volume_24h'])} ({Fps(statistics['derivatives_volume_24h_change'])})"
            dominance_fstring = f"{Fp(statistics['btc_dominance'])} ({Fps(statistics['btc_dominance_24h_change'])}); " +\
                                f"{Fp(statistics['eth_dominance'])}"
            fear_greed_index_fstring = f"{Fn(statistics['fear_greed_index_value'])} ({statistics['fear_greed_index_name']})"
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
            self._ms_index_cache = statistics
            self._ms_index_cache_ts = datetime_timestamp
            return self._ms_index_cache
        except BaseException as e:
            traceback.print_exc()
            self.logger.log(*e.args)
            raise

    async def fetch_balance(self):
        self.check_connection()
        balance_dict = dict()
        try:
            balance = await self._async_run(self._connection.fetch_balance)
            balance: dict = dict(balance)
            if balance['info']['retMsg'] != 'OK':
                raise Exception('Fetching balance error')
            if balance['info']['result']['list'][0]['totalMarginBalance'] == '':
                self._margin_mode = MarginModes.ISOLATED
            else:
                self._margin_mode = MarginModes.CROSS
            _, unified_account = await self._async_run(self._connection.is_unified_enabled)
            self._unified_account = unified_account
            balance_dict['margin_mode'] = self._margin_mode
            balance_dict['unified_account'] = self._unified_account
            balance_dict['coins'] = list()
            for account_balance_list in balance['info']['result']['list']:
                if account_balance_list['accountType'] != 'UNIFIED':
                    continue
                for account_balance in account_balance_list['coin']:
                    coin_name = account_balance['coin']
                    wallet_balance = Decimal(account_balance['walletBalance'] or 0)
                    total_order_im = Decimal(account_balance['totalOrderIM'] or 0)
                    total_position_im = Decimal(account_balance['totalPositionIM'] or 0)
                    locked = total_order_im + total_position_im
                    free = Decimal(account_balance['availableToWithdraw'])
                    if wallet_balance == free:
                        free = wallet_balance - locked
                    total_pnl = Decimal(account_balance['cumRealisedPnl'] or 0)
                    total_pnl = f"{round(total_pnl, 3):+}"
                    pnl = Decimal(account_balance['unrealisedPnl'] or 0)
                    usd_value = Decimal(account_balance['usdValue'] or 0)
                    if round(usd_value, 3) == 0:
                        continue
                    used_coin = f'{round(locked, 6)}{round(pnl, 3):+}' if pnl else f'{round(locked, 6)}'
                    free_coin = f'{round(free, 6)}'
                    total_coin = f'{round(locked + free + pnl, 6)}'
                    locked *= usd_value / (wallet_balance or 1)
                    pnl *= usd_value / (wallet_balance or 1)
                    free *= usd_value / (wallet_balance or 1)
                    used_usd = f'{round(locked, 6)}{round(pnl, 3):+}' if pnl else f'{round(locked, 6)}'
                    free_usd = f'{round(free, 6)}'
                    total_usd = f'{round(locked + free + pnl, 6)}'
                    used_usd_hidden = round(locked + pnl, 6)
                    free_usd_hidden = round(free, 6)
                    total_usd_hidden = round(locked + free + pnl, 6)
                    used_string = f'{used_coin} {coin_name} / ${used_usd}'
                    free_string = f'{free_coin} {coin_name} / ${free_usd}'
                    total_string = f'{total_coin} {coin_name} / ${total_usd}'
                    if not any(x in used_string for x in '123456789'):
                        used_string = '–'
                    if not any(x in free_string for x in '123456789'):
                        free_string = '–'
                    if not any(x in total_string for x in '123456789'):
                        total_string = '–'
                    if any(x in '123456789' for x in used_usd + free_usd):
                        balance_dict['coins'].append({
                            'coin': coin_name,
                            'used_str': used_string,
                            'free_str': free_string,
                            'total_str': total_string,
                            'total_pnl': total_pnl,
                            'used_usd': used_usd_hidden,
                            'free_usd': free_usd_hidden,
                            'total_usd': total_usd_hidden,
                        })
        except BaseException as e:
            traceback.print_exc()
            self.logger.log(*e.args)
            raise
        return balance_dict

    async def fetch_markets(self, filtered_coins=None):
        self.check_connection()
        markets_data = []

        async def fetch_tickers(source_symbols):
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

        try:
            spot_source_symbols = set()
            swap_linear_source_symbols = set()
            swap_inverse_source_symbols = set()
            future_linear_source_symbols = set()
            future_inverse_source_symbols = set()

            markets = await self._async_run(self._connection.fetch_markets)
            markets_info: dict = dict()
            for x in list(markets):
                if x['active'] and not x['option'] and (x['spot'] or x['linear'] or x['inverse']):
                    source_symbol = x['symbol']
                    if filtered_coins and source_symbol not in filtered_coins:
                        continue
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
                    min_leverage = Decimal(x['info'].get('leverageFilter', dict()).get('minLeverage', 0) or 0)
                    max_leverage = Decimal(x['info'].get('leverageFilter', dict()).get('maxLeverage', 0) or 0)
                    min_qty = Decimal(x['info'].get('lotSizeFilter', dict()).get('minOrderQty', 0) or 0)
                    min_notional = Decimal(x['info'].get('lotSizeFilter', dict()).get('minNotionalValue', 0) or 0)
                    maker = Decimal(str(x.get('maker', 0)) or 0)
                    taker = Decimal(str(x.get('taker', 0)) or 0)
                    markets_info[source_symbol] = {
                        'launch_timestamp': launch_timestamp,
                        'min_leverage': min_leverage,
                        'max_leverage': max_leverage,
                        'min_qty': min_qty,
                        'min_notional': min_notional,
                        'maker': maker,
                        'taker': taker,
                    }
            if spot_source_symbols or swap_linear_source_symbols or swap_inverse_source_symbols or\
                    future_linear_source_symbols or future_inverse_source_symbols:
                try:
                    tickers = dict()
                    if spot_source_symbols:
                        tickers, spot_source_symbols = await fetch_tickers(spot_source_symbols)
                    if swap_linear_source_symbols:
                        tmp_tickers, swap_linear_source_symbols = await fetch_tickers(swap_linear_source_symbols)
                        tickers.update(tmp_tickers)
                    if swap_inverse_source_symbols:
                        tmp_tickers, swap_inverse_source_symbols = await fetch_tickers(swap_inverse_source_symbols)
                        tickers.update(tmp_tickers)
                    if future_linear_source_symbols:
                        tmp_tickers, future_linear_source_symbols = await fetch_tickers(future_linear_source_symbols)
                        tickers.update(tmp_tickers)
                    if future_inverse_source_symbols:
                        tmp_tickers, future_inverse_source_symbols = await fetch_tickers(future_inverse_source_symbols)
                        tickers.update(tmp_tickers)
                    for symbol, ticker in tickers.items():
                        symbol_tuple = get_symbol(symbol)
                        close_price_24h = Decimal(ticker['info'].get('lastPrice') or 0)
                        open_price_24h = Decimal(ticker['info'].get('prevPrice24h') or 0)
                        high_price_24h = Decimal(ticker['info'].get('highPrice24h') or 0)
                        low_price_24h = Decimal(ticker['info'].get('lowPrice24h') or 0)
                        open_close_percent = round((close_price_24h / open_price_24h - 1) * 100, 6)
                        low_high_percent = round((high_price_24h / low_price_24h - 1) * 100, 6)
                        volume_24h = Decimal(ticker['info'].get('turnover24h') or 0)
                        vwap = Decimal(ticker.get('vwap', 0) or close_price_24h)
                        last_trend = round((close_price_24h / vwap - 1) * 100, 6)
                        launch_timestamp = 0
                        min_leverage = Decimal(0)
                        max_leverage = Decimal(0)
                        min_qty = Decimal(0)
                        min_notional = Decimal(0)
                        maker = Decimal(0)
                        taker = Decimal(0)
                        if symbol in markets_info:
                            symbol_info = markets_info[symbol]
                            launch_timestamp = int(symbol_info['launch_timestamp'])
                            min_leverage = Decimal(symbol_info['min_leverage'])
                            max_leverage = Decimal(symbol_info['max_leverage'])
                            min_qty = Decimal(symbol_info['min_qty'])
                            min_notional = Decimal(symbol_info['min_notional'])
                            maker = Decimal(symbol_info['maker'])
                            taker = Decimal(symbol_info['taker'])
                        launch_datetime = ''
                        if launch_timestamp:
                            launch_datetime = TimeStamp.format_time(
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
                except BaseException as e:
                    traceback.print_exc()
                    self.logger.log(*e.args)
        except BaseException as e:
            traceback.print_exc()
            self.logger.log(*e.args)
            raise
        return markets_data

    @staticmethod
    def _get_positions_markers(positions_data):
        positions_markers = dict()
        for position in positions_data:
            contracts = Decimal(position['info']['size'] or 0)
            if not contracts:
                continue
            contract = position['info']['symbol']
            side = 'Long' if position['info']['side'] == 'buy' else 'Short'
            value = Decimal(position['info']['positionValue'] or 0)
            leverage = Decimal(position['info']['leverage'] or 1)
            entry_price = Decimal(position['info']['avgPrice'])
            mark_price = Decimal(position['info']['markPrice'])
            positions_markers[(contract, side)] = {
                'contracts': contracts,
                'value': value,
                'leverage': leverage,
                'entry_price': entry_price,
                'mark_price': mark_price
            }
        return positions_markers

    async def fetch_positions(self, *, usdc=True, _save_markers=False, _load_closed_orders_data=False):
        self.check_connection()
        positions = []
        try:
            positions_data = await self._async_run(self._connection.fetch_positions)
            try:
                if usdc:
                    if _load_closed_orders_data:
                        closed_orders = self._closed_orders_data
                    else:
                        closed_orders = await self._async_run(self._connection.fetch_closed_orders)
                    perp_contracts = set()
                    for x in closed_orders:
                        if x['info']['symbol'].endswith('PERP'):
                            perp_contracts.add(x['info']['symbol'])
                    perp_contracts = list(perp_contracts)
                    for symbol in perp_contracts:
                        try:
                            ps = await self._async_run(self._connection.fetch_positions, symbol)
                            positions_data.extend(ps)
                        except BaseException as e:
                            traceback.print_exc()
                            self.logger.log(*e.args)
            except BaseException as e:
                traceback.print_exc()
                self.logger.log(*e.args)
            if _save_markers:
                self._positions_markers = ExchangeModel._get_positions_markers(positions_data)
            for position in positions_data:
                contracts = Decimal(position['info']['size'] or 0)
                if not contracts:
                    continue
                created_timestamp = int(position['info']['createdTime'])
                datetime_string = TimeStamp.format_time(TimeStamp.get_local_dt_from_timestamp(created_timestamp))
                contract = position['info']['symbol']
                value = Decimal(position['info']['positionValue'] or 0)
                real_size = round(value, 4)
                size = f"{contracts}/{real_size}"
                side = 'Long' if position['info']['side'] == 'buy' else 'Short'
                leverage = Decimal(position['info']['leverage'] or 1)
                status = position['info']['positionStatus']
                unrealized_pnl = Decimal(position['info']['unrealisedPnl'] or 0)
                realized_pnl = Decimal(position['info']['cumRealisedPnl'] or 0)
                entry_price = Decimal(position['info']['avgPrice'])
                mark_price = Decimal(position['info']['markPrice'])
                pnl = unrealized_pnl + realized_pnl - mark_price * contracts * self._base_fee
                liquidation_price = Decimal(position['info']['liqPrice'] or 0)
                take_profit_price = Decimal(position['info']['takeProfit'] or 0)
                stop_loss_price = Decimal(position['info']['stopLoss'] or 0)
                tp_sl = f'{take_profit_price or "-"}/{stop_loss_price or "-"}'
                trailing_stop = Decimal(position['info']['trailingStop']) or '-'
                leverage = round(leverage, 2)
                pnl = round(pnl, 4)
                unrealized_pnl = round(unrealized_pnl, 4)
                realized_pnl = round(realized_pnl, 4)
                positions.append({
                    'datetime': datetime_string,
                    'contract': contract,
                    'real_size': real_size,
                    'size': size,
                    'side': side,
                    'leverage': leverage,
                    'status': status,
                    'pnl': pnl,
                    'unrealized_pnl': unrealized_pnl,
                    'realized_pnl': realized_pnl,
                    'entry_price': entry_price,
                    'mark_price': mark_price,
                    'liquidation_price': liquidation_price,
                    'tp_sl': tp_sl,
                    'trailing_stop': trailing_stop,
                })
        except BaseException as e:
            traceback.print_exc()
            self.logger.log(*e.args)
            raise
        return positions

    async def fetch_open_orders(self, *, usdc=True, _load_markers=False, _load_closed_orders_data=False):
        self.check_connection()
        open_orders = []
        try:
            positions_data = []
            if not _load_markers:
                positions_data = await self._async_run(self._connection.fetch_positions)
            open_orders_data = await self._async_run(self._connection.fetch_open_orders)
            try:
                if usdc:
                    if _load_closed_orders_data:
                        closed_orders = self._closed_orders_data
                    else:
                        closed_orders = await self._async_run(self._connection.fetch_closed_orders)
                    perp_contracts = set()
                    for x in closed_orders:
                        if x['info']['symbol'].endswith('PERP'):
                            perp_contracts.add(x['info']['symbol'])
                    perp_contracts = list(perp_contracts)
                    for symbol in perp_contracts:
                        if not _load_markers:
                            try:
                                ps = await self._async_run(self._connection.fetch_positions, symbol)
                                positions_data.extend(ps)
                            except BaseException as e:
                                traceback.print_exc()
                                self.logger.log(*e.args)
                        try:
                            os = await self._async_run(self._connection.fetch_open_orders, symbol)
                            open_orders_data.extend(os)
                        except BaseException as e:
                            traceback.print_exc()
                            self.logger.log(*e.args)
            except BaseException as e:
                traceback.print_exc()
                self.logger.log(*e.args)
            if _load_markers:
                positions_markers = self._positions_markers
            else:
                positions_markers = ExchangeModel._get_positions_markers(positions_data)
            for open_order in open_orders_data:
                contracts = Decimal(open_order['info']['leavesQty'] or 0)
                if not contracts:
                    continue
                symbol = get_symbol(open_order['symbol'])
                if not symbol:
                    continue
                updated_timestamp = int(open_order['info']['updatedTime'])
                datetime_string = TimeStamp.format_time(TimeStamp.get_local_dt_from_timestamp(updated_timestamp))
                contract = open_order['info']['symbol']
                status = open_order['info']['orderStatus']
                take_profit_price = Decimal(open_order['info']['takeProfit'] or 0)
                take_profit_limit_price = Decimal(open_order['info']['tpLimitPrice'] or 0)
                take_profit_trigger = open_order['info']['tpTriggerBy'].replace('Price', '')
                stop_loss_price = Decimal(open_order['info']['stopLoss'] or 0)
                stop_loss_limit_price = Decimal(open_order['info']['slLimitPrice'] or 0)
                stop_loss_trigger = open_order['info']['slTriggerBy'].replace('Price', '')
                trigger_price = Decimal(open_order['info']['triggerPrice'] or 0)
                price = Decimal(trigger_price or open_order['info']['price'] or 0)
                trigger_by = open_order['info']['triggerBy'].replace('Price', '')
                create_type = open_order['info']['createType'].replace('CreateBy', '')
                create_type = create_type.replace('Closing', 'Close')
                if create_type == 'User':
                    create_type = 'Open'
                side = open_order['info']['side']
                stop_order_type = open_order['info']['stopOrderType']
                if stop_order_type or any(x in create_type for x in self._stop_types):
                    side = 'Short' if side == 'Buy' else 'Long'
                else:
                    side = 'Long' if side == 'Buy' else 'Short'
                order_price_type = open_order['info']['orderType']
                order_type = create_type + bool(order_price_type) * (' ' + order_price_type)
                mark_price = entry_price = Decimal(open_order['info']['lastPriceOnCreated'] or price)
                reduce_only = open_order['info']['reduceOnly']
                time_in_force = open_order['info']['timeInForce']
                if time_in_force == 'GTC':
                    time_in_force = 'Good-Till-Canceled'
                elif time_in_force == 'IOC':
                    time_in_force = 'Immediate-Or-Cancel'
                elif time_in_force == 'FOK':
                    time_in_force = 'Fill-Or-Kill'
                leverage = 1
                position_contracts = contracts
                value = contracts * mark_price
                if (contract, side) in positions_markers:
                    marker = positions_markers[(contract, side)]
                    leverage = marker['leverage']
                    mark_price = marker['mark_price']
                    entry_price = marker['entry_price']
                    position_contracts = marker['contracts']
                    value = marker['value']
                real_size = contracts * mark_price
                size = f"{contracts}/{round(real_size, 3)}"
                tp_sl = ''
                if trigger_price:
                    p = (price / entry_price - 1) * contracts / position_contracts * (-1 if side == 'Short' else 1)
                    real_base_value = p * value - mark_price * contracts * self._base_fee
                    tmp = real_base_value / value * 100
                    base_currency = symbol[1].lower()
                    tp_sl = f"{round(tmp, 2):+}% ({round(real_base_value, 2):+} {base_currency})"
                elif any([take_profit_limit_price, take_profit_price, stop_loss_limit_price, stop_loss_price]):
                    if take_profit_limit_price:
                        tmp = (take_profit_limit_price / price - 1) * 100 * (-1 if side == 'Short' else 1)
                        tp_sl = f"{round(tmp, 2):+}% * L ({take_profit_trigger})"
                    elif take_profit_price:
                        tmp = (take_profit_price / price - 1) * 100 * (-1 if side == 'Short' else 1)
                        tp_sl = f"{round(tmp, 2):+}% * L ({take_profit_trigger})"
                    else:
                        tp_sl = "-"
                    if stop_loss_limit_price:
                        tmp = (stop_loss_limit_price / price - 1) * 100 * (-1 if side == 'Short' else 1)
                        tp_sl += f" / {round(tmp, 2):+}% * L ({stop_loss_trigger})"
                    elif stop_loss_price:
                        tmp = (stop_loss_price / price - 1) * 100 * (-1 if side == 'Short' else 1)
                        tp_sl += f" / {round(tmp, 2):+}% * L ({stop_loss_trigger})"
                    else:
                        tp_sl += " / -"
                real_price = price
                price = f"{price} ({trigger_by if trigger_by else 'Last'})"
                open_orders.append({
                    'datetime': datetime_string,
                    'contract': contract,
                    'real_size': real_size,
                    'size': size,
                    'side': side,
                    'order': order_type,
                    'status': status,
                    'real_price': real_price,
                    'price': price,
                    'tp_sl': tp_sl,
                    'reduce_only': reduce_only,
                    'time_in_force': time_in_force,
                })
        except BaseException as e:
            traceback.print_exc()
            self.logger.log(*e.args)
            raise
        return open_orders

    async def fetch_closed_orders(self, *, _save_closed_orders_data=False):
        self.check_connection()
        closed_orders = []
        try:
            closed_orders_data = await self._async_run(self._connection.fetch_closed_orders)
            if _save_closed_orders_data:
                self._closed_orders_data = closed_orders_data

            for closed_order in closed_orders_data:
                contracts = Decimal(closed_order['info']['qty'] or 0)
                if not contracts:
                    continue
                symbol = get_symbol(closed_order['symbol'])
                if not symbol:
                    continue
                created_timestamp = int(closed_order['info']['createdTime'])
                updated_timestamp = int(closed_order['info']['updatedTime'])
                datetime_string = TimeStamp.format_time(TimeStamp.get_local_dt_from_timestamp(updated_timestamp))
                contract = closed_order['info']['symbol']
                status = closed_order['info']['orderStatus']
                average_price = Decimal(closed_order['info']['avgPrice'] or 0)
                trigger_price = Decimal(closed_order['info']['triggerPrice'] or 0)
                price = Decimal(average_price or trigger_price or closed_order['info']['price'] or 0)
                trigger_by = closed_order['info']['triggerBy'].replace('Price', '')
                create_type = closed_order['info']['createType'].replace('CreateBy', '')
                create_type = create_type.replace('Closing', 'Close')
                if create_type == 'User':
                    create_type = 'Open'
                side = closed_order['info']['side']
                stop_order_type = closed_order['info']['stopOrderType']
                is_stop_type = False
                if stop_order_type or any(x in create_type for x in self._stop_types):
                    side = 'Short' if side == 'Buy' else 'Long'
                    is_stop_type = True
                else:
                    side = 'Long' if side == 'Buy' else 'Short'
                order_price_type = closed_order['info']['orderType']
                order_type = create_type + bool(order_price_type) * (' ' + order_price_type)
                mark_price = price
                commission = round(Decimal(closed_order['info']['cumExecFee'] or 0), 4)
                reduce_only = closed_order['info']['reduceOnly']
                time_in_force = closed_order['info']['timeInForce']
                if time_in_force == 'GTC':
                    time_in_force = 'Good-Till-Canceled'
                elif time_in_force == 'IOC':
                    time_in_force = 'Immediate-Or-Cancel'
                elif time_in_force == 'FOK':
                    time_in_force = 'Fill-Or-Kill'
                real_size = contracts * mark_price
                size = f"{contracts}/{round(real_size, 2)}"
                real_price = price
                price = f"{price} ({trigger_by if trigger_by else 'Last'})"
                closed_orders.append({
                    'datetime': datetime_string,
                    'contract': contract,
                    'real_size': real_size,
                    'size': size,
                    'side': side,
                    'order': order_type,
                    'status': status,
                    'real_price': real_price,
                    'price': price,
                    'tp_sl': '',
                    'commission': commission,
                    'reduce_only': reduce_only,
                    'time_in_force': time_in_force,
                    'created_timestamp': created_timestamp,
                    'contracts': contracts,
                    'is_stop_type': is_stop_type,
                    'symbol': symbol
                })
            try:
                closed_orders.sort(key=lambda x: (x['created_timestamp'], x['is_stop_type']))
                d = dict()
                for closed_order in closed_orders:
                    contract = (closed_order['contract'], closed_order['side'])
                    price = closed_order['real_price']
                    side = closed_order['side']
                    contracts = closed_order['contracts']
                    commission = closed_order['commission']
                    real_size = closed_order['real_size']
                    base_currency = closed_order['symbol'][1]
                    if closed_order['is_stop_type']:
                        old_price, old_contracts = d.get(contract, [0, 0])
                        if old_contracts == 0:
                            d[contract] = [0, 0]
                            closed_order['tp_sl'] = '-'
                            continue
                        new_contracts = old_contracts - contracts
                        if new_contracts > 0:
                            d[contract] = [old_price, new_contracts]
                        elif contract in d:
                            d.pop(contract)
                        p = old_price / price
                        real_base_value = real_size * (1 - p) * (-1 if side == 'Short' else 1) - commission
                        tmp = real_base_value * 100 / real_size
                        closed_order['tp_sl'] = f"{round(tmp, 2):+}% ({round(real_base_value, 2):+} {base_currency})"
                    else:
                        old_price, old_contracts = d.get(contract, [0, 0])
                        new_price = (old_price * old_contracts + price * contracts) / (old_contracts + contracts)
                        new_contracts = old_contracts + contracts
                        d[contract] = [new_price, new_contracts]
                        tmp = commission / real_size * 100
                        closed_order['tp_sl'] = f"{-round(tmp, 4):+}% ({-round(commission, 4):+} {base_currency})"
            except Exception as e:
                traceback.print_exc()
                self.logger.log(*e.args)
        except BaseException as e:
            traceback.print_exc()
            self.logger.log(*e.args)
            raise
        return closed_orders

    async def fetch_canceled_orders(self):
        self.check_connection()
        canceled_orders = []
        try:
            canceled_orders_data = await self._async_run(self._connection.fetch_canceled_orders)

            for canceled_order in canceled_orders_data:
                contracts = Decimal(canceled_order['info']['qty'] or 0)
                if not contracts:
                    continue
                symbol = get_symbol(canceled_order['symbol'])
                if not symbol:
                    continue
                updated_timestamp = int(canceled_order['info']['updatedTime'])
                datetime_string = TimeStamp.format_time(TimeStamp.get_local_dt_from_timestamp(updated_timestamp))
                contract = canceled_order['info']['symbol']
                reason = canceled_order['info']['orderStatus']
                cancel_type = canceled_order['info']['cancelType'].replace('CancelBy', '')
                if reason in ('Cancelled', 'Canceled'):
                    if cancel_type == 'UNKNOWN':
                        reason = canceled_order['info']['rejectReason'].replace('EC_', '')
                    else:
                        reason = f"{reason} by {cancel_type}"
                average_price = Decimal(canceled_order['info']['avgPrice'] or 0)
                trigger_price = Decimal(canceled_order['info']['triggerPrice'] or 0)
                price = Decimal(average_price or trigger_price or canceled_order['info']['price'] or 0)
                trigger_by = canceled_order['info']['triggerBy'].replace('Price', '')
                create_type = canceled_order['info']['createType'].replace('CreateBy', '')
                create_type = create_type.replace('Closing', 'Close')
                if create_type == 'User':
                    create_type = 'Open'
                side = canceled_order['info']['side']
                stop_order_type = canceled_order['info']['stopOrderType']
                if stop_order_type or any(x in create_type for x in self._stop_types):
                    side = 'Short' if side == 'Buy' else 'Long'
                else:
                    side = 'Long' if side == 'Buy' else 'Short'
                order_price_type = canceled_order['info']['orderType']
                order_type = create_type + bool(order_price_type) * (' ' + order_price_type)
                mark_price = price
                reduce_only = canceled_order['info']['reduceOnly']
                time_in_force = canceled_order['info']['timeInForce']
                if time_in_force == 'GTC':
                    time_in_force = 'Good-Till-Canceled'
                elif time_in_force == 'IOC':
                    time_in_force = 'Immediate-Or-Cancel'
                elif time_in_force == 'FOK':
                    time_in_force = 'Fill-Or-Kill'
                real_size = contracts * mark_price
                size = f"{contracts}/{round(real_size, 2)}"
                real_price = price
                price = f"{price} ({trigger_by if trigger_by else 'Last'})"
                canceled_orders.append({
                    'datetime': datetime_string,
                    'contract': contract,
                    'real_size': real_size,
                    'size': size,
                    'side': side,
                    'order': order_type,
                    'reason': reason,
                    'real_price': real_price,
                    'price': price,
                    'reduce_only': reduce_only,
                    'time_in_force': time_in_force
                })
        except BaseException as e:
            traceback.print_exc()
            self.logger.log(*e.args)
            raise
        return canceled_orders

    async def fetch_ledger(self):
        self.check_connection()
        ledger_result = []
        try:
            ledger_data = await self._async_run(self._connection.fetch_ledger)

            for ledger in ledger_data:
                transaction_timestamp = int(ledger['info']['transactionTime'])
                datetime_string = TimeStamp.format_time(TimeStamp.get_local_dt_from_timestamp(transaction_timestamp))
                contract = ledger['info']['symbol']
                transaction_type = ledger['info']['type']
                side = ledger['info']['side']
                quantity = Decimal(ledger['info']['qty'] or 0)
                filled_price = Decimal(ledger['info']['tradePrice'] or 0)
                funding = Decimal(ledger['info']['funding'] or 0)
                fee_paid = 0 if funding else Decimal(ledger['info']['feeRate'] or 0) * filled_price * quantity
                cash_flow = Decimal(ledger['info']['cashFlow'] or 0)
                change = Decimal(ledger['info']['change'] or 0)
                cash_balance = Decimal(ledger['info']['cashBalance'] or 0)
                funding = round(funding, 5)
                fee_paid = round(fee_paid, 5)
                change = round(change, 5)
                cash_balance = round(cash_balance, 5)
                ledger_result.append({
                    'datetime': datetime_string,
                    'contract': contract,
                    'type': transaction_type,
                    'side': side,
                    'quantity': quantity,
                    'filled_price': filled_price,
                    'funding': funding,
                    'fee_paid': fee_paid,
                    'cash_flow': cash_flow,
                    'change': change,
                    'cash_balance': cash_balance
                })
        except BaseException as e:
            traceback.print_exc()
            self.logger.log(*e.args)
            raise
        return ledger_result

    async def fetch_all_positions_and_orders(self, usdc=True):
        closed_orders = await self.fetch_closed_orders(_save_closed_orders_data=True)
        positions = await self.fetch_positions(usdc=usdc, _save_markers=True, _load_closed_orders_data=True)
        open_orders = await self.fetch_open_orders(usdc=usdc, _load_markers=True, _load_closed_orders_data=True)
        canceled_orders = await self.fetch_canceled_orders()
        return {
            'positions': positions,
            'open_orders': open_orders,
            'closed_orders': closed_orders,
            'canceled_orders': canceled_orders,
        }
