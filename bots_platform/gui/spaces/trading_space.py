from nicegui import ui
from typing import Union
from decimal import Decimal
import traceback

from bots_platform.model.workers import TradingWorker
from bots_platform.model.utils import get_exchange_trade_url, TimeStamp
from bots_platform.gui.spaces import Columns, ChartsSpace


class TradingSpace:
    UPDATE_CHARTS_CHECKBOX = 'UPDATE_CHARTS_CHECKBOX'
    UPDATE_BUTTON = 'UPDATE_BUTTON'
    FILTER_INPUT = 'FILTER_INPUT'
    POSITIONS_TABLE = 'POSITIONS_TABLE'
    OPEN_ORDERS_TABLE = 'OPEN_ORDERS_TABLE'
    CLOSED_ORDERS_TABLE = 'CLOSED_ORDERS_TABLE'
    CANCELED_ORDERS_TABLE = 'CANCELED_ORDERS_TABLE'
    LEDGER_TABLE = 'LEDGER_TABLE'
    UPDATE_TRADING_TIMER = 'UPDATE_TRADING_TIMER'

    def __init__(self):
        self._trading_worker: Union[TradingWorker, None] = None
        self._trading_space = None
        self._charts_space: Union[ChartsSpace, None] = None
        self._elements = dict()
        self._constructed = False

    async def init(self):
        self._elements.clear()
        if self._trading_space:
            self._trading_space.delete()
        self._trading_space = ui.card().classes('items-center')
        await self.update()
        self._constructed = True

    async def update(self):
        self._delete_update_trading_timer()
        notification = ui.notification(timeout=10, close_button=True)
        notification.message = 'Fetching trading info...'
        notification.spinner = True

        async def update_trading_triggered(force=False):
            if not self._constructed:
                return
            self._constructed = False
            try:
                self._delete_update_trading_timer()
                if force:
                    await self._trading_worker.force_update_trading_data(only_reset=True)
                await self.update()
            except:
                pass
            self._constructed = True

        with self._trading_space:

            if TradingSpace.UPDATE_BUTTON not in self._elements:
                update_button = ui.button('Update trading info',
                                          on_click=lambda *_: update_trading_triggered(True)).classes('m-auto')
                self._elements[TradingSpace.UPDATE_BUTTON] = update_button

            if TradingSpace.FILTER_INPUT not in self._elements:
                filter_input = ui.input('Filter')
                self._elements[TradingSpace.FILTER_INPUT] = filter_input
            else:
                filter_input = self._elements[TradingSpace.FILTER_INPUT]

            if ChartsSpace.UPDATE_CHARTS_CHECKBOX not in self._elements:
                update_charts_checkbox = ui.checkbox('Automatically create and update charts', value=False)
                self._elements[ChartsSpace.UPDATE_CHARTS_CHECKBOX] = update_charts_checkbox

            autocomplete = set()
            trading_data = dict()
            positions = []
            open_orders = []
            closed_orders = []
            canceled_orders = []
            ledger = []
            try:
                trading_data = await self._trading_worker.fetch_trading_data()
                positions = trading_data[TradingWorker.POSITIONS]
                open_orders = trading_data[TradingWorker.OPEN_ORDERS]
                closed_orders = trading_data[TradingWorker.CLOSED_ORDERS]
                canceled_orders = trading_data[TradingWorker.CANCELED_ORDERS]
                ledger = trading_data[TradingWorker.LEDGER]
            except:
                pass

            # POSITIONS
            for x in positions:
                x['key'] = f"{x['datetime']} {x['type']} {x['contract']} {x['side']}"
                x['exchange_link'] = get_exchange_trade_url(x['contract'])
                contract = x['contract']
                autocomplete.add(contract)
            positions.sort(key=lambda x: x['key'], reverse=True)
            if TradingSpace.POSITIONS_TABLE not in self._elements:
                ui.separator()
                ui.label('Positions')
                table = ui.table(columns=Columns.POSITION_COLUMNS, rows=positions, row_key='key',
                                 pagination=10).style("width: 1250px;")
                table.add_slot('body-cell-contract', '''
                     <q-td :props="props">
                         <a :href="props.row.exchange_link" target="_blank">{{ props.row.contract }}</a>
                     </q-td>
                ''')
                self._elements[TradingSpace.POSITIONS_TABLE] = table
                filter_input.bind_value_to(table, 'filter')
            else:
                table = self._elements[TradingSpace.POSITIONS_TABLE]
                table.update_rows(positions)

            # OPEN ORDERS
            for x in open_orders:
                x['key'] = f"{x['datetime']} {x['type']} {x['contract']} {x['side']} {x['order']} {x['price']} {x['size']}"
                x['exchange_link'] = get_exchange_trade_url(x['contract'])
                contract = x['contract']
                autocomplete.add(contract)
            open_orders.sort(key=lambda x: x['key'], reverse=True)
            if TradingSpace.OPEN_ORDERS_TABLE not in self._elements:
                ui.separator()
                ui.label('Open orders')
                table = ui.table(columns=Columns.OPEN_ORDERS_COLUMNS, rows=open_orders, row_key='key',
                                 pagination=5).style("width: 1250px;")
                table.add_slot('body-cell-contract', '''
                     <q-td :props="props">
                         <a :href="props.row.exchange_link" target="_blank">{{ props.row.contract }}</a>
                     </q-td>
                ''')
                self._elements[TradingSpace.OPEN_ORDERS_TABLE] = table
                filter_input.bind_value_to(table, 'filter')
            else:
                table = self._elements[TradingSpace.OPEN_ORDERS_TABLE]
                table.update_rows(open_orders)

            # CLOSED ORDERS
            for x in closed_orders:
                x['key'] = f"{x['datetime']} {x['type']} {x['contract']} {x['side']} {x['order']} {x['price']} {x['size']}"
                x['exchange_link'] = get_exchange_trade_url(x['contract'])
                autocomplete.add(x['contract'])
            closed_orders.sort(key=lambda x: x['key'], reverse=True)
            if TradingSpace.CLOSED_ORDERS_TABLE not in self._elements:
                ui.separator()
                ui.label('Closed orders')
                table = ui.table(columns=Columns.CLOSED_ORDERS_COLUMNS, rows=closed_orders, row_key='key',
                                 pagination=5).style("width: 1250px;")
                table.add_slot('body-cell-contract', '''
                     <q-td :props="props">
                         <a :href="props.row.exchange_link" target="_blank">{{ props.row.contract }}</a>
                     </q-td>
                ''')
                self._elements[TradingSpace.CLOSED_ORDERS_TABLE] = table
                filter_input.bind_value_to(table, 'filter')
            else:
                table = self._elements[TradingSpace.CLOSED_ORDERS_TABLE]
                table.update_rows(closed_orders)

            # CANCELED ORDERS
            for x in canceled_orders:
                x['key'] = f"{x['datetime']} {x['type']} {x['contract']} {x['side']} {x['order']} {x['reason']} {x['size']}"
                x['exchange_link'] = get_exchange_trade_url(x['contract'])
                autocomplete.add(x['contract'])
            canceled_orders.sort(key=lambda x: x['key'], reverse=True)
            if TradingSpace.CANCELED_ORDERS_TABLE not in self._elements:
                ui.separator()
                ui.label('Canceled orders')
                table = ui.table(columns=Columns.CANCELED_ORDERS_COLUMNS, rows=canceled_orders, row_key='key',
                                 pagination=5).style("width: 1250px;")
                table.add_slot('body-cell-contract', '''
                     <q-td :props="props">
                         <a :href="props.row.exchange_link" target="_blank">{{ props.row.contract }}</a>
                     </q-td>
                ''')
                self._elements[TradingSpace.CANCELED_ORDERS_TABLE] = table
                filter_input.bind_value_to(table, 'filter')
            else:
                table = self._elements[TradingSpace.CANCELED_ORDERS_TABLE]
                table.update_rows(canceled_orders)

            # LEDGER
            for x in ledger:
                x['key'] = f"{x['datetime']} {x['contract']} {x['type']} {x['side']} {x['quantity']}"
                x['exchange_link'] = get_exchange_trade_url(x['contract'])
                autocomplete.add(x['contract'])
            ledger.sort(key=lambda x: x['key'], reverse=True)
            if TradingSpace.LEDGER_TABLE not in self._elements:
                ui.separator()
                ui.label('Transactions')
                table = ui.table(columns=Columns.LEDGER_COLUMNS, rows=ledger, row_key='key',
                                 pagination=5).style("width: 1250px;")
                table.add_slot('body-cell-contract', '''
                     <q-td :props="props">
                         <a :href="props.row.exchange_link" target="_blank">{{ props.row.contract }}</a>
                     </q-td>
                ''')
                self._elements[TradingSpace.LEDGER_TABLE] = table
                filter_input.bind_value_to(table, 'filter')
            else:
                table = self._elements[TradingSpace.LEDGER_TABLE]
                table.update_rows(ledger)

            filter_input.set_autocomplete(list(autocomplete))
            await self._add_update_charts(trading_data)

            self._elements[TradingSpace.UPDATE_TRADING_TIMER] = ui.timer(10,  # 10 seconds
                                                                         callback=lambda *_: update_trading_triggered(),
                                                                         once=True)

        notification.spinner = False
        notification.dismiss()

    def check(self):
        if self._trading_space is None or self._trading_worker is None:
            raise Exception(f'{type(self).__name__} is not initialized')

    def set_trading_worker(self, trading_worker: TradingWorker):
        self._trading_worker = trading_worker

    def set_charts_space(self, charts_space: ChartsSpace):
        self._charts_space = charts_space

    def detach(self):
        try:
            self._delete_update_trading_timer()
            self._trading_space.delete()
        except:
            pass
        self._constructed = False
        self._elements.clear()
        self._trading_space = None

    def _delete_update_trading_timer(self):
        if TradingSpace.UPDATE_TRADING_TIMER in self._elements:
            try:
                update_trading_timer = self._elements.pop(TradingSpace.UPDATE_TRADING_TIMER)
                update_trading_timer.cancel()
                update_trading_timer.delete()
            except:
                pass

    async def _add_update_charts(self, trading_data: dict):
        try:
            if not trading_data or not self._charts_space:
                return
            if ChartsSpace.UPDATE_CHARTS_CHECKBOX not in self._elements:
                return
            update_charts_checkbox = self._elements[ChartsSpace.UPDATE_CHARTS_CHECKBOX]
            if not update_charts_checkbox.value:
                return

            positions = trading_data[TradingWorker.POSITIONS]
            open_orders = trading_data[TradingWorker.OPEN_ORDERS]
            closed_orders = trading_data[TradingWorker.CLOSED_ORDERS]
            graphs = dict()
            first_timestamps = dict()

            for x in positions:
                market_type = x['type']
                contract = x['contract']
                side = x['side']
                market_type_d = graphs.setdefault(market_type, dict())
                contract_d = market_type_d.setdefault(contract, dict())
                side_d = contract_d.setdefault(side, dict())
                position_d = side_d.setdefault('position', dict())
                first_timestamp = x['timestamp']
                key = (market_type, contract, side)
                first_timestamps[key] = min(
                    first_timestamp,
                    first_timestamps.get(key, first_timestamp)
                )
                position_d.clear()
                position_d.update({
                    'timestamp': x['timestamp'],
                    'pnl': x['pnl'],
                    'entry_price': x['entry_price'],
                    'mark_price': x['mark_price'],
                    'liquidation_price': x['liquidation_price'],
                    'trailing_stop': x['trailing_stop'],
                })

            for x in open_orders:
                market_type = x['type']
                contract = x['contract']
                side = x['side']
                market_type_d = graphs.setdefault(market_type, dict())
                contract_d = market_type_d.setdefault(contract, dict())
                side_d = contract_d.setdefault(side, dict())
                open_orders_l = side_d.setdefault('open_orders', list())
                first_timestamp = x['timestamp']
                key = (market_type, contract, side)
                first_timestamps[key] = min(
                    first_timestamp,
                    first_timestamps.get(key, first_timestamp)
                )
                open_orders_l.append({
                    'timestamp': x['timestamp'],
                    'order': x['order'],
                    'price': x['real_price'],
                    'tp_sl': x['tp_sl'],
                })

            for x in closed_orders:
                market_type = x['type']
                contract = x['contract']
                side = x['side']
                market_type_d = graphs.setdefault(market_type, dict())
                contract_d = market_type_d.setdefault(contract, dict())
                side_d = contract_d.setdefault(side, dict())
                closed_orders_l = side_d.setdefault('closed_orders', list())
                first_timestamp = x['timestamp']
                key = (market_type, contract, side)
                first_timestamps[key] = min(
                    first_timestamp,
                    first_timestamps.get(key, first_timestamp)
                )
                closed_orders_l.append({
                    'timestamp': x['timestamp'],
                    'order': x['order'],
                    'price': x['real_price'],
                    'tp_sl': x['tp_sl'],
                })

            def put_numbers_pair(value1, value2):
                if not isinstance(value1, (int, float, Decimal)):
                    try:
                        value1 = Decimal(value1)
                    except:
                        return []
                try:
                    value1 = int(value1)
                except:
                    pass
                if not isinstance(value2, (int, float, Decimal)):
                    try:
                        value2 = Decimal(value2)
                    except:
                        return []
                return [[value1, value2]]

            for market_type, market_type_d in graphs.items():
                for contract, contract_d in market_type_d.items():
                    for side, side_d in contract_d.items():
                        key = (market_type, contract, side)
                        first_timestamp = first_timestamps.get(key)
                        if not first_timestamp:
                            continue
                        first_timestamp = TimeStamp.convert_utc_to_local_timestamp(first_timestamp)
                        b_add_update = False
                        b_last_update = False
                        current_timestamp = TimeStamp.get_utc_dt_from_now().timestamp()
                        current_timestamp = int(TimeStamp.convert_utc_to_local_timestamp(current_timestamp) * 1000)
                        objects = []
                        if 'position' in side_d:
                            position = side_d['position']
                            objects.append({
                                'target': 'x',
                                'visual-type': 'line',
                                'object-type': 'entry-price',
                                'marker-label': '',
                                'values': position['timestamp'],
                            })
                            objects.append({
                                'target': 'ohlc',
                                'visual-type': 'line',
                                'object-type': 'entry-price',
                                'marker-label': str(position['entry_price']),
                                'values': position['entry_price'],
                            })
                            objects.append({
                                'target': 'ohlc',
                                'visual-type': 'line',
                                'object-type': 'current-price',
                                'marker-label': str(position['mark_price']),
                                'line-label': str(position['pnl']),
                                'values': put_numbers_pair(current_timestamp, position['mark_price']),
                            })
                            objects.append({
                                'target': 'ohlc',
                                'visual-type': 'line',
                                'object-type': 'liquidation-price',
                                'marker-label': str(position['liquidation_price']),
                                'values': put_numbers_pair(current_timestamp, position['liquidation_price']),
                            })
                            objects.append({
                                'target': 'ohlc',
                                'visual-type': 'line',
                                'object-type': 'trailing-stop',
                                'marker-label': str(position['trailing_stop']),
                                'values': put_numbers_pair(current_timestamp, position['trailing_stop']),
                            })
                        if 'open_orders' in side_d:
                            open_orders = side_d['open_orders']
                            for open_order in open_orders:
                                if any(x in open_order['order'] for x in ('Open', 'Buy')):
                                    marker_label = str(open_order['price'])
                                    if open_order['tp_sl']:
                                        marker_label = f"{marker_label} ({open_order['tp_sl']})"
                                    objects.append({
                                        'target': 'ohlc',
                                        'visual-type': 'line',
                                        'object-type': 'open-order',
                                        'marker-label': marker_label,
                                        'values': put_numbers_pair(current_timestamp, open_order['price']),
                                    })
                                elif any(x in open_order['order'] for x in ('Close', 'Sell')):
                                    marker_label = str(open_order['price'])
                                    if open_order['tp_sl']:
                                        marker_label = f"{marker_label} ({open_order['tp_sl']})"
                                    objects.append({
                                        'target': 'ohlc',
                                        'visual-type': 'line',
                                        'object-type': 'close-order',
                                        'marker-label': marker_label,
                                        'values': put_numbers_pair(current_timestamp, open_order['price']),
                                    })
                                elif 'TakeProfit' in open_order['order']:
                                    objects.append({
                                        'target': 'ohlc',
                                        'visual-type': 'line',
                                        'object-type': 'take-profit',
                                        'marker-label': str(open_order['price']),
                                        'line-label': open_order['tp_sl'],
                                        'values': put_numbers_pair(current_timestamp, open_order['price']),
                                    })
                                elif 'Stop' in open_order['order']:
                                    objects.append({
                                        'target': 'ohlc',
                                        'visual-type': 'line',
                                        'object-type': 'stop-loss',
                                        'marker-label': str(open_order['price']),
                                        'line-label': open_order['tp_sl'],
                                        'values': put_numbers_pair(current_timestamp, open_order['price']),
                                    })
                                else:
                                    line_label = open_order['tp_sl'] if open_order['tp_sl'] else open_order['order']
                                    objects.append({
                                        'target': 'ohlc',
                                        'visual-type': 'line',
                                        'object-type': 'other',
                                        'marker-label': str(open_order['price']),
                                        'line-label': line_label,
                                        'values': put_numbers_pair(current_timestamp, open_order['price']),
                                    })
                        if ('closed_orders' in side_d and 'position' not in side_d and
                                'open_orders' not in side_d):
                            closed_orders = side_d['closed_orders']
                            if closed_orders:
                                closed_order = max(closed_orders, key=lambda x: x['timestamp'])
                                line_label = closed_order['tp_sl'] if closed_order['tp_sl'] else closed_order['order']
                                objects.append({
                                    'target': 'ohlc',
                                    'visual-type': 'marker-and-line',
                                    'object-type': 'closed-order',
                                    'marker-label': str(closed_order['price']),
                                    'line-label': line_label,
                                    'values': put_numbers_pair(closed_order['timestamp'], closed_order['price']),
                                })
                                b_last_update = True
                        b_add_update = b_add_update or objects
                        if b_add_update:
                            try:
                                await self._charts_space.add_update_auto_chart(
                                    first_timestamp=first_timestamp,
                                    contract=contract,
                                    side=side,
                                    timeframe='1m',
                                    price_type='OHLCV',
                                    objects=objects,
                                    chart_type='candlestick',
                                    complex=False,
                                    last_update=b_last_update
                                )
                            except:
                                traceback.print_exc()
        except:
            traceback.print_exc()
