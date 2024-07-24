from nicegui import ui
from typing import Union

from bots_platform.model import ExchangeModel
from bots_platform.gui.spaces import Columns
from bots_platform.model.utils import get_exchange_trade_url, get_trading_view_url


class MarketsSpace:
    STATISTICS_TABLE = 'STATISTICS_TABLE'
    FILTER_UPDATE_ROW = 'FILTER_UPDATE_ROW'
    UPDATE_BUTTON = 'UPDATE_BUTTON'
    FILTER_INPUT = 'FILTER_INPUT'
    MARKETS_TABLE = 'MARKETS_TABLE'
    UPDATE_MARKETS_TIMER = 'UPDATE_MARKETS_TIMER'

    def __init__(self):
        self._exchange_model: Union[ExchangeModel, None] = None
        self._market_space = None
        self._elements = dict()
        self._constructed = False

    async def init(self):
        self._elements.clear()
        if self._market_space:
            self._market_space.delete()
        self._market_space = ui.card().classes('items-center')
        await self.update()
        self._constructed = True

    async def update(self):
        notification = ui.notification(timeout=8, close_button=True)
        notification.message = 'Fetching markets...'
        notification.spinner = True

        async def update_markets_callback():
            if self._constructed:
                self._delete_update_markets_timer()
                await self.update()

        with self._market_space:

            if MarketsSpace.UPDATE_BUTTON not in self._elements:
                update_button = ui.button('Update',
                                          on_click=lambda *_: update_markets_callback()).classes('m-auto')
                self._elements[MarketsSpace.UPDATE_BUTTON] = update_button

            stat_metrics = [
                ('DateTime', 'datetime_fstring'),
                ('Cryptocurrencies', 'cryptocurrencies_fstring'),
                ('Markets', 'markets_fstring'),
                ('Active Exchanges', 'active_exchanges_fstring'),
                ('Market Cap (Total; De-Fi)', 'market_cap_fstring'),
                ('Volume 24h (Spot; Stablecoin; De-Fi; Derivatives)', 'volume_24h_fstring'),
                ('Dominance (BTC; ETH)', 'dominance_fstring'),
                ('Fear and Greed Index', 'fear_greed_index_fstring'),
                ('Altcoin Index (Season, Month, Year)', 'alt_coin_index_fstring'),
                ('Top Cryptos', 'top_cryptos_fstring'),
            ]
            stat_metrics_rows = []
            try:
                data: dict = await self._exchange_model.fetch_market_statistics()
                for metric_name, metric_key in stat_metrics:
                    metric_value = data[metric_key]
                    stat_metrics_rows.append({
                        'metric': metric_name,
                        'value': metric_value,
                    })
            except:
                pass

            if MarketsSpace.STATISTICS_TABLE not in self._elements:
                ui.separator()
                ui.label('Global market')
                table = ui.table(columns=Columns.MARKETS_STATISTICS_COLUMNS, rows=stat_metrics_rows, row_key='metric'
                                 ).style("width: 800px;").props('table-header-class=hidden')
                self._elements[MarketsSpace.STATISTICS_TABLE] = table
            else:
                table = self._elements[MarketsSpace.STATISTICS_TABLE]
                table.update_rows(stat_metrics_rows)

            if MarketsSpace.FILTER_INPUT not in self._elements:
                ui.separator()
                ui.label('Bybit market')
                filter_input = ui.input('Filter')
                self._elements[MarketsSpace.FILTER_INPUT] = filter_input
            else:
                filter_input = self._elements[MarketsSpace.FILTER_INPUT]

            words = {'spot', 'linear', 'inverse'}
            markets_rows = []
            try:
                markets_rows: list = await self._exchange_model.fetch_markets()
                for x in markets_rows:
                    x['key'] = f"{x['type']} {x['symbol']} {x['launch_timestamp']}"
                    x['exchange_link'] = get_exchange_trade_url(x['symbol'])
                    x['tv_link'] = get_trading_view_url(x['symbol'])
                    words.add(x['symbol'])
            except:
                pass
            filter_input.set_autocomplete(list(words))

            if MarketsSpace.MARKETS_TABLE not in self._elements:
                table = ui.table(columns=Columns.MARKETS_TABLE_COLUMNS, rows=markets_rows, row_key='key',
                                 pagination=10).style("width: 1250px;")
                table.add_slot('body-cell-type', '''
                     <q-td :props="props">
                         <a :href="props.row.exchange_link" target="_blank">{{ props.row.type }}</a>
                     </q-td>
                ''')
                table.add_slot('body-cell-symbol', '''
                     <q-td :props="props">
                         <a :href="props.row.tv_link" target="_blank">{{ props.row.symbol }}</a>
                     </q-td>
                 ''')
                self._elements[MarketsSpace.MARKETS_TABLE] = table
                filter_input.bind_value_to(table, 'filter')
            else:
                table = self._elements[MarketsSpace.MARKETS_TABLE]
                table.update_rows(markets_rows)

            self._elements[MarketsSpace.UPDATE_MARKETS_TIMER] = ui.timer(60 * 60,  # 1 hour (60 minutes, 3600 seconds)
                                                                         callback=lambda *_: update_markets_callback(),
                                                                         once=True)

        notification.spinner = False
        notification.dismiss()

    def check(self):
        if self._market_space is None or self._exchange_model is None:
            raise Exception(f'{type(self).__name__} is not initialized')

    def set_exchange_model(self, model: ExchangeModel):
        self._exchange_model = model

    def detach(self):
        try:
            self._delete_update_markets_timer()
            self._market_space.delete()
        except:
            pass
        self._constructed = False
        self._elements.clear()
        self._market_space = None

    def _delete_update_markets_timer(self):
        if MarketsSpace.UPDATE_MARKETS_TIMER in self._elements:
            try:
                update_markets_timer = self._elements.pop(MarketsSpace.UPDATE_MARKETS_TIMER)
                update_markets_timer.cancel()
                update_markets_timer.delete()
            except:
                pass
