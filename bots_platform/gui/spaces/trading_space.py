from nicegui import ui
from typing import Union

from bots_platform.model import ExchangeModel
from bots_platform.model.utils import get_exchange_trade_url
from bots_platform.gui.spaces import Columns


class TradingSpace:
    UPDATE_BUTTON = 'UPDATE_BUTTON'
    FILTER_INPUT = 'FILTER_INPUT'
    POSITIONS_TABLE = 'POSITIONS_TABLE'
    OPEN_ORDERS_TABLE = 'OPEN_ORDERS_TABLE'
    CLOSED_ORDERS_TABLE = 'CLOSED_ORDERS_TABLE'
    CANCELED_ORDERS_TABLE = 'CANCELED_ORDERS_TABLE'
    LEDGER_TABLE = 'LEDGER_TABLE'
    UPDATE_TRADING_TIMER = 'UPDATE_TRADING_TIMER'

    def __init__(self):
        self._exchange_model: Union[ExchangeModel, None] = None
        self._trading_space = None
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
        notification = ui.notification(timeout=8, close_button=True)
        notification.message = 'Fetching trading info...'
        notification.spinner = True

        async def update_trading_callback():
            if self._constructed:
                self._delete_update_trading_timer()
                await self.update()

        with self._trading_space:

            if TradingSpace.UPDATE_BUTTON not in self._elements:
                update_button = ui.button('Update',
                                          on_click=lambda *_: update_trading_callback()).classes('m-auto')
                self._elements[TradingSpace.UPDATE_BUTTON] = update_button

            if TradingSpace.FILTER_INPUT not in self._elements:
                filter_input = ui.input('Filter')
                self._elements[TradingSpace.FILTER_INPUT] = filter_input
            else:
                filter_input = self._elements[TradingSpace.FILTER_INPUT]
            autocomplete = set()

            positions = []
            open_orders = []
            closed_orders = []
            canceled_orders = []
            try:
                positions_and_orders = await self._exchange_model.fetch_all_positions_and_orders()
                positions = positions_and_orders['positions']
                open_orders = positions_and_orders['open_orders']
                closed_orders = positions_and_orders['closed_orders']
                canceled_orders = positions_and_orders['canceled_orders']
            except:
                pass
            ledger: list = []
            try:
                ledger = await self._exchange_model.fetch_ledger()
            except:
                pass

            for x in positions:
                x['key'] = f"{x['datetime']} {x['contract']} {x['size']} {x['side']} {x['leverage']} {x['entry_price']}"
                x['exchange_link'] = get_exchange_trade_url(x['contract'])
                autocomplete.add(x['contract'])
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

            for x in open_orders:
                x['key'] = f"{x['datetime']} {x['contract']} {x['size']} {x['side']} {x['order']} {x['price']}"
                x['exchange_link'] = get_exchange_trade_url(x['contract'])
                autocomplete.add(x['contract'])
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

            for x in closed_orders:
                x['key'] = f"{x['datetime']} {x['contract']} {x['size']} {x['side']} {x['order']} {x['price']}"
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

            for x in canceled_orders:
                x['key'] = f"{x['datetime']} {x['contract']} {x['size']} {x['side']} {x['order']} {x['reason']}"
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

            self._elements[TradingSpace.UPDATE_TRADING_TIMER] = ui.timer(10,  # 10 seconds
                                                                         callback=lambda *_: update_trading_callback(),
                                                                         once=True)

        notification.spinner = False
        notification.dismiss()

    def check(self):
        if self._trading_space is None or self._exchange_model is None:
            raise Exception(f'{type(self).__name__} is not initialized')

    def set_exchange_model(self, model: ExchangeModel):
        self._exchange_model = model

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
