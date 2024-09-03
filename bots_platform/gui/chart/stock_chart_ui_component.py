from typing import Union
from copy import deepcopy
import inspect
import traceback

from nicegui import ui
from bots_platform.gui.chart import ChartUiData
from bots_platform.gui.chart.klinechart import KLineChart
from bots_platform.model.utils import TimeStamp, get_trading_view_url, get_exchange_trade_url


class StockChartUiComponent:
    def __init__(self):
        self._is_custom = True
        self._theme = None
        self._contracts = set()
        self._timeframes = []
        self._price_types = []
        self._chart_types = [
            'candle_solid',
            'candle_stroke',
            'candle_up_stroke',
            'candle_down_stroke',
            'ohlc',
            'area'
        ]
        self._update_chart_callback = lambda *_, **__: None
        self._duplicate_chart_callback = lambda *_, **__: None
        self._delete_chart_callback = lambda *_, **__: None
        self.__new_object_contract = {
            'type': ['overlay'],
            'overlay-type': {'marker', 'line', 'marker-and-line'},
            'overlay-hint': {'entry-price', 'current-price', 'open-order', 'close-order', 'closed-order',
                             'take-profit', 'stop-loss', 'trailing-stop', 'liquidation-price', 'other'},
            'marker-label': '',
            'line-label': '',
            'marker-label-color': '',
            'marker-background-color': '',
            'line-color': '',
            'line-label-color': '',
            'line-label-background-color': '',
            'line-width': '',
            'values': [],
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
        self._chart_caption_label = None
        self._chart = None

    def create(self, *,
               contract: '',
               date_from_str: str = '',
               date_to_str: str = '',
               timeframe: str = '1m',
               price_type: str = 'OHLCV',
               chart_type: str = 'candle_solid',
               chart_style: str = '',
               complex: bool = False):

        def trading_view_triggered(*_):
            v = self._contract_input.value
            if v in self._contracts:
                ui.navigate.to(get_trading_view_url(v), new_tab=True)
            else:
                ui.notify('Market contract not found!', close_button=True, type='warning')

        def exchange_triggered(*_):
            v = self._contract_input.value
            if v in self._contracts:
                ui.navigate.to(get_exchange_trade_url(v), new_tab=True)
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
            chart_type = self._chart_type_select.value.replace(' ', '_')
            if chart_type in self._chart_types:
                self._chart.options['styles']['candle']['type'] = chart_type
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

        def set_mode(value):
            nonlocal mode, mode_button
            mode = value
            mode_button.set_text(f"Mode [{mode.replace('_', ' ').capitalize()}]")

        def update():
            self._chart.options['styles'].setdefault('u', 0)
            if self._chart.options['styles']['u'] == 0:
                self._chart.options['styles']['u'] = 1
            else:
                self._chart.options['styles']['u'] = 0
            self._chart.update()

        mode = ''
        self._complex = complex
        in_row_style = 'margin: auto auto;'
        caption_style = 'font-size: 18px;'
        if chart_type not in self._chart_types:
            chart_type = 'candle_solid'

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
                self._chart_type_select = ui.select(options=[x.replace('_', ' ') for x in self._chart_types],
                                                    value=chart_type.replace('_', ' '),
                                                    on_change=lambda *_: chart_type_changed())
                caption = (contract or 'Chart') + f' {price_type}'
            self._chart_caption_label = ui.label(caption).style(caption_style).style(in_row_style)
            self._chart = KLineChart(options=deepcopy(ChartUiData.STOCK_CHART)).style(chart_style)
            with ui.row():
                with ui.card(align_items='center').style(in_row_style), ui.row():
                    ui.label('Overlay').style(in_row_style)
                    with ui.dropdown_button('', auto_close=True, color='dark').style(in_row_style) as mode_button:
                        set_mode('normal')
                        items = [
                            ('Normal', lambda *_: set_mode('normal')),
                            ('Weak Magnet', lambda *_: set_mode('weak_magnet')),
                            ('Strong Magnet', lambda *_: set_mode('strong_magnet')),
                        ]
                        for title, on_click in items:
                            ui.item(title, on_click=on_click).style('text-align:center;')
                    with ui.dropdown_button('Add', auto_close=True, color='dark').style(in_row_style):
                        items = [
                            ('Lines', lambda *_:
                            self._chart.add_overlay({'name': 'lines', 'mode': mode},
                                                    KLineChart.DRAWINGS_GROUP)),
                            ('% change', lambda *_:
                            self._chart.add_overlay({'name': 'percentage_change', 'mode': mode},
                                                    KLineChart.DRAWINGS_GROUP)),
                            ('↑↓%', lambda *_:
                            self._chart.add_overlay({'name': 'buildup_drawdown', 'mode': mode},
                                                    KLineChart.DRAWINGS_GROUP)),
                            ('↑↓% max', lambda *_:
                            self._chart.add_overlay({'name': 'buildup_drawdown_max', 'mode': mode},
                                                    KLineChart.DRAWINGS_GROUP)),
                            ('Risk:Reward', lambda *_:
                            self._chart.add_overlay({'name': 'risk_reward', 'mode': mode},
                                                    KLineChart.DRAWINGS_GROUP)),
                            ('Volume Profile', lambda *_:
                            self._chart.add_overlay({'name': 'volume_profile', 'mode': mode},
                                                    KLineChart.DRAWINGS_GROUP))
                        ]
                        for title, on_click in items:
                            ui.item(title, on_click=on_click).style('text-align:center;')
                    ui.button('Clear',
                              on_click=lambda *_: self._chart.remove_overlay(KLineChart.DRAWINGS_GROUP),
                              color='dark').style(in_row_style)
                with ui.card(align_items='center').style(in_row_style), ui.row():
                    ui.label('Chart').style(in_row_style)
                    ui.button('Update view',
                              on_click=lambda *_: update(),
                              color='dark').style(in_row_style)
                    ui.button('Duplicate',
                              on_click=lambda *_: self._duplicate_chart_callback(),
                              color='dark').style(in_row_style)
                    ui.button('Delete',
                              on_click=lambda *_: self._delete_chart_callback(),
                              color='dark').style(in_row_style)
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
        b = b and self._chart_caption_label is not None
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
        self._chart_caption_label.update()
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
            r = func(self)
            b = inspect.isawaitable(r)
            if b:
                return await r
            return r

        self._update_chart_callback = callback

    def set_duplicate_chart_callback(self, func: callable):

        async def callback(*_, **__):
            r = func(self)
            b = inspect.isawaitable(r)
            if b:
                return await r
            return r

        self._duplicate_chart_callback = callback

    def set_delete_chart_callback(self, func: callable):

        async def callback(*_, **__):
            r = func(self)
            b = inspect.isawaitable(r)
            if b:
                return await r
            return r

        self._delete_chart_callback = callback

    def get_stock_data(self) -> dict:
        self.check()
        stock_data = dict()
        stock_data['title'] = self._chart_caption_label.text
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
        stock_data['data'] = self._chart.options['data']
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

    def _get_view_parameters(self, *,
                             object_type,
                             default_marker_label_color,
                             default_marker_background_color,
                             default_line_color,
                             default_line_label_color,
                             default_line_label_background_color,
                             default_line_width,
                             force_marker_label_color,
                             force_marker_background_color,
                             force_line_color,
                             force_line_label_color,
                             force_line_label_background_color,
                             force_line_width):
        marker_label_color = default_marker_label_color
        marker_background_color = default_marker_background_color
        line_color = default_line_color
        line_label_color = default_line_label_color
        line_label_background_color = default_line_label_background_color
        line_width = default_line_width

        if object_type == 'current-price':
            marker_label_color = ChartUiData.LIGHT_COLOR
            marker_background_color = ChartUiData.BLUE_COLOR
            line_color = ChartUiData.BLUE_COLOR
            line_label_color = ChartUiData.LIGHT_COLOR
            line_label_background_color = ChartUiData.BLUE_COLOR
            line_width = 3
        elif object_type == 'entry-price':
            marker_label_color = ChartUiData.DARK_COLOR
            marker_background_color = ChartUiData.LIGHT_COLOR
            line_color = ChartUiData.LIGHT_COLOR
            line_label_color = ChartUiData.DARK_COLOR
            line_label_background_color = ChartUiData.LIGHT_COLOR
            line_width = 2
        elif object_type == 'open-order':
            marker_label_color = ChartUiData.LIGHT_COLOR
            marker_background_color = ChartUiData.DARK_COLOR
            line_color = ChartUiData.DARK_COLOR
            line_label_color = ChartUiData.LIGHT_COLOR
            line_label_background_color = ChartUiData.DARK_COLOR
            line_width = 2
        elif object_type == 'close-order':
            marker_label_color = ChartUiData.DARK_COLOR
            marker_background_color = ChartUiData.GRAY_COLOR
            line_color = ChartUiData.GRAY_COLOR
            line_label_color = ChartUiData.DARK_COLOR
            line_label_background_color = ChartUiData.GRAY_COLOR
            line_width = 2
        elif object_type == 'closed-order':
            marker_label_color = ChartUiData.GRAY_COLOR
            marker_background_color = ChartUiData.DARK_COLOR
            line_color = ChartUiData.DARK_COLOR
            line_label_color = ChartUiData.GRAY_COLOR
            line_label_background_color = ChartUiData.DARK_COLOR
            line_width = 2
        elif object_type == 'take-profit':
            marker_label_color = ChartUiData.DARK_COLOR
            marker_background_color = ChartUiData.GREEN_COLOR
            line_color = ChartUiData.GREEN_COLOR
            line_label_color = ChartUiData.DARK_COLOR
            line_label_background_color = ChartUiData.GREEN_COLOR
            line_width = 2
        elif object_type == 'stop-loss':
            marker_label_color = ChartUiData.DARK_COLOR
            marker_background_color = ChartUiData.ORANGE_COLOR
            line_color = ChartUiData.ORANGE_COLOR
            line_label_color = ChartUiData.DARK_COLOR
            line_label_background_color = ChartUiData.ORANGE_COLOR
            line_width = 2
        elif object_type == 'trailing-stop':
            marker_label_color = ChartUiData.DARK_COLOR
            marker_background_color = ChartUiData.ORANGE_COLOR
            line_color = ChartUiData.ORANGE_COLOR
            line_label_color = ChartUiData.DARK_COLOR
            line_label_background_color = ChartUiData.ORANGE_COLOR
            line_width = 1
        elif object_type == 'liquidation-price':
            marker_label_color = ChartUiData.DARK_COLOR
            marker_background_color = ChartUiData.RED_COLOR
            line_color = ChartUiData.RED_COLOR
            line_label_color = ChartUiData.DARK_COLOR
            line_label_background_color = ChartUiData.RED_COLOR
            line_width = 3
        if force_marker_label_color:
            marker_label_color = force_marker_label_color
        if force_marker_background_color:
            marker_background_color = force_marker_background_color
        if force_line_color:
            line_color = force_line_color
        if force_line_label_color:
            line_label_color = force_line_label_color
        if force_line_label_background_color:
            line_label_background_color = force_line_label_background_color
        if force_line_width:
            line_width = force_line_width
        return {
            'marker_label_color': marker_label_color,
            'marker_background_color': marker_background_color,
            'line_color': line_color,
            'line_label_color': line_label_color,
            'line_label_background_color': line_label_background_color,
            'line_width': line_width,
        }

    def set_stock_data(self, stock_data: dict, clear_auto_overlay: bool = False):
        self.check()
        self._chart_caption_label.set_text(stock_data['title'])
        stock_data_input = stock_data['input']
        self._set_contract(stock_data_input['contract'])
        self._set_date_from(stock_data_input['date_from'])
        self._set_date_to(stock_data_input['date_to'])
        self._set_timeframe(stock_data_input['timeframe'])
        self._set_price_type(stock_data_input['price_type'])
        self._chart.options['parameters'] = stock_data['parameters']
        self._chart.options['data'] = stock_data['data']

        if stock_data['data']:
            p0 = 0.1
            v0 = 0.1
            p11 = stock_data['data'][0]['low']
            p12 = stock_data['data'][0]['high']
            v1 = stock_data['data'][0]['volume']
            p21 = stock_data['data'][-1]['low']
            p22 = stock_data['data'][-1]['high']
            v2 = stock_data['data'][-1]['volume']
            price_digits = max(len(f"{abs(x % 1):.12f}".rstrip('0')) - 2
                               for x in (p0, p11, p12, p21, p22) if x % 1 > 0)
            volume_digits = max(len(f"{abs(x % 1):.12f}".rstrip('0')) - 2
                                for x in (v0, v1, v2) if x % 1 > 0)
            self._chart.options['price_precision'] = price_digits
            self._chart.options['volume_precision'] = volume_digits

        if clear_auto_overlay:
            self._chart.remove_overlay(KLineChart.AUTO_DRAWINGS_GROUP)
        if isinstance(stock_data['new_object_contract'], list):
            new_objects = stock_data['new_object_contract']
            for obj in new_objects:
                try:
                    obj_type = obj.get('type')
                    if obj_type not in self.__new_object_contract['type']:
                        continue
                    marker_label = obj.get('marker-label', '')
                    if type(marker_label) is not type(self.__new_object_contract['marker-label']):
                        continue
                    line_label = obj.get('line-label', '')
                    if type(line_label) is not type(self.__new_object_contract['line-label']):
                        continue
                    marker_label_color = obj.get('marker-label-color', '')
                    if type(marker_label_color) is not type(self.__new_object_contract['marker-label-color']):
                        continue
                    marker_background_color = obj.get('marker-background-color', '')
                    if type(marker_background_color) is not type(self.__new_object_contract['marker-background-color']):
                        continue
                    line_color = obj.get('line-color', '')
                    if type(line_color) is not type(self.__new_object_contract['line-color']):
                        continue
                    line_label_color = obj.get('line-label-color', '')
                    if type(line_label_color) is not type(self.__new_object_contract['line-label-color']):
                        continue
                    line_label_background_color = obj.get('line-label-background-color', '')
                    if type(line_label_background_color) is not type(self.__new_object_contract['line-label-background-color']):
                        continue
                    line_width = obj.get('line-width', '')
                    if type(line_width) is not type(self.__new_object_contract['line-width']):
                        continue
                    values = obj.get('values', [])
                    if type(values) is not type(self.__new_object_contract['values']) or not values:
                        continue
                    if obj_type == 'overlay':
                        overlay_type = obj.get('overlay-type')
                        overlay_hint = obj.get('overlay-hint')
                        view_parameters = self._get_view_parameters(
                            object_type=overlay_hint,
                            default_marker_label_color=ChartUiData.LIGHT_COLOR,
                            default_marker_background_color=ChartUiData.PINK_COLOR,
                            default_line_color=ChartUiData.PINK_COLOR,
                            default_line_label_color=ChartUiData.LIGHT_COLOR,
                            default_line_label_background_color=ChartUiData.PINK_COLOR,
                            default_line_width=1,
                            force_marker_label_color=marker_label_color,
                            force_marker_background_color=marker_background_color,
                            force_line_color=line_color,
                            force_line_label_color=line_label_color,
                            force_line_label_background_color=line_label_background_color,
                            force_line_width=line_width
                        )
                        if 'marker' in overlay_type:
                            if isinstance(values[0], list):
                                values = values[0]
                            timestamp, value = values
                            marker = ChartUiData.make_marker(
                                timestamp=timestamp,
                                value=value,
                                label_text=marker_label,
                                label_color=view_parameters['marker_label_color'],
                                label_background_color=view_parameters['marker_background_color'],
                            )
                            self._chart.add_overlay(marker)
                        if 'line' in overlay_type:
                            if isinstance(values[0], list):
                                values = values[0]
                            _, value = values
                            line = ChartUiData.make_line(
                                value=value,
                                label_text=line_label,
                                label_color=view_parameters['line_label_color'],
                                label_background_color=view_parameters['line_label_background_color'],
                                line_color=view_parameters['line_color'],
                                line_width=view_parameters['line_width'],
                                align='right',
                            )
                            self._chart.add_overlay(line)
                except:
                    traceback.print_exc()
        self.update()
