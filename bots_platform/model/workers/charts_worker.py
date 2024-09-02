from typing import Union
from threading import RLock
import re
import traceback


from bots_platform.model.utils import TimeStamp, ArithOHLCVList
from bots_platform.model.workers import Worker, TradingWorker, MarketsWorker


class ChartsWorker(Worker):
    def __init__(self):
        super().__init__()
        self._lock: RLock = RLock()
        self._trading_worker: Union[TradingWorker, None] = None
        self._markets_worker: Union[MarketsWorker, None] = None
        self.__symbol_pattern = re.compile(r'[A-Z0-9]+?/[A-Z0-9]+(?::[A-Z0-9]+(?:-[0-9]+)?)?|\bRANDOM\b',
                                           flags=re.IGNORECASE)

    def set_trading_worker(self, trading_worker: TradingWorker):
        self._trading_worker = trading_worker

    def set_markets_worker(self, markets_worker: MarketsWorker):
        self._markets_worker = markets_worker

    async def fetch_exchange_contracts(self, *, number_of_seconds_to_update: int = 60):
        await self._markets_worker.fetch_exchange_contracts(
            number_of_seconds_to_update=number_of_seconds_to_update
        )

    def get_contracts(self) -> set:
        return set(self._markets_worker.get_contracts())

    def get_timeframes(self) -> list:
        return list(self._trading_worker.get_timeframes())

    def get_price_types(self) -> list:
        return list(self._trading_worker.get_price_types())

    async def update_chart_data(self, *,
                                contract: str,
                                date_from: int,
                                date_to: int,
                                timeframe: str,
                                price_type,
                                data: list):
        expression = contract.upper()
        symbols = self.__symbol_pattern.findall(expression)
        symbols.sort(key=lambda x: len(x), reverse=True)
        trans = {
            '/': '_', ':': '_', '-': '_',
            '0': '_0', '1': '_1', '2': '_2',
            '3': '_3', '4': '_4', '5': '_5',
            '6': '_6', '7': '_7', '8': '_8', '9': '_9',
        }
        trans = str.maketrans(trans)
        locals_dict = dict()
        for symbol in symbols:
            ts = data[-1]['timestamp'] if data else 0
            tmp_ohlc_data = [[ts] for x in range(len(data))]
            tmp_volume_data = [[ts] for x in range(len(data))]
            try:
                chart_data = await self._aux_update_chart_data(
                    contract=symbol,
                    date_from=date_from,
                    date_to=date_to,
                    timeframe=timeframe,
                    price_type=price_type,
                    ohlc_data=tmp_ohlc_data,
                    volume_data=tmp_volume_data
                )
            except:
                traceback.print_exc()
                continue
            date_from = chart_data['date_from']
            ohlcv = []
            for ohlc, volume in zip(chart_data['ohlc'], chart_data['volume']):
                if len(ohlc) > 1 and len(volume) > 1:
                    ohlcv.append([*ohlc, volume[-1]])
            variable = symbol.translate(trans)
            expression = expression.replace(symbol, variable)
            locals_dict[variable] = ArithOHLCVList(ohlcv)
        r = eval(expression, {}, locals_dict).list()
        first_ts = r and r[0] and r[0][0] or 0
        for i in range(len(data)):
            if data[i]['timestamp'] == first_ts:
                data = data[:i]
                break
        data.extend({
            'timestamp': x[0],
            'open': x[1],
            'high': x[2],
            'low': x[3],
            'close': x[4],
            'volume': x[5] if len(x) >= 6 else 0,
        } for x in r)
        return {
            'date_from': date_from,
            'data': data
        }

    async def _aux_update_chart_data(self,
                                     contract: str,
                                     date_from: int,
                                     date_to: int,
                                     timeframe: str,
                                     price_type,
                                     ohlc_data: list,
                                     volume_data: list):
        date_from = int(TimeStamp.normalize_timestamp(date_from)) * 1000
        date_to = int(TimeStamp.normalize_timestamp(date_to)) * 1000
        ohlc_data, volume_data, real_date_from = await self._trading_worker.fetch_ohlcv(
            contract=contract,
            timeframe=timeframe,
            date_from_timestamp=date_from,
            date_to_timestamp=date_to,
            price_type=price_type,
            old_ohlc_data=ohlc_data,
            old_volume_data=volume_data,
            in_place=True
        )
        return {
            'date_from': real_date_from,
            'ohlc': ohlc_data,
            'volume': volume_data
        }
