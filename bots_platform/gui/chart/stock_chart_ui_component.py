from typing import Union, Literal
from copy import deepcopy
import traceback
import json
import os

from nicegui import ui
from bots_platform.gui.chart import ChartUiData
from bots_platform.model.utils import TimeStamp, get_trading_view_url, get_exchange_trade_url


class StockChartUiComponent:
    OHLC_SERIES = 'ohlc'
    VOLUME_SERIES = 'volume'

    def __init__(self):
        self._is_custom = True
        self._theme = None
        self._contracts = set()
        self._timeframes = []
        self._price_types = []
        self._chart_types = ['candlestick', 'ohlc']
        self._update_chart_callback = lambda *_, **__: None
        self.__new_object_contract = {
            'target': ['ohlc', 'volume', 'x'],
            'visual-type': ['marker', 'line', 'marker-and-line', 'box'],
            'object-type': ['entry-price', 'current-price', 'open-order', 'close-order', 'closed-order',
                            'take-profit', 'stop-loss', 'trailing-stop', 'liquidation-price', 'other'],
            'marker-label': '',
            'line-label': '',
            'values': [],
            'marker-color': '',
            'line-color': '',
        }
        self._complex = False

        self._chart_box = None
        self._contract_input = None
        self._date_from_input = None
        self._date_to_input = None
        self._timeframe_select = None
        self._price_type_select = None
        self._chart_type_select = None
        self._fetch_button = None
        self._chart = None

    def create(self, *,
               contract: '',
               date_from_str: str = '',
               date_to_str: str = '',
               timeframe: str = '1m',
               price_type: str = 'OHLCV',
               chart_type: Literal['candlestick', 'ohlc'] = 'candlestick',
               chart_style: str = '',
               complex: bool = False,
               theme_path: Union[str, None] = None):

        def trading_view_triggered(*_):
            v = self._contract_input.value
            if v in self._contracts:
                ui.navigate().to(get_trading_view_url(v), new_tab=True)
            else:
                ui.notify('Market contract not found!', close_button=True, type='warning')

        def exchange_triggered(*_):
            v = self._contract_input.value
            if v in self._contracts:
                ui.navigate().to(get_exchange_trade_url(v), new_tab=True)
            else:
                ui.notify('Market contract not found!', close_button=True, type='warning')

        def contract_input_on_change(*_):
            v = self._contract_input.value
            v_upper = self._contract_input.value.upper()
            if v != v_upper:
                self._contract_input.set_value(v_upper)

        def validate_date_string(x):
            if x == '':
                return
            if len(x) != 10:
                return 'YYYY-mm-dd'
            try:
                TimeStamp.parse_date(x, utc=True)
            except:
                return 'Invalid date'

        def chart_type_changed():
            chart_type = self._chart_type_select.value
            if chart_type in self._chart_types:
                self._chart.options['series'][0]['type'] = chart_type
                self._chart.update()

        def create_date_input(string, default_value):
            with ui.input(string, validation=validate_date_string).props("size=10") as date_input:
                with ui.menu().props('no-parent-event') as menu:
                    with ui.date().bind_value(date_input):
                        with ui.row().classes('justify-end'):
                            ui.button('Close', on_click=menu.close).props('flat')
                with date_input.add_slot('append'):
                    ui.icon('edit_calendar').on('click', menu.open).classes('cursor-pointer')
                date_input.set_value(default_value)
            return date_input

        if chart_type not in self._chart_types:
            chart_type = 'candlestick'

        self._complex = complex
        in_row_style = 'margin: auto auto;'

        with ui.column().classes('w-full items-center') as self._chart_box:
            with ui.row():
                if not complex:
                    ui.button('TradingView', on_click=trading_view_triggered, color='black').style(in_row_style)
                    ui.button('Bybit', on_click=exchange_triggered, color='black').style(in_row_style)
                validation = None if complex else lambda x: None if x in self._contracts else 'Not found'
                self._contract_input = ui.input('Contract',
                                                value=contract,
                                                autocomplete=list(self._contracts),
                                                on_change=contract_input_on_change,
                                                validation=validation)
                self._date_from_input = create_date_input('From', date_from_str)
                self._date_to_input = create_date_input('To', date_to_str)
                self._timeframe_select = ui.select(options=self._timeframes,
                                                   value=timeframe)
                self._price_type_select = ui.select(options=self._price_types,
                                                    value=price_type)
                self._fetch_button = ui.button('Fetch',
                                               on_click=lambda *_: self._update_chart_callback()).style(in_row_style)
                self._chart_type_select = ui.select(options=self._chart_types,
                                                    value=chart_type,
                                                    on_change=lambda *_: chart_type_changed())
            self._chart = ui.highchart(
                options=deepcopy(ChartUiData.STOCK_CHART),
                type='stockChart',
                extras=['stock', 'accessibility']
            ).style(chart_style)
            self._load_theme(theme_path)
            self._apply_theme(self._chart.options)
            self.set_custom_mode(self._is_custom)
            self._chart.update()
        return self._chart_box, self._chart

    def check(self):
        b = True
        b = b and self._contract_input is not None
        b = b and self._date_from_input is not None
        b = b and self._date_to_input is not None
        b = b and self._timeframe_select is not None
        b = b and self._price_type_select is not None
        b = b and self._chart_type_select is not None
        b = b and self._chart is not None
        if not b:
            raise Exception('Some of chart elements are not set')

    def update(self):
        self.check()
        self._chart_box.update()
        self._contract_input.update()
        self._date_from_input.update()
        self._date_to_input.update()
        self._timeframe_select.update()
        self._price_type_select.update()
        self._chart_type_select.update()
        self._fetch_button.update()
        self._chart.update()

    def is_custom(self):
        self.check()
        return self._is_custom

    def set_custom_mode(self, custom_mode: bool):
        self._is_custom = custom_mode
        if self._fetch_button:
            self._fetch_button.set_enabled(self._is_custom)
        if self._contract_input:
            self._contract_input.set_enabled(self._is_custom)
        if self._timeframe_select:
            self._timeframe_select.set_enabled(self._is_custom)
        if self._price_type_select:
            self._price_type_select.set_enabled(self._is_custom)
        if self._date_from_input:
            self._date_from_input.set_enabled(self._is_custom)
        if self._date_to_input:
            self._date_to_input.set_enabled(self._is_custom)

    def get_contract(self):
        self.check()
        if self._contract_input:
            return self._contract_input.value

    def set_contracts(self, contracts: Union[set, list]):
        self._contracts = set(contracts) | {'RANDOM'}
        if self._contract_input is not None:
            self._contract_input.set_autocomplete(list(self._contracts))

    def get_date_from(self):
        self.check()
        if self._date_from_input:
            return self._date_from_input.value

    def get_date_to(self):
        self.check()
        if self._date_to_input:
            return self._date_to_input.value

    def get_timeframe(self):
        self.check()
        if self._timeframe_select:
            return self._timeframe_select.value

    def set_timeframes(self, timeframes: list):
        self._timeframes = timeframes
        if self._timeframe_select is not None:
            self._timeframe_select.set_options(self._timeframes, value=self._timeframes[0])

    def get_price_type(self):
        self.check()
        if self._price_type_select:
            return self._price_type_select.value

    def set_price_types(self, price_types: list):
        self._price_types = price_types
        if self._price_type_select is not None:
            self._price_type_select.set_options(self._price_types, value=self._price_types[0])

    def set_update_chart_callback(self, func: callable):

        async def callback(*_, **__):
            return await func(self)

        self._update_chart_callback = callback

    def get_series(self, series_id: str):
        self.check()
        return next((x for x in self._chart.options['series'] if x['id'] == series_id), None)

    def get_stock_data(self, *, clear_series=False, clear_lines=False) -> dict:
        self.check()
        stock_data = dict()
        stock_data['title'] = self._chart.options['title']['text']
        contract = self.get_contract()
        if not self._complex and contract not in self._contracts:
            contract = ''
        stock_data['input'] = {
            'contract': contract,
            'date_from': self.get_date_from(),
            'date_to': self.get_date_to(),
            'timeframe': self.get_timeframe(),
            'price_type': self.get_price_type(),
        }
        stock_data['parameters'] = self._chart.options['parameters']
        stock_data['ohlc'] = self.get_series(StockChartUiComponent.OHLC_SERIES)['data']
        stock_data['volume'] = self.get_series(StockChartUiComponent.VOLUME_SERIES)['data']
        stock_data['other_series'] = [
            x for x in self._chart.options['series'] if x['id'] not in [
                StockChartUiComponent.OHLC_SERIES, StockChartUiComponent.VOLUME_SERIES
            ]
        ] if not clear_series else []
        stock_data['x_lines'] = self._chart.options['xAxis']['plotLines'] if not clear_lines else []
        stock_data['ohlc_lines'] = self._chart.options['yAxis'][0]['plotLines'] if not clear_lines else []
        stock_data['volume_lines'] = self._chart.options['yAxis'][1]['plotLines'] if not clear_lines else []
        stock_data['new_object_contract'] = deepcopy(self.__new_object_contract)
        return stock_data

    def _set_contract(self, value):
        self.check()
        if self._contract_input:
            self._contract_input.set_value(value)

    def _set_date_from(self, value):
        self.check()
        if self._date_from_input:
            self._date_from_input.set_value(value)

    def _set_date_to(self, value):
        self.check()
        if self._date_to_input:
            self._date_to_input.set_value(value)

    def _set_timeframe(self, value):
        self.check()
        if self._timeframe_select:
            self._timeframe_select.set_value(value)

    def _set_price_type(self, value):
        self.check()
        if self._price_type_select:
            self._price_type_select.set_value(value)

    def _get_object_type_color_width(self, *,
                                     object_type,
                                     default_color,
                                     force_color):
        color = default_color
        width = 1
        if object_type == 'current-price':
            color = ChartUiData.BLUE_COLOR
            width = 3
        elif object_type == 'entry-price':
            color = ChartUiData.WHITE_COLOR
            width = 2
        elif object_type == 'open-order':
            color = ChartUiData.LIGHT_COLOR
            width = 2
        elif object_type == 'close-order':
            color = ChartUiData.LIGHT_COLOR
            width = 2
        elif object_type == 'closed-order':
            color = ChartUiData.GRAY_COLOR
            width = 2
        elif object_type == 'take-profit':
            color = ChartUiData.GREEN_COLOR
            width = 2
        elif object_type == 'stop-loss':
            color = ChartUiData.ORANGE_COLOR
            width = 2
        elif object_type == 'trailing-stop':
            color = ChartUiData.ORANGE_COLOR
            width = 2
        elif object_type == 'liquidation-price':
            color = ChartUiData.RED_COLOR
            width = 2
        if force_color:
            color = force_color
        return color, width

    def set_stock_data(self, stock_data: dict):
        self.check()
        self._chart.options['title']['text'] = stock_data['title']
        stock_data_input = stock_data['input']
        self._set_contract(stock_data_input['contract'])
        self._set_date_from(stock_data_input['date_from'])
        self._set_date_to(stock_data_input['date_to'])
        self._set_timeframe(stock_data_input['timeframe'])
        self._set_price_type(stock_data_input['price_type'])
        self._chart.options['parameters'] = stock_data['parameters']
        self.get_series(StockChartUiComponent.OHLC_SERIES)['data'] = stock_data['ohlc']
        self.get_series(StockChartUiComponent.VOLUME_SERIES)['data'] = stock_data['volume']
        self._chart.options['series'] = [
            self.get_series(StockChartUiComponent.OHLC_SERIES),
            self.get_series(StockChartUiComponent.VOLUME_SERIES),
            *stock_data['other_series']
        ]
        if isinstance(stock_data['x_lines'], list):
            self._chart.options['xAxis']['plotLines'] = stock_data['x_lines']
        if isinstance(stock_data['ohlc_lines'], list):
            self._chart.options['yAxis'][0]['plotLines'] = stock_data['ohlc_lines']
        if isinstance(stock_data['volume_lines'], list):
            self._chart.options['yAxis'][1]['plotLines'] = stock_data['volume_lines']
        if isinstance(stock_data['new_object_contract'], list):
            new_objects = stock_data['new_object_contract']
            new_series = []
            new_x_lines = []
            new_ohlc_lines = []
            new_volume_lines = []
            for obj in new_objects:
                tmp_series = []
                tmp_x_lines = []
                tmp_ohlc_lines = []
                tmp_volume_lines = []
                target = obj.get('target', 'ohlc')
                visual_type = obj.get('visual-type', 'none')
                object_type = obj.get('object-type', 'other')
                marker_label = obj.get('marker-label', '')
                line_label = obj.get('line-label', '')
                values = obj.get('values', [])
                marker_color_f = obj.get('marker-color', '')
                line_color_f = obj.get('line-color', '')
                if target not in self.__new_object_contract['target']:
                    continue
                if visual_type not in self.__new_object_contract['visual-type']:
                    continue
                if object_type not in self.__new_object_contract['object-type']:
                    continue
                if type(marker_label) is not type(self.__new_object_contract['marker-label']):
                    continue
                if type(line_label) is not type(self.__new_object_contract['line-label']):
                    continue
                if type(values) is type(self.__new_object_contract['values']) and not values:
                    continue
                if type(marker_color_f) is not type(self.__new_object_contract['marker-color']):
                    continue
                if type(line_color_f) is not type(self.__new_object_contract['line-color']):
                    continue
                if visual_type in ('marker', 'marker-and-line'):
                    values_l = values if (isinstance(values, list) and
                                          values and isinstance(values[0], list)) else [values]
                    marker_color, _ = self._get_object_type_color_width(
                        object_type=object_type,
                        default_color=ChartUiData.PINK_COLOR,
                        force_color=marker_color_f
                    )
                    tmp_series.append(ChartUiData.make_marker(
                        target=target,
                        marker_id=''.join(x for x in marker_label if x.isalnum() or x == '_'),
                        marker_name=marker_label,
                        data=values_l,
                        color=marker_color,
                        radius=10,
                    ))
                if visual_type in ('line', 'marker-and-line'):
                    value = values if not isinstance(values, list) else\
                            values[1] if len(values) >= 2 else\
                            values[0] if not isinstance(values[0], list) else\
                            values[0][1] if len(values[0]) >= 2 else values[0][0]
                    line_color, line_width = self._get_object_type_color_width(
                        object_type=object_type,
                        default_color=ChartUiData.PINK_COLOR,
                        force_color=line_color_f
                    )
                    if target == 'x':
                        tmp_lines = tmp_x_lines
                    elif target == 'volume':
                        tmp_lines = tmp_volume_lines
                    else:
                        tmp_lines = tmp_ohlc_lines
                    tmp_lines.append(ChartUiData.make_line(
                        value=value,
                        label_text=line_label,
                        label_align='left',
                        line_color=line_color,
                        line_width=line_width
                    ))
                new_series.extend(tmp_series)
                new_x_lines.extend(tmp_x_lines)
                new_ohlc_lines.extend(tmp_ohlc_lines)
                new_volume_lines.extend(tmp_volume_lines)
            self._chart.options['series'].extend(new_series)
            self._chart.options['xAxis']['plotLines'].extend(new_x_lines)
            self._chart.options['yAxis'][0]['plotLines'].extend(new_ohlc_lines)
            self._chart.options['yAxis'][1]['plotLines'].extend(new_volume_lines)
        self.update()

    def _load_theme(self, theme_path):
        try:
            if not theme_path:
                theme_path = os.path.join(os.path.dirname(__file__), "high_contrast_dark_theme.json")
            with open(theme_path, 'r+', encoding='utf-8') as fp:
                self._theme = json.load(fp)
        except:
            traceback.print_exc()

    def _apply_theme(self, options: dict):
        if not self._theme:
            return
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
