from nicegui import ui
from typing import Union
import traceback

from bots_platform.gui.chart import StockChartUiComponent
from bots_platform.gui.utils import Notification
from bots_platform.model.workers import ChartsWorker
from bots_platform.model import TimeStamp


class ChartsSpace:
    UPDATE_CHARTS_CHECKBOX = 'UPDATE_CHARTS_CHECKBOX'
    UPDATE_CHARTS_TIMER = 'UPDATE_CHARTS_TIMER'
    CHARTS_BOX = 'CHARTS_BOX'

    def __init__(self):
        self._charts_worker: Union[ChartsWorker, None] = None
        self._charts_space = None
        self._elements = dict()
        self._constructed = False
        self._charts = []
        self._auto_charts = dict()
        notification = ui.notification(timeout=None, close_button=False)
        notification.message = 'Updating custom charts...'
        notification.spinner = True
        self.__notification = Notification(notification)

    async def init(self):
        self._elements.clear()
        if self._charts_space:
            self._charts_space.delete()
        self._charts_space = ui.card().classes('items-center')
        await self.update()
        self._constructed = True

    async def update(self):
        self.__notification.show()

        async def add_chart_triggered(*, complex):
            if not self._constructed:
                return
            self._constructed = False
            try:
                self._delete_update_charts_timer()
                self.add_custom_chart(complex=complex)
                await self._auto_update_timer_check()
            except:
                pass
            self._constructed = True

        with self._charts_space:
            try:
                await self._charts_worker.fetch_exchange_contracts(
                    number_of_seconds_to_update=10*60
                )
            except:
                pass

            if ChartsSpace.UPDATE_CHARTS_CHECKBOX not in self._elements:
                update_charts_checkbox = ui.checkbox('Auto update custom charts',
                                                     value=False,
                                                     on_change=lambda *_:
                                                     self._auto_update_timer_check())
                self._elements[ChartsSpace.UPDATE_CHARTS_CHECKBOX] = update_charts_checkbox

            if ChartsSpace.CHARTS_BOX not in self._elements:
                with ui.column():
                    ui.button('Add chart',
                              on_click=lambda *_: add_chart_triggered(complex=False)).classes('m-auto')
                    ui.button('Add complex chart',
                              on_click=lambda *_: add_chart_triggered(complex=True)).classes('m-auto')
                charts_box = ui.column().classes('w-full items-center')
                self._elements[ChartsSpace.CHARTS_BOX] = charts_box

            await self.update_custom_charts()
            await self._auto_update_timer_check()

        self.__notification.hide()

    def check(self):
        if self._charts_space is None or self._charts_worker is None:
            raise Exception(f'{type(self).__name__} is not initialized')

    def set_charts_worker(self, charts_worker: ChartsWorker):
        self._charts_worker = charts_worker

    def detach(self):
        try:
            self._charts_space.delete()
        except:
            pass
        self._constructed = False
        self._elements.clear()
        self._charts_space = None

    async def _auto_update_timer_check(self):
        if ChartsSpace.UPDATE_CHARTS_CHECKBOX not in self._elements:
            return
        update_charts_checkbox = self._elements[ChartsSpace.UPDATE_CHARTS_CHECKBOX]
        self._delete_update_charts_timer()
        if update_charts_checkbox.value:
            update_charts_timer = ui.timer(10.0,  # 10 seconds
                                           callback=lambda *_: self.update(),
                                           once=True)
            self._elements[ChartsSpace.UPDATE_CHARTS_TIMER] = update_charts_timer

    def _delete_update_charts_timer(self):
        if ChartsSpace.UPDATE_CHARTS_TIMER in self._elements:
            try:
                update_charts_timer = self._elements.pop(ChartsSpace.UPDATE_CHARTS_TIMER)
                update_charts_timer.cancel()
            except:
                pass

    def add_custom_chart(self, *, complex=False):

        async def update_chart_triggered(chart, *_, **__):
            await self._update_chart(chart)

        def duplicate_chart_triggered(*_, **__):
            nonlocal stock_chart, chart_col, complex
            try:
                new_stock_chart, new_chart_col = self.add_custom_chart(complex=complex)
                new_stock_chart.set_stock_data(stock_chart.get_stock_data())
                idx = new_chart_col.parent_slot.children.index(chart_col)
                new_chart_col.move(charts_box, idx + 1)
            except:
                traceback.print_exc()

        def delete_chart_triggered(*_, **__):
            charts_box.remove(chart_col)
            self._charts.remove(stock_chart)

        if ChartsSpace.CHARTS_BOX in self._elements:
            charts_box: ui.column = self._elements[ChartsSpace.CHARTS_BOX]
            with charts_box:
                with ui.column().classes('w-full items-center') as chart_col:
                    stock_chart = StockChartUiComponent()
                    stock_chart.set_custom_mode(True)
                    stock_chart.set_contracts(self._charts_worker.get_contracts())
                    timeframes = self._charts_worker.get_timeframes()
                    stock_chart.set_timeframes(timeframes)
                    price_types = self._charts_worker.get_price_types()
                    stock_chart.set_price_types(price_types)
                    stock_chart.set_update_chart_callback(update_chart_triggered)
                    stock_chart.set_duplicate_chart_callback(duplicate_chart_triggered)
                    stock_chart.set_delete_chart_callback(delete_chart_triggered)
                    prev_date = TimeStamp.format_date(TimeStamp.get_local_dt_from_now() - TimeStamp.timedelta(days=1))
                    stock_chart.create(
                        contract=r'''BTC/USDT:USDT''',
                        date_from_str=prev_date,
                        date_to_str='',
                        timeframe=timeframes[0],
                        price_type=price_types[0],
                        chart_type='candlestick',
                        chart_style='width:1000px;height:700px;',
                        complex=complex
                    )
                    stock_chart.check()
                    stock_chart.update()
                    self._charts.append(stock_chart)
                    ui.separator()
                    return stock_chart, chart_col

    async def update_custom_charts(self):
        for stock_chart in self._charts:
            if stock_chart.is_custom():
                await self._update_chart(stock_chart, timer_update=True)

    async def _update_chart(self,
                            stock_chart: StockChartUiComponent, *,
                            timer_update: bool = False):
        stock_data = stock_chart.get_stock_data()
        parameters = stock_data['parameters']
        p_contract = parameters['contract']
        p_date_from = parameters['date_from']
        p_date_to = parameters['date_to']
        p_timeframe = parameters['timeframe']
        p_price_type = parameters['price_type']
        p_real_date_from = parameters['real_date_from']
        data = stock_data['data']
        stock_data_input = stock_data['input']
        contract = stock_data_input['contract']
        date_from = stock_data_input['date_from']
        date_to = stock_data_input['date_to']
        timeframe = stock_data_input['timeframe']
        price_type = stock_data_input['price_type']

        if not contract or timer_update and 'random' in contract.lower():
            return

        b_clear = False
        if contract != p_contract:
            b_clear = True
        if date_from != p_date_from:
            b_clear = True
        if date_to != p_date_to:
            b_clear = True
        if timeframe != p_timeframe:
            b_clear = True
        if price_type != p_price_type:
            b_clear = True

        date_from_timestamp = None
        date_to_timestamp = ...
        if date_from:
            date_from_timestamp = int(TimeStamp.parse_date(date_from, utc=True).timestamp())
            date_from_timestamp = TimeStamp.convert_utc_to_local_timestamp(date_from_timestamp)
        if date_to:
            date_to_timestamp = int(TimeStamp.parse_date(date_to, utc=True).timestamp())
            date_to_timestamp = TimeStamp.convert_utc_to_local_timestamp(date_to_timestamp)
        date_from_timestamp, date_to_timestamp = TimeStamp.get_timestamps_range(
            date_from_timestamp, date_to_timestamp, utc=False)

        if b_clear or 'random' in contract.lower():
            data.clear()
            p_real_date_from = date_from_timestamp

        try:
            chart_data = await self._charts_worker.update_chart_data(
                contract=contract,
                date_from=p_real_date_from,
                date_to=date_to_timestamp,
                timeframe=timeframe,
                price_type=price_type,
                data=data
            )
            p_real_date_from = chart_data['date_from']
            data = chart_data['data']
        except:
            traceback.print_exc()

        stock_data['title'] = f"{contract} ({price_type})"
        stock_data['data'] = data

        parameters['contract'] = contract
        parameters['date_from'] = date_from
        parameters['date_to'] = date_to
        parameters['timeframe'] = timeframe
        parameters['price_type'] = price_type
        parameters['real_date_from'] = p_real_date_from

        stock_chart.set_contracts(self._charts_worker.get_contracts())
        stock_chart.set_stock_data(stock_data, clear_auto_overlay=True)

    async def add_update_auto_chart(self, *,
                                    first_timestamp,
                                    contract: str,
                                    side: str,
                                    objects: list,
                                    timeframe: str = '1m',
                                    price_type: str = 'OHLCV',
                                    chart_type='candle_solid',
                                    complex: bool = False,
                                    last_update: bool = False,
                                    forget: bool = False):

        key = (first_timestamp, contract, side)
        if key in self._auto_charts:
            if forget:
                self._auto_charts.pop(key)
                return await self.add_update_auto_chart(
                    first_timestamp=first_timestamp,
                    contract=contract,
                    side=side,
                    objects=objects,
                    timeframe=timeframe,
                    price_type=price_type,
                    chart_type=chart_type,
                    complex=complex,
                    last_update=last_update,
                    forget=forget,
                )
            stock_chart = self._auto_charts[key]
            if not isinstance(stock_chart, StockChartUiComponent):
                return
            await self._update_chart(stock_chart)
            stock_data = stock_chart.get_stock_data()
            stock_data['new_object_contract'] = objects
            stock_chart.set_contracts(self._charts_worker.get_contracts())
            stock_chart.set_stock_data(stock_data, clear_auto_overlay=True)
            if last_update:
                self._auto_charts[key] = 'deleted'  # todo: first_timestamp
            return
        if last_update:
            return

        async def update_chart_triggered(*_, **__):
            pass

        def duplicate_chart_triggered(*_, **__):
            nonlocal stock_chart, chart_col, complex
            try:
                new_stock_chart, new_chart_col = self.add_custom_chart(complex=complex)
                new_stock_chart.set_stock_data(stock_chart.get_stock_data())
                idx = new_chart_col.parent_slot.children.index(chart_col)
                new_chart_col.move(charts_box, idx + 1)
            except:
                traceback.print_exc()

        def delete_chart_triggered(*_, **__):
            self._auto_charts[key] = 'deleted'
            charts_box.remove(chart_col)
            self._charts.remove(stock_chart)

        async def dialog_yes():
            nonlocal dialog
            delete_chart_triggered()
            dialog.close()

        async def dialog_no():
            nonlocal dialog
            dialog.close()

        with ui.dialog() as dialog, ui.card().classes('items-center'):
            ui.label('Are you sure you want to delete this chart?')
            with ui.row():
                ui.button('Yes', on_click=dialog_yes)
                ui.button('No', on_click=dialog_no)

        if ChartsSpace.CHARTS_BOX in self._elements:
            charts_box: ui.column = self._elements[ChartsSpace.CHARTS_BOX]
            with charts_box:
                with ui.column().classes('w-full items-center') as chart_col:
                    stock_chart = StockChartUiComponent()
                    stock_chart.set_custom_mode(False)
                    stock_chart.set_contracts(self._charts_worker.get_contracts())
                    timeframes = self._charts_worker.get_timeframes()
                    stock_chart.set_timeframes(timeframes)
                    price_types = self._charts_worker.get_price_types()
                    stock_chart.set_price_types(price_types)
                    stock_chart.set_update_chart_callback(update_chart_triggered)
                    stock_chart.set_duplicate_chart_callback(duplicate_chart_triggered)
                    stock_chart.set_delete_chart_callback(lambda *_, **__: dialog.open())
                    prev_date = TimeStamp.convert_local_to_utc_timestamp(first_timestamp)
                    prev_date = TimeStamp.format_date(TimeStamp.get_utc_dt_from_timestamp(prev_date))
                    stock_chart.create(
                        contract=contract,
                        date_from_str=prev_date,
                        date_to_str='',
                        timeframe=timeframe,
                        price_type=price_type,
                        chart_type=chart_type,
                        chart_style='width:1000px;height:700px;',
                        complex=complex
                    )
                    stock_chart.check()
                    await self._update_chart(stock_chart)
                    stock_data = stock_chart.get_stock_data()
                    stock_data['new_object_contract'] = objects
                    stock_chart.set_stock_data(stock_data, clear_auto_overlay=True)
                    self._charts.append(stock_chart)
                    self._auto_charts[key] = stock_chart
                    ui.separator()
                    chart_col.update()
                charts_box.update()
            return stock_chart
