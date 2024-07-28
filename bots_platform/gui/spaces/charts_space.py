from nicegui import ui
from typing import Union
from datetime import timedelta
from copy import deepcopy
import traceback
import json
import os

from bots_platform.gui.spaces import Columns
from bots_platform.model import ExchangeModel
from bots_platform.model.utils import get_exchange_trade_url, get_trading_view_url, TimeStamp, decimal_number


class ChartsSpace:
    UPDATE_BUTTON = 'UPDATE_BUTTON'
    CHARTS_BOX = 'CHARTS_BOX'

    def __init__(self):
        self._exchange_model: Union[ExchangeModel, None] = None
        self._charts_space = None
        self._elements = dict()
        self._constructed = False
        self._fetch_options = {
            'OHLCV': ExchangeModel.fetch_ohlcv,
            'MARK': ExchangeModel.fetch_mark_ohlcv,
            'INDEX': ExchangeModel.fetch_index_ohlcv,
            'PREMIUM_INDEX': ExchangeModel.fetch_premium_index_ohlcv,
        }
        self._timeframes = [
            '1m', '3m', '5m', '15m', '30m',
            '1h', '2h', '4h', '6h', '12h',
            '1d', '1w', '1M',
        ]
        self._markets_symbols = set()
        self._charts = []
        self._theme = dict()
        self._load_theme()

    async def init(self):
        self._elements.clear()
        if self._charts_space:
            self._charts_space.delete()
        self._charts_space = ui.card().classes('items-center')
        await self.update()
        self._constructed = True

    async def update(self):
        notification = ui.notification(timeout=8, close_button=True)
        notification.message = 'Updating charts...'
        notification.spinner = True

        async def update_charts_callback():
            if self._constructed:
                await self.update()

        async def add_chart_callback():
            if self._constructed:
                try:
                    await self.add_chart()
                except BaseException:
                    traceback.print_exc()
                await self.update()

        with self._charts_space:

            if ChartsSpace.UPDATE_BUTTON not in self._elements:
                update_button = ui.button('Update',
                                          on_click=lambda *_: update_charts_callback()).classes('m-auto')
                self._elements[ChartsSpace.UPDATE_BUTTON] = update_button

            if ChartsSpace.CHARTS_BOX not in self._elements:
                ui.button('Add chart', on_click=lambda *_: add_chart_callback()).classes('m-auto')
                charts_box = ui.column().classes('w-full items-center')
                self._elements[ChartsSpace.CHARTS_BOX] = charts_box

            await self.update_charts()

        notification.spinner = False
        notification.dismiss()

    @staticmethod
    def __validate_datestr(x):
        if len(x) != 10:
            return 'YYYY-mm-dd'
        try:
            TimeStamp.parse_date(x, utc=True)
        except:
            return 'Invalid date'

    async def add_chart(self,
                        symbol='',
                        timeframe='1m',
                        date_from_timestamp: Union[int, None, ...] = None,
                        date_to_timestamp: Union[int, None, ...] = None,
                        side=None,
                        price=None,
                        block=False):

        async def update_chart_callback():
            await self._update_chart(symbol_input, fetch_input,
                                     timeframe_input, chart,
                                     date_from, date_to)

        def exchange_callback():
            nonlocal symbol_input
            v = symbol_input.value
            if v in self._markets_symbols:
                ui.navigate().to(get_exchange_trade_url(v), new_tab=True)
            else:
                ui.notify('Market symbol not found!', close_button=True, type='warning')

        def trading_view_callback():
            nonlocal symbol_input
            v = symbol_input.value
            if v in self._markets_symbols:
                ui.navigate().to(get_trading_view_url(v), new_tab=True)
            else:
                ui.notify('Market symbol not found!', close_button=True, type='warning')

        def symbol_input_on_change(e):
            nonlocal symbol_input
            v = symbol_input.value
            v_upper = symbol_input.value.upper()
            if v != v_upper:
                symbol_input.set_value(v_upper)

        def insert_date_input(string, str_date):
            with ui.input(string, validation=ChartsSpace.__validate_datestr) as date_input:
                with ui.menu().props('no-parent-event') as menu:
                    with ui.date().bind_value(date_input):
                        with ui.row().classes('justify-end'):
                            ui.button('Close', on_click=menu.close).props('flat')
                with date_input.add_slot('append'):
                    ui.icon('edit_calendar').on('click', menu.open).classes('cursor-pointer')
                date_input.set_value(str_date)
            return date_input

        if ChartsSpace.CHARTS_BOX in self._elements:
            try:
                markets_symbols = await self._exchange_model.fetch_markets_symbols()
            except:
                return
            self._markets_symbols = markets_symbols
            autocomplete = list(self._markets_symbols)
            charts_box = self._elements[ChartsSpace.CHARTS_BOX]
            with charts_box:
                chart_box = ui.column().classes('w-full items-center')
                with chart_box:
                    with ui.row():
                        in_row_style = 'margin: auto auto;'
                        ui.button('TradingView', on_click=trading_view_callback, color='black').style(in_row_style)
                        ui.button('Bybit', on_click=exchange_callback, color='black').style(in_row_style)
                        symbol_input = ui.input('Symbol',
                                                value=symbol,
                                                autocomplete=autocomplete,
                                                on_change=symbol_input_on_change,
                                                validation=lambda x: None if x in self._markets_symbols else 'Not found')
                        previous_dt = int((TimeStamp.get_utc_dt_from_now() - timedelta(days=1)).timestamp())
                        previous_dt = TimeStamp.convert_utc_to_local_timestamp(previous_dt)
                        previous_dt = TimeStamp.get_utc_dt_from_timestamp(previous_dt)
                        current_dt = int(TimeStamp.get_utc_dt_from_now().timestamp())
                        current_dt = TimeStamp.convert_utc_to_local_timestamp(current_dt)
                        current_dt = TimeStamp.get_utc_dt_from_timestamp(current_dt)
                        b11, b12 = date_from_timestamp is None, date_to_timestamp is None
                        b21, b22 = date_from_timestamp is ..., date_to_timestamp is ...
                        if b11 and b12:
                            str_date_from = TimeStamp.format_date(previous_dt)
                            str_date_to = TimeStamp.format_date(current_dt)
                        elif b11:
                            if b22:
                                date_to_timestamp = current_dt.timestamp()
                            str_date_from = str_date_to = TimeStamp.format_date(
                                TimeStamp.get_utc_dt_from_timestamp(date_to_timestamp))
                        elif b12:
                            if b21:
                                date_from_timestamp = current_dt.timestamp()
                            str_date_to = str_date_from = TimeStamp.format_date(
                                TimeStamp.get_utc_dt_from_timestamp(date_from_timestamp))
                        else:
                            if b21:
                                date_from_timestamp = current_dt.timestamp()
                            if b22:
                                date_to_timestamp = current_dt.timestamp()
                            if date_from_timestamp > date_to_timestamp:
                                date_to_timestamp = date_from_timestamp
                            str_date_from = TimeStamp.format_date(
                                TimeStamp.get_utc_dt_from_timestamp(date_from_timestamp))
                            str_date_to = TimeStamp.format_date(
                                TimeStamp.get_utc_dt_from_timestamp(date_to_timestamp))
                        date_from = insert_date_input('From', str_date_from)
                        date_to = insert_date_input('To', str_date_to)
                        fetch_input = ui.select(options=sorted(self._fetch_options),
                                                value='OHLCV')
                        timeframe_input = ui.select(options=self._timeframes,
                                                    value=timeframe)
                        if not block:
                            ui.button('Fetch', on_click=update_chart_callback).style(in_row_style)
                    chart = ui.highchart(deepcopy(Columns.STOCK_CHART),
                                         type='stockChart',
                                         extras=['stock', 'accessibility']
                                         ).style("width:1000px;height:700px;")
                    self._set_theme(chart.options)
                    chart.update()
                    dft = date_from_timestamp
                    chart_data_object = [symbol_input, fetch_input,
                                         timeframe_input, chart,
                                         date_from, date_to, side, price, dft]
                    if block:
                        symbol_input.disable()
                        fetch_input.disable()
                        date_to.disable()
                    self._charts.append(chart_data_object)
            return chart_data_object

    async def update_chart(self, chart_data_object):
        (symbol_input, fetch_input, timeframe_input,
         chart, date_from, date_to, side, price, dft) = chart_data_object
        await self._update_chart(symbol_input, fetch_input,
                                 timeframe_input, chart,
                                 date_from, date_to, side, price, dft)

    async def update_charts(self):
        for x in self._charts:
            (symbol_input, fetch_input, timeframe_input,
             chart, date_from, date_to, side, price, dft) = x
            await self._update_chart(symbol_input, fetch_input,
                                     timeframe_input, chart,
                                     date_from, date_to, side, price, dft)

    def check(self):
        if self._charts_space is None or self._exchange_model is None:
            raise Exception(f'{type(self).__name__} is not initialized')

    def set_exchange_model(self, model: ExchangeModel):
        self._exchange_model = model

    def detach(self):
        try:
            self._charts_space.delete()
        except:
            pass
        self._constructed = False
        self._elements.clear()
        self._charts_space = None

    async def _fetch_chart_data(self,
                                symbol,
                                timeframe,
                                date_from_timestamp,
                                date_to_timestamp,
                                tohlc,
                                volumes,
                                fetch_func):
        candles = TimeStamp.get_number_of_candles(timeframe,
                                                  date_from_timestamp,
                                                  date_to_timestamp)
        candles_needed = candles - len(tohlc) + bool(len(tohlc) == candles)
        if candles_needed == 0:
            return
        full_data = []
        current_timestamp = TimeStamp.convert_local_to_utc_timestamp(
            tohlc[-1][0] if tohlc else date_from_timestamp)
        while True:
            data = await fetch_func(self._exchange_model, symbol,
                                    timeframe=timeframe,
                                    since=current_timestamp,
                                    limit=candles_needed)
            if not full_data and not tohlc and date_from_timestamp < data[0][0]:
                date_from_timestamp = data[0][0]
                candles = TimeStamp.get_number_of_candles(timeframe,
                                                          date_from_timestamp,
                                                          date_to_timestamp)
                candles_needed = candles - len(tohlc) + bool(len(tohlc) == candles)
                if candles_needed == 0:
                    return
                continue
            if not len(data):
                break
            full_data.extend(data)
            candles_needed -= len(data)
            if candles_needed <= 0:
                break
            timestamp = current_timestamp
            current_timestamp = data[-1][0]
            if timestamp == current_timestamp:
                break
        tmp_data = []
        for x in full_data:
            if not tmp_data or tmp_data[-1][0] < x[0]:
                tmp_data.append(x)
        full_data = tmp_data
        new_tohlc = []
        new_volumes = []
        for x in full_data:
            timestamp, *ohlcv = x
            timestamp = TimeStamp.convert_utc_to_local_timestamp(timestamp)
            open, high, low, close, volume = [decimal_number(x) for x in ohlcv]
            new_tohlc.append([timestamp, open, high, low, close])
            new_volumes.append([timestamp, volume])
        if tohlc and full_data and tohlc[-1][0] == new_tohlc[0][0]:
            tohlc.pop(-1)
            volumes.pop(-1)
        tohlc.extend(new_tohlc)
        volumes.extend(new_volumes)
        return date_from_timestamp

    async def _update_chart(self,
                            symbol_input: ui.input,
                            fetch_input: ui.select,
                            timeframe_input: ui.select,
                            chart: ui.chart,
                            date_from: ui.input,
                            date_to: ui.input,
                            side=None,
                            price=None,
                            dft=None):
        fetch_option = fetch_input.value
        fetch_func = self._fetch_options[fetch_option]
        symbol = symbol_input.value.upper()
        timeframe = timeframe_input.value
        date_from_str = date_from.value
        date_to_str = date_to.value
        if (not fetch_func or
            not timeframe or
            symbol not in self._markets_symbols or
            ChartsSpace.__validate_datestr(date_from_str) is not None or
            ChartsSpace.__validate_datestr(date_to_str) is not None):
            return
        dtimestamp = int(TimeStamp.parse_date(date_from_str, utc=True).timestamp())
        date_from_timestamp = TimeStamp.convert_utc_to_local_timestamp(dtimestamp) * 1000
        dtimestamp = int((TimeStamp.parse_date(date_to_str, utc=True) + timedelta(days=1)).timestamp())
        date_to_timestamp = TimeStamp.convert_utc_to_local_timestamp(dtimestamp) * 1000
        dft = TimeStamp.convert_utc_to_local_timestamp(dft)
        try:
            tohlc = chart.options['series'][0]['data']
            entry_price_series = chart.options['series'][1]['data']
            current_price_series = chart.options['series'][2]['data']
            volumes = chart.options['series'][3]['data']
            parameters = chart.options['parameters']
            if (parameters['symbol'] != symbol or
                parameters['fetch_option'] != fetch_option or
                parameters['timeframe'] != timeframe or
                parameters['date_from_timestamp'] != date_from_timestamp or
                parameters['date_to_timestamp'] != date_to_timestamp):
                tohlc.clear()
                volumes.clear()
                parameters['real_date_from_timestamp'] = date_from_timestamp
            real_date_from_timestamp = parameters['real_date_from_timestamp']
            real_date_from_timestamp = await self._fetch_chart_data(
                symbol,
                timeframe,
                real_date_from_timestamp,
                date_to_timestamp,
                tohlc,
                volumes,
                fetch_func
            )
            parameters['symbol'] = symbol
            parameters['fetch_option'] = fetch_option
            parameters['timeframe'] = timeframe
            parameters['real_date_from_timestamp'] = real_date_from_timestamp
            parameters['date_from_timestamp'] = date_from_timestamp
            parameters['date_to_timestamp'] = date_to_timestamp
            chart.options['series'][0]['name'] = f"{symbol} ({fetch_option})"
            chart.options['title']['text'] = f"{symbol} ({fetch_option})"
            if tohlc:
                all_indicators = []
                cpi = deepcopy(Columns.CURRENT_PRICE_INDICATOR)
                cpi[0]['value'] = current_price = decimal_number(tohlc[-1][-1])
                current_price_series.clear()
                current_price_series.append([tohlc[-1][0], current_price])
                if price is not None and side is not None:
                    entry_price = decimal_number(price)
                    entry_price_series.clear()
                    entry_price_series.append([dft, entry_price])
                    green = '#b9ee67'
                    red = '#ee67b9'
                    if (side.lower() == 'long' and entry_price < current_price or
                            side.lower() == 'short' and entry_price > current_price):
                        cpi[0]['color'] = green
                    else:
                        cpi[0]['color'] = red
                    epi = deepcopy(Columns.ENTRY_PRICE_INDICATOR)
                    epi[0]['value'] = entry_price
                    all_indicators.extend(epi)
                all_indicators.extend(cpi)
                chart.options['yAxis'][0]['plotLines'] = all_indicators
            chart.update()
        except BaseException:
            traceback.print_exc()

    def _load_theme(self):
        try:
            filename = os.path.join(os.path.dirname(__file__), "high_contrast_dark_theme.json")
            with open(filename, 'r+', encoding='utf-8') as fp:
                self._theme = json.load(fp)
        except BaseException:
            traceback.print_exc()

    def _set_theme(self, options: dict):
        tmp = [[options, self._theme]]
        while tmp:
            item, tail = tmp.pop()
            if isinstance(item, dict) and isinstance(tail, dict):
                for k, v in tail.items():
                    if k in item:
                        tmp.append([item[k], tail[k]])
                    else:
                        item[k] = tail[k]
            elif isinstance(item, list) and isinstance(tail, list):
                for v in tail:
                    if v not in item:
                        item.append(v)
            elif isinstance(item, list) and isinstance(tail, dict):
                for x in item:
                    tmp.append([x, tail])
