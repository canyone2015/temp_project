from nicegui import ui
from typing import Union

from bots_platform.model import ExchangeModel
from bots_platform.gui.spaces import Columns
from bots_platform.model.utils import get_exchange_trade_url, get_trading_view_url


class MarketsSpace:
    FEAR_GREED_INDEX_LABEL = 'FEAR_GREED_INDEX_LABEL'
    MARKET_CAP_LABEL = 'MARKET_CAP_LABEL'
    VOLUME_LABEL = 'VOLUME_LABEL'
    DOMINANCE_LABEL = 'DOMINANCE_LABEL'
    ALT_COIN_INDEX_LABEL = 'ALT_COIN_INDEX_LABEL'
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

            fear_greed_index_fstring = ''
            fear_greed_index_url = ''
            market_cap_fstring = ''
            market_cap_url = ''
            volume_fstring = ''
            volume_url = ''
            dominance_fstring = ''
            dominance_url = ''
            alt_coin_index_fstring = ''
            alt_coin_index_url = ''
            try:
                data: dict = await self._exchange_model.fetch_market_statistics()
                datetime_fstring = data['datetime_fstring']
                fear_greed_index_fstring = data['fear_greed_index_fstring']
                fear_greed_index_fstring = f"{datetime_fstring} – {fear_greed_index_fstring}"
                fear_greed_index_url = data['fear_greed_index_url']
                market_cap_fstring = data['market_cap_fstring']
                market_cap_url = data['market_cap_url']
                volume_fstring = data['24h_volume_fstring']
                volume_url = data['24h_volume_url']
                dominance_fstring = data['dominance_fstring']
                dominance_url = data['dominance_url']
                alt_coin_index_fstring = data['alt_coin_index_fstring']
                alt_coin_index_url = data['alt_coin_index_url']
            except:
                pass

            if MarketsSpace.FEAR_GREED_INDEX_LABEL not in self._elements:
                fear_greed_index_label = ui.link(fear_greed_index_fstring,
                                                 fear_greed_index_url,
                                                 new_tab=True)
                self._elements[MarketsSpace.FEAR_GREED_INDEX_LABEL] = fear_greed_index_label
            else:
                self._elements[MarketsSpace.FEAR_GREED_INDEX_LABEL].set_text(fear_greed_index_fstring)

            if MarketsSpace.MARKET_CAP_LABEL not in self._elements:
                market_cap_label = ui.link(market_cap_fstring,
                                           market_cap_url,
                                           new_tab=True)
                self._elements[MarketsSpace.MARKET_CAP_LABEL] = market_cap_label
            else:
                self._elements[MarketsSpace.MARKET_CAP_LABEL].set_text(market_cap_fstring)

            if MarketsSpace.VOLUME_LABEL not in self._elements:
                volume_label = ui.link(volume_fstring,
                                       volume_url,
                                       new_tab=True)
                self._elements[MarketsSpace.VOLUME_LABEL] = volume_label
            else:
                self._elements[MarketsSpace.VOLUME_LABEL].set_text(volume_fstring)

            if MarketsSpace.DOMINANCE_LABEL not in self._elements:
                dominance_label = ui.link(dominance_fstring,
                                          dominance_url,
                                          new_tab=True)
                self._elements[MarketsSpace.DOMINANCE_LABEL] = dominance_label
            else:
                self._elements[MarketsSpace.DOMINANCE_LABEL].set_text(dominance_fstring)

            if MarketsSpace.ALT_COIN_INDEX_LABEL not in self._elements:
                alt_coin_index_label = ui.link(alt_coin_index_fstring,
                                               alt_coin_index_url,
                                               new_tab=True)
                self._elements[MarketsSpace.ALT_COIN_INDEX_LABEL] = alt_coin_index_label
                alt_coin_index_label.tooltip("""
                If 75% of the Top 50 coins performed better than Bitcoin over the last season (90 days) / last month (30 days) / last year it is Altcoin Season / Month / Year.
                """.strip())
            else:
                self._elements[MarketsSpace.ALT_COIN_INDEX_LABEL].set_text(alt_coin_index_fstring)

            if MarketsSpace.FILTER_INPUT not in self._elements:
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
