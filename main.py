import string
import traceback
import asyncio
from datetime import datetime, timezone
from decimal import Decimal
import ccxt
from nicegui import ui
import urllib.request
import json
import pprint


class BotData:
    config4exchange: dict
    exchange: ccxt.bybit
    gui: dict
    fee: Decimal


g_bot_data = BotData()
g_bot_data.config4exchange = {
    'apiKey': '8MOZNveF4mxaOINkZE',  # 'd0CBRJfXahg4MNayag',
    'secret': '9sT5mCZondAz0WijmQOBdDCVM9KqJBu4JLv7',  # 'V4BJCIwuxIGyhpUPBC3cxo6S0Qs7QFD4G2DP',
}
g_bot_data.gui = dict()


class Elements:
    INIT_BUTTON = 'INIT_BUTTON'
    QUIT_BUTTON = 'QUIT_BUTTON'
    MAIN_SPACE = 'MAIN_SPACE'
    LOGIN_SPACE = 'LOGIN_SPACE'
    BALANCE_SPACE = 'BALANCE_SPACE'
    MARKETS_SPACE = 'CURRENCIES_SPACE'
    API_KEY_INPUT = 'API_KEY_INPUT'
    API_SECRET_INPUT = 'API_SECRET_INPUT'
    TESTNET_CHECKBOX = 'TESTNET_CHECKBOX'
    UPDATE_BALANCE_BUTTON = 'UPDATE_BALANCE_BUTTON'
    UPDATE_BALANCE_TIMER = 'UPDATE_BALANCE_TIMER'
    BALANCE_TABLE = 'BALANCE_TABLE'
    UPDATE_MARKETS_BUTTON = 'UPDATE_MARKETS_BUTTON'
    LOG_SPACE = 'LOG_SPACE'
    UNIFIED_INFO_COL = 'UNIFIED_INFO_ROW'
    TRADING_ACCOUNT_LINK = 'TRADING_ACCOUNT_LINK'
    MARGIN_MODE_ROW = 'MARGIN_MODE_ROW'
    UPDATE_QUIT_ROW = 'UPDATE_QUIT_ROW'
    FEAR_GREED_INDEX_LABEL = 'FEAR_GREED_INDEX_LABEL'
    MARKETS_TABLE = 'MARKETS_TABLE'
    FILTER_UPDATE_ROW = 'FILTER_UPDATE_ROW'
    INPUT_FILTER = 'INPUT_FILTER'
    TRADING_BOTS_SPACE = 'TRADING_BOT_SPACE'
    TRADING_SPACE = 'TRADING_SPACE'
    OPEN_ORDERS_BOX = 'OPEN_ORDERS_BOX'
    CLOSED_ORDERS_BOX = 'CLOSED_ORDERS_BOX'
    CANCELED_ORDERS_BOX = 'CANCELED_ORDERS_BOX'
    LEDGER_BOX = 'LEDGER_BOX'
    POSITIONS_BOX = 'POSITIONS_BOX'
    POSITIONS_TABLE = 'POSITIONS_TABLE'
    OPEN_ORDERS_TABLE = 'OPEN_ORDERS_TABLE'
    CLOSED_ORDERS_TABLE = 'CLOSED_ORDERS_TABLE'
    LEDGER_TABLE = 'LEDGER_TABLE'
    CANCELED_ORDERS_TABLE = 'CANCELED_ORDERS_TABLE'
    UPDATE_TRADING_INFO_BUTTON = 'UPDATE_TRADING_INFO_BUTTON'
    UPDATE_TRADING_INFO_TIMER = 'UPDATE_TRADING_INFO_TIMER'


def log(line):
    s = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {line}"
    if Elements.LOG_SPACE in g_bot_data.gui:
        g_bot_data.gui[Elements.LOG_SPACE].push(s)
    print(s)


def dt_from_timestamp(timestamp):
    try:
        return datetime.utcfromtimestamp(timestamp)
    except:
        return datetime.utcfromtimestamp(timestamp / 1000)


def utc_to_local(utc_dt):
    return utc_dt.replace(tzinfo=timezone.utc).astimezone(tz=None)


def local_dt_from_timestamp(timestamp):
    return utc_to_local(dt_from_timestamp(timestamp))


def format_time(dt):
    return dt.strftime('%Y-%m-%d %H:%M:%S')


def remove_from_gui(gui_element):
    if gui_element in g_bot_data.gui:
        g_bot_data.gui[gui_element].delete()
        g_bot_data.gui.pop(gui_element)


def get_symbol(symbol):
    symbol = symbol.split('/')
    if len(symbol) != 2:
        return []
    symbol[1] = symbol[1][:symbol[1].find(':')]
    return symbol


async def update_balance():
    if Elements.BALANCE_SPACE not in g_bot_data.gui:
        return

    notification = ui.notification(timeout=8, close_button=True)
    notification.message = 'Fetching balance...'
    notification.spinner = True

    loop = asyncio.get_event_loop()
    margin_mode = 'isolated'
    balance = {}
    try:
        balance = await loop.run_in_executor(None, g_bot_data.exchange.fetch_balance)
        balance = dict(balance)
        if balance['info']['retMsg'] != 'OK':
            ui.notify("Fetching balance error", type='negative')
            log(f'[ERROR] Fetching balance error')
        if balance['info']['result']['list'][0]['totalMarginBalance'] == '':
            margin_mode = 'isolated'
        else:
            margin_mode = 'cross'
    except Exception as e:
        log(f'[ERROR] {e}')
        traceback.print_exc()
    unified_account = False
    try:
        _, unified_account = await loop.run_in_executor(None, g_bot_data.exchange.is_unified_enabled)
    except Exception as e:
        log(f'[ERROR] {e}')
        traceback.print_exc()
    try:
        update_balance_gui(balance, margin_mode, unified_account)
    except Exception as e:
        log(f'[ERROR] {e}')
        traceback.print_exc()

    notification.spinner = False
    notification.dismiss()


def update_balance_gui(balance, margin_mode, unified_account):
    if Elements.BALANCE_SPACE not in g_bot_data.gui:
        return

    def dialog_yes():
        dialog.close()
        quit_action()

    def dialog_no():
        dialog.close()

    balance_space = g_bot_data.gui[Elements.BALANCE_SPACE]
    with balance_space:

        async def upgrade_unified_trade_account():
            try:
                g_bot_data.exchange.upgrade_unified_trade_account()
                await update_balance()
                quit_action()
            except Exception as e:
                log(f'[ERROR] {e}')
                traceback.print_exc()

        if Elements.UNIFIED_INFO_COL not in g_bot_data.gui:
            g_bot_data.gui[Elements.UNIFIED_INFO_COL] = ui.column().classes('w-full items-center')
        else:
            g_bot_data.gui[Elements.UNIFIED_INFO_COL].clear()
        unified_info_col = g_bot_data.gui[Elements.UNIFIED_INFO_COL]
        if not unified_account:
            with unified_info_col:
                ui.label('Not unified account!')
                ui.button('Upgrade to unified account',
                          on_click=lambda *_: upgrade_unified_trade_account())
                with ui.dialog() as dialog, ui.card().classes('items-center'):
                    ui.label('Are you sure you want to quit?')
                    with ui.row():
                        ui.button('Yes', on_click=dialog_yes)
                        ui.button('No', on_click=dialog_no)
                g_bot_data.gui[Elements.QUIT_BUTTON] = ui.button('Quit', on_click=dialog.open).classes("m-auto")
            return
        else:
            unified_info_col.clear()

        if Elements.TRADING_ACCOUNT_LINK not in g_bot_data.gui:
            g_bot_data.gui[Elements.TRADING_ACCOUNT_LINK] = ui.link(f'Trading Account',
                                                                    'https://www.bybit.com/user/assets/home/tradingaccount',
                                                                    new_tab=True)
        columns = [
            {'name': 'coin', 'label': 'Coin', 'field': 'coin', 'align': 'center', 'sortable': True},
            {'name': 'used', 'label': 'Used', 'field': 'used', 'align': 'center', 'sortable': True,
             ':sort': '(a, b, rowA, rowB) => rowA.used_hidden - rowB.used_hidden'},
            {'name': 'free', 'label': 'Free', 'field': 'free', 'align': 'center', 'sortable': True,
             ':sort': '(a, b, rowA, rowB) => rowA.free_hidden - rowB.free_hidden'},
            {'name': 'used_hidden', 'label': 'Used Hidden', 'field': 'used_hidden', 'align': 'center',
             'classes': 'hidden', 'headerClasses': 'hidden'},
            {'name': 'free_hidden', 'label': 'Free Hidden', 'field': 'free_hidden', 'align': 'center',
             'classes': 'hidden', 'headerClasses': 'hidden'},
        ]
        rows = []
        if 'info' in balance:
            for account_balance_list in balance['info']['result']['list']:
                if account_balance_list['accountType'] != 'UNIFIED':
                    continue
                for account_balance in account_balance_list['coin']:
                    coin_name = account_balance['coin']
                    free = Decimal(account_balance['availableToWithdraw'])
                    wallet_balance = Decimal(account_balance['walletBalance'])
                    locked = wallet_balance - free
                    pnl = Decimal(account_balance['unrealisedPnl'])
                    usd_value = Decimal(account_balance['usdValue'])
                    if round(usd_value, 3) == 0:
                        continue
                    used_coin = f"{round(locked, 6)}{round(pnl, 6):+.3f}" if pnl else f"{round(locked, 6)}"
                    free_coin = f"{round(free, 6)}"
                    locked *= usd_value / (wallet_balance or 1)
                    pnl *= usd_value / (wallet_balance or 1)
                    free *= usd_value / (wallet_balance or 1)
                    used_usd = f"{round(locked, 6)}{round(pnl, 6):+.3f}" if pnl else f"{round(locked, 6)}"
                    free_usd = f"{round(free, 6)}"
                    used_usd_hidden = locked + pnl
                    free_usd_hidden = free
                    used_string = f"{used_coin} {coin_name} / ${used_usd}"
                    free_string = f"{free_coin} {coin_name} / ${free_usd}"
                    if not any(x in used_string for x in '123456789'):
                        used_string = '–'
                    if not any(x in free_string for x in '123456789'):
                        free_string = '–'
                    if any(x in '123456789' for x in used_usd + free_usd):
                        rows.append({
                            'coin': coin_name,
                            'used': used_string,
                            'free': free_string,
                            'used_hidden': used_usd_hidden,
                            'free_hidden': free_usd_hidden,
                        })

        if Elements.BALANCE_TABLE in g_bot_data.gui:
            table = g_bot_data.gui[Elements.BALANCE_TABLE]
            table.update_rows(rows)
        else:
            g_bot_data.gui[Elements.BALANCE_TABLE] = ui.table(columns=columns,
                                                              rows=rows,
                                                              row_key='name').classes('col-span-2 justify-center items-center justify-self-center')

        async def switch_margin_mode():
            try:
                if 'cross' in margin_mode:
                    s = 'isolated'
                elif 'isolated' in margin_mode:
                    s = 'cross'
                else:
                    s = 'isolated'
                response = g_bot_data.exchange.set_margin_mode(s)
                await update_balance()
                ui.notify(f'{response}', type='info')
            except Exception as e:
                ui.notify(f'{e}', type='negative')
                log(f'[ERROR] {e}')
                traceback.print_exc()
                return

        if Elements.MARGIN_MODE_ROW in g_bot_data.gui:
            g_bot_data.gui[Elements.MARGIN_MODE_ROW].clear()
        else:
            g_bot_data.gui[Elements.MARGIN_MODE_ROW] = ui.row()
        margin_mode_row = g_bot_data.gui[Elements.MARGIN_MODE_ROW]
        with margin_mode_row:
            if 'cross' in margin_mode:
                s = 'Cross Margin'
            elif 'isolated' in margin_mode:
                s = 'Isolated Margin'
            else:
                s = 'Portfolio Margin'
            ui.label(s).classes("m-auto")
            ui.button('switch', on_click=lambda *_: switch_margin_mode()).classes("m-auto")

        async def update_balance_callback():
            if Elements.UPDATE_BALANCE_TIMER in g_bot_data.gui:
                timer = g_bot_data.gui.pop(Elements.UPDATE_BALANCE_TIMER)
                timer.cancel()
                timer.delete()
            await update_balance()

        if Elements.UPDATE_BALANCE_TIMER in g_bot_data.gui:
            g_bot_data.gui[Elements.UPDATE_BALANCE_TIMER].delete()
        g_bot_data.gui[Elements.UPDATE_BALANCE_TIMER] = ui.timer(5.0,
                                                                 callback=lambda: update_balance_callback(), once=True)

        if Elements.UPDATE_QUIT_ROW not in g_bot_data.gui:
            g_bot_data.gui[Elements.UPDATE_QUIT_ROW] = update_quit_row = ui.row()
            with update_quit_row:
                g_bot_data.gui[Elements.UPDATE_BALANCE_BUTTON] = ui.button('Update',
                                                                           on_click=lambda
                                                                               *_: update_balance_callback()).classes(
                    "m-auto")
                with ui.dialog() as dialog, ui.card().classes('items-center'):
                    ui.label('Are you sure you want to quit?')
                    with ui.row():
                        ui.button('Yes', on_click=dialog_yes)
                        ui.button('No', on_click=dialog_no)
                g_bot_data.gui[Elements.QUIT_BUTTON] = ui.button('Quit', on_click=dialog.open).classes("m-auto")


async def update_markets():
    if Elements.MARKETS_SPACE not in g_bot_data.gui:
        return

    notification = ui.notification(timeout=8, close_button=True)
    notification.message = 'Fetching markets...'
    notification.spinner = True

    loop = asyncio.get_event_loop()
    fear_greed_index = ''
    try:
        url = "https://api.alternative.me/fng/?limit=1"
        jsonurl = urllib.request.urlopen(url)
        obj = json.loads(jsonurl.read())
        value = str(obj['data'][0]['value'])
        value_classification = str(obj['data'][0]['value_classification'])
        datetime_string = format_time(local_dt_from_timestamp(int(obj['data'][0]['timestamp'])))
        fear_greed_index = f"{datetime_string} – Fear and Greed Index: {value} ({value_classification}) "
    except Exception as e:
        log(f'[ERROR] {e}')
        traceback.print_exc()

    markets_data = []
    spot_source_pairs = set()
    future_source_pairs = set()
    for x in list(await loop.run_in_executor(None, g_bot_data.exchange.fetch_markets)):
        if x['active'] and (x['expiry'] is None or x['expiryDatetime'] is None) and 'USDT' in x['symbol']:
            source_pair = x['symbol']
            if x['spot']:
                spot_source_pairs.add(source_pair)
            elif ':' in x['symbol']:
                future_source_pairs.add(source_pair)
    if spot_source_pairs:
        try:
            while True:
                try:
                    tickers = await loop.run_in_executor(None, g_bot_data.exchange.fetch_tickers,
                                                         list(spot_source_pairs))
                    break
                except ccxt.BadSymbol as e:
                    s = f"{e}"
                    p = 'market symbol'
                    if p in s:
                        spot_source_pairs.discard(s[s.rfind(p) + len(p):].strip())
            for pair, ticker in tickers.items():
                close_price_24h = Decimal(ticker['info']['lastPrice'])
                open_price_24h = Decimal(ticker['info']['prevPrice24h'])
                high_price_24h = Decimal(ticker['info']['highPrice24h'])
                low_price_24h = Decimal(ticker['info']['lowPrice24h'])
                open_close_percent = round((close_price_24h / open_price_24h - 1) * 100, 6)
                low_high_percent = round((high_price_24h / low_price_24h - 1) * 100, 6)
                volume_24h = Decimal(ticker['info']['turnover24h'])
                vwap = Decimal(ticker['vwap'] or close_price_24h)
                last_trend = round((close_price_24h / vwap - 1) * 100, 6)
                markets_data.append({
                    "type": "spot",
                    "pair": pair,
                    "open_price_24h": open_price_24h,
                    "low_price_24h": low_price_24h,
                    "high_price_24h": high_price_24h,
                    "close_price_24h": close_price_24h,
                    "open_close_percent": open_close_percent,
                    "low_high_percent": low_high_percent,
                    "volume_24h": volume_24h,
                    "last_trend": last_trend
                })
        except Exception as e:
            log(f'[ERROR] {e}')
            traceback.print_exc()
    if future_source_pairs:
        try:
            while True:
                try:
                    tickers = await loop.run_in_executor(None, g_bot_data.exchange.fetch_tickers,
                                                         list(future_source_pairs))
                    break
                except ccxt.BadSymbol as e:
                    s = f"{e}"
                    p = 'market symbol'
                    if p in s:
                        future_source_pairs.discard(s[s.rfind(p) + len(p):].strip())
            for pair, ticker in tickers.items():
                idx = pair.find(':')
                if idx != -1:
                    pair = pair[:idx]
                else:
                    continue
                close_price_24h = Decimal(ticker['info']['markPrice'])
                open_price_24h = Decimal(ticker['info']['prevPrice24h'])
                high_price_24h = Decimal(ticker['info']['highPrice24h'])
                low_price_24h = Decimal(ticker['info']['lowPrice24h'])
                open_close_percent = round((close_price_24h / open_price_24h - 1) * 100, 6)
                low_high_percent = round((high_price_24h / low_price_24h - 1) * 100, 6)
                volume_24h = Decimal(ticker['info']['turnover24h'])
                vwap = Decimal(ticker['vwap'])
                last_trend = round((close_price_24h / vwap - 1) * 100, 6)
                markets_data.append({
                    "type": "future",
                    "pair": pair,
                    "open_price_24h": open_price_24h,
                    "low_price_24h": low_price_24h,
                    "high_price_24h": high_price_24h,
                    "close_price_24h": close_price_24h,
                    "open_close_percent": open_close_percent,
                    "low_high_percent": low_high_percent,
                    "volume_24h": volume_24h,
                    "last_trend": last_trend
                })
        except Exception as e:
            log(f'[ERROR] {e}')
            traceback.print_exc()
    try:
        update_markets_gui(markets_data, fear_greed_index)
    except Exception as e:
        log(f'[ERROR] {e}')
        traceback.print_exc()

    notification.spinner = False
    notification.dismiss()


def update_markets_gui(markets_data, fear_greed_index):
    if Elements.MARKETS_SPACE not in g_bot_data.gui:
        return

    markets_space = g_bot_data.gui[Elements.MARKETS_SPACE]
    with markets_space:
        if Elements.FEAR_GREED_INDEX_LABEL in g_bot_data.gui:
            g_bot_data.gui[Elements.FEAR_GREED_INDEX_LABEL].set_text(fear_greed_index)
        else:
            g_bot_data.gui[Elements.FEAR_GREED_INDEX_LABEL] = ui.link(fear_greed_index,
                                                                      'https://alternative.me/crypto/fear-and-greed-index/',
                                                                      new_tab=True)

        async def update_markets_callback():
            await update_markets()

        if Elements.FILTER_UPDATE_ROW not in g_bot_data.gui:
            g_bot_data.gui[Elements.FILTER_UPDATE_ROW] = filter_update_row = ui.row().classes(
                'justify-center items-center')
            with filter_update_row:
                g_bot_data.gui[Elements.INPUT_FILTER] = input_filter = ui.input('Filter')
                ui.button('Update', on_click=lambda *_: update_markets_callback()).classes('m-auto')
        else:
            input_filter = g_bot_data.gui[Elements.INPUT_FILTER]

        columns = [
            {'name': 'key', 'label': 'Key', 'field': 'key', 'align': 'center', 'sortable': True,
             'classes': 'hidden', 'headerClasses': 'hidden'},
            {'name': 'type', 'label': 'Type', 'field': 'type', 'align': 'center', 'sortable': True},
            {'name': 'pair', 'label': 'Pair', 'field': 'pair', 'align': 'center', 'sortable': True},
            {'name': 'tv_link', 'label': 'TV Link', 'field': 'tv_link', 'align': 'center',
             'classes': 'hidden', 'headerClasses': 'hidden'},
            {'name': 'exchange_link', 'label': 'Exchange Link', 'field': 'exchange_link', 'align': 'center',
             'classes': 'hidden', 'headerClasses': 'hidden'},
            {'name': 'last_trend', 'label': 'Last Trend', 'field': 'last_trend', 'align': 'center', 'sortable': True},
            {'name': 'open_price_24h', 'label': 'Open 24h', 'field': 'open_price_24h', 'align': 'center',
             'sortable': True},
            {'name': 'low_price_24h', 'label': 'Low 24h', 'field': 'low_price_24h', 'align': 'center',
             'sortable': True},
            {'name': 'high_price_24h', 'label': 'High 24h', 'field': 'high_price_24h', 'align': 'center',
             'sortable': True},
            {'name': 'close_price_24h', 'label': 'Close 24h', 'field': 'close_price_24h', 'align': 'center',
             'sortable': True},
            {'name': 'open_close_percent', 'label': 'Open-Close %', 'field': 'open_close_percent', 'align': 'center',
             'sortable': True},
            {'name': 'low_high_percent', 'label': 'Low-High %', 'field': 'low_high_percent', 'align': 'center',
             'sortable': True},
            {'name': 'volume_24h', 'label': 'USDT Volume 24h', 'field': 'volume_24h', 'align': 'center',
             'sortable': True},
        ]
        rows = []
        pairs = []
        for x in markets_data:
            pair = x['pair']
            if x['type'] == 'spot':
                spot_format = lambda \
                        s: f"https://ru.tradingview.com/symbols/{''.join(x for x in s if x.isalnum())}/?exchange=BYBIT"
                allowed = '/'
                exchange_format = lambda \
                        s: f"https://www.bybit.com/trade/spot/{''.join(x for x in s if x.isalnum() or x in allowed)}"
                rows.append({'key': f'spot {pair}', 'type': 'Spot', 'pair': pair, 'tv_link': spot_format(pair),
                             'exchange_link': exchange_format(pair),
                             'last_trend': x['last_trend'],
                             'open_price_24h': x['open_price_24h'],
                             'low_price_24h': x['low_price_24h'],
                             'high_price_24h': x['high_price_24h'],
                             'close_price_24h': x['close_price_24h'],
                             'open_close_percent': x['open_close_percent'],
                             'low_high_percent': x['low_high_percent'],
                             'volume_24h': x['volume_24h'],
                             })
                pairs.append(pair)
            elif x['type'] == 'future':
                future_format = lambda \
                        s: f"https://ru.tradingview.com/symbols/{''.join(x for x in s if x.isalnum())}.P/?exchange=BYBIT"
                exchange_format = lambda \
                        s: f"https://www.bybit.com/trade/usdt/{''.join(x for x in s if x.isalnum())}"
                rows.append({'key': f'future {pair}', 'type': 'Future', 'pair': pair, 'tv_link': future_format(pair),
                             'exchange_link': exchange_format(pair),
                             'last_trend': x['last_trend'],
                             'open_price_24h': x['open_price_24h'],
                             'low_price_24h': x['low_price_24h'],
                             'high_price_24h': x['high_price_24h'],
                             'close_price_24h': x['close_price_24h'],
                             'open_close_percent': x['open_close_percent'],
                             'low_high_percent': x['low_high_percent'],
                             'volume_24h': x['volume_24h'],
                             })
                pairs.append(pair)

        if Elements.MARKETS_TABLE not in g_bot_data.gui:
            g_bot_data.gui[Elements.MARKETS_TABLE] = table = ui.table(columns=columns, rows=rows, row_key='key',
                                                                      pagination=10).style("max-width: 1250px;")
            table.add_slot('body-cell-type', '''
                 <q-td :props="props">
                     <a :href="props.row.exchange_link" target="_blank">{{ props.row.type }}</a>
                 </q-td>
            ''')
            table.add_slot('body-cell-pair', '''
                 <q-td :props="props">
                     <a :href="props.row.tv_link" target="_blank">{{ props.row.pair }}</a>
                 </q-td>
             ''')
        else:
            table = g_bot_data.gui[Elements.MARKETS_TABLE]
            table.update_rows(rows)

        input_filter.set_autocomplete(pairs)
        input_filter.bind_value_to(table, 'filter')


async def setup_trading_bots():
    if Elements.TRADING_BOTS_SPACE not in g_bot_data.gui:
        return

    notification = ui.notification(timeout=8, close_button=True)
    notification.message = 'Fetching bots...'
    notification.spinner = True
    trading_bots = dict()
    try:
        trading_bots = {
            'Bot-1': {

            },
            'Bot-2': {

            }
        }
    except Exception as e:
        log(f'[ERROR] {e}')
        traceback.print_exc()
    try:
        setup_trading_bots_gui(trading_bots)
    except Exception as e:
        log(f'[ERROR] {e}')
        traceback.print_exc()
    notification.spinner = False
    notification.dismiss()


def setup_trading_bots_gui(trading_bots):
    if Elements.TRADING_BOTS_SPACE not in g_bot_data.gui:
        return

    trading_bot_space = g_bot_data.gui[Elements.TRADING_BOTS_SPACE]
    with trading_bot_space:
        tabs = []
        with ui.tabs().classes('w-full') as tabs_gui:
            for x in trading_bots:
                tabs.append((x, ui.tab(x)))
        if not tabs:
            return
        with ui.tab_panels(tabs_gui, value=tabs[0][1]).classes('items-center'):
            for tab_name, tab_element in tabs:
                with ui.tab_panel(tab_element):
                    card = ui.card().classes('items-center')


async def fetch_positions(symbols=None):
    loop = asyncio.get_event_loop()
    positions = []
    for symbol in (symbols or [None]):
        positions.extend(await loop.run_in_executor(None, g_bot_data.exchange.fetch_positions, symbol))
    return positions


async def fetch_open_orders(symbols=None):
    loop = asyncio.get_event_loop()
    open_orders = []
    for symbol in (symbols or [None]):
        open_orders.extend(await loop.run_in_executor(None, g_bot_data.exchange.fetch_open_orders, symbol))
    return open_orders


async def update_trading_info():
    if Elements.TRADING_SPACE not in g_bot_data.gui:
        return

    notification = ui.notification(timeout=8, close_button=True)
    notification.message = 'Fetching trading info...'
    notification.spinner = True
    trading_info = dict()
    try:
        loop = asyncio.get_event_loop()
        positions = await loop.run_in_executor(None, g_bot_data.exchange.fetch_positions)
        open_orders = await loop.run_in_executor(None, g_bot_data.exchange.fetch_open_orders)
        closed_orders = await loop.run_in_executor(None, g_bot_data.exchange.fetch_closed_orders)
        canceled_orders = await loop.run_in_executor(None, g_bot_data.exchange.fetch_canceled_orders)
        ledger = await loop.run_in_executor(None, g_bot_data.exchange.fetch_ledger)

        # usdc positions and orders
        perp_contracts = set()
        for x in closed_orders:
            if x['info']['symbol'].endswith('PERP'):
                perp_contracts.add(x['info']['symbol'])
        perp_contracts = list(perp_contracts)
        try:
            positions.extend(await fetch_positions(perp_contracts))
        except Exception as e:
            log(f'[ERROR] {e}')
            traceback.print_exc()
        try:
            open_orders.extend(await fetch_open_orders(perp_contracts))
        except Exception as e:
            log(f'[ERROR] {e}')
            traceback.print_exc()

        trading_info = {
            'open_orders': open_orders,
            'closed_orders': closed_orders,
            'canceled_orders': canceled_orders,
            'positions': positions,
            'ledger': ledger
        }
    except Exception as e:
        log(f'[ERROR] {e}')
        traceback.print_exc()
    try:
        update_trading_info_gui(trading_info)
    except Exception as e:
        log(f'[ERROR] {e}')
        traceback.print_exc()
    notification.spinner = False
    notification.dismiss()


def update_trading_info_gui(trading_info):
    if Elements.TRADING_SPACE not in g_bot_data.gui:
        return

    def exchange_format(contract):
        contract = ''.join(x for x in contract if x.isalnum())
        if 'PERP' in contract:
            return f"https://www.bybit.com/trade/futures/usdc/{contract}"
        return f"https://www.bybit.com/trade/usdt/{contract}"

    trading_bot_space = g_bot_data.gui[Elements.TRADING_SPACE]
    with trading_bot_space:

        async def update_trading_info_callback():
            if Elements.UPDATE_TRADING_INFO_TIMER in g_bot_data.gui:
                timer = g_bot_data.gui.pop(Elements.UPDATE_TRADING_INFO_TIMER)
                timer.cancel()
                timer.delete()
            await update_trading_info()

        if Elements.UPDATE_TRADING_INFO_BUTTON not in g_bot_data.gui:
            g_bot_data.gui[Elements.UPDATE_TRADING_INFO_BUTTON] = ui.button('Update', on_click=lambda
                *_: update_trading_info_callback()).classes('m-auto')

        if Elements.UPDATE_TRADING_INFO_TIMER not in g_bot_data.gui:
            g_bot_data.gui[Elements.UPDATE_TRADING_INFO_TIMER] = ui.timer(10.0,
                                                                          callback=lambda: update_trading_info_callback(),
                                                                          once=True)

        if Elements.POSITIONS_BOX not in g_bot_data.gui:
            g_bot_data.gui[Elements.POSITIONS_BOX] = positions_box = ui.column().classes('justify-center items-center')
        positions_box = g_bot_data.gui[Elements.POSITIONS_BOX]

        if Elements.OPEN_ORDERS_BOX not in g_bot_data.gui:
            g_bot_data.gui[Elements.OPEN_ORDERS_BOX] = open_orders_box = ui.column().classes(
                'justify-center items-center')
        open_orders_box = g_bot_data.gui[Elements.OPEN_ORDERS_BOX]

        if Elements.CLOSED_ORDERS_BOX not in g_bot_data.gui:
            g_bot_data.gui[Elements.CLOSED_ORDERS_BOX] = closed_orders_box = ui.column().classes(
                'justify-center items-center')
        closed_orders_box = g_bot_data.gui[Elements.CLOSED_ORDERS_BOX]

        if Elements.CANCELED_ORDERS_BOX not in g_bot_data.gui:
            g_bot_data.gui[Elements.CANCELED_ORDERS_BOX] = canceled_orders_box = ui.column().classes(
                'justify-center items-center')
        canceled_orders_box = g_bot_data.gui[Elements.CANCELED_ORDERS_BOX]

        if Elements.LEDGER_BOX not in g_bot_data.gui:
            g_bot_data.gui[Elements.LEDGER_BOX] = ledger_box = ui.column().classes(
                'justify-center items-center')
        ledger_box = g_bot_data.gui[Elements.LEDGER_BOX]

        stop_types = ['Close', 'Settle', 'Stop', 'Take', 'Liq', 'TakeOver', 'Adl']

        positions_columns = [
            {'name': 'key', 'label': 'Key', 'field': 'key', 'align': 'center', 'sortable': True,
             'classes': 'hidden', 'headerClasses': 'hidden'},
            {'name': 'exchange_link', 'label': 'Exchange Link', 'field': 'exchange_link', 'align': 'center',
             'classes': 'hidden', 'headerClasses': 'hidden'},
            {'name': 'datetime', 'label': 'DateTime', 'field': 'datetime', 'align': 'center', 'sortable': True},
            {'name': 'contract', 'label': 'Contract', 'field': 'contract', 'align': 'center', 'sortable': True},
            {'name': 'real_size', 'label': 'Size', 'field': 'real_size', 'align': 'center', 'sortable': True,
             'classes': 'hidden', 'headerClasses': 'hidden'},
            {'name': 'size', 'label': 'Size', 'field': 'size', 'align': 'center', 'sortable': True,
             ':sort': '(a, b, rowA, rowB) => rowA.real_size - rowB.real_size'},
            {'name': 'side', 'label': 'Side', 'field': 'side', 'align': 'center', 'sortable': True},
            {'name': 'leverage', 'label': 'Leverage (L)', 'field': 'leverage', 'align': 'center', 'sortable': True},
            {'name': 'status', 'label': 'Status', 'field': 'status', 'align': 'center', 'sortable': True},
            {'name': 'pnl', 'label': 'P&L', 'field': 'pnl', 'align': 'center', 'sortable': True},
            {'name': 'unrealized_pnl', 'label': 'Unrealized', 'field': 'unrealized_pnl', 'align': 'center',
             'sortable': True},
            {'name': 'realized_pnl', 'label': 'Realized', 'field': 'realized_pnl', 'align': 'center', 'sortable': True},
            {'name': 'entry_price', 'label': 'Entry price', 'field': 'entry_price', 'align': 'center',
             'sortable': True},
            {'name': 'mark_price', 'label': 'Mark price', 'field': 'mark_price', 'align': 'center', 'sortable': True},
            {'name': 'liquidation_price', 'label': 'Liquidation price', 'field': 'liquidation_price', 'align': 'center',
             'sortable': True},
            {'name': 'tp_sl', 'label': 'TP/SL', 'field': 'tp_sl', 'align': 'center', 'sortable': False},
            {'name': 'trailing_stop', 'label': 'Trailing stop', 'field': 'trailing_stop', 'align': 'center',
             'sortable': False},
        ]
        positions_rows = []
        positions_data = trading_info['positions']
        positions_markers = dict()
        for position in positions_data:
            datetime_string = format_time(local_dt_from_timestamp(int(position['info']['createdTime'])))
            contract = position['info']['symbol']
            contracts = Decimal(position['info']['size'] or 0)
            if not contracts:
                continue
            value = Decimal(position['info']['positionValue'] or 0)
            size = f"{contracts}/{round(value, 4)}"
            side = 'Long' if position['info']['side'] == 'buy' else 'Short'
            leverage = Decimal(position['info']['leverage'] or 1)
            status = position['info']['positionStatus']
            unrealized_pnl = Decimal(position['info']['unrealisedPnl'] or 0)
            realized_pnl = Decimal(position['info']['cumRealisedPnl'] or 0)
            entry_price = Decimal(position['info']['avgPrice'])
            mark_price = Decimal(position['info']['markPrice'])
            pnl = unrealized_pnl - mark_price * contracts * g_bot_data.fee + realized_pnl
            liquidation_price = Decimal(position['info']['liqPrice'] or 0)
            take_profit_price = Decimal(position['info']['takeProfit'] or 0)
            stop_loss_price = Decimal(position['info']['stopLoss'] or 0)
            tp_sl = f'{take_profit_price or "-"}/{stop_loss_price or "-"}'
            trailing_stop = Decimal(position['info']['trailingStop']) or '-'
            positions_markers[(contract, side)] = {
                'contracts': contracts,
                'value': value,
                'leverage': leverage,
                'entry_price': entry_price,
                'mark_price': mark_price
            }
            positions_rows.append({
                'exchange_link': exchange_format(contract),
                'key': f"{datetime_string} {size} {side} {leverage}",
                'datetime': datetime_string,
                'contract': contract,
                'size': size,
                'side': side,
                'leverage': round(leverage, 1),
                'status': status,
                'pnl': round(pnl, 4),
                'unrealized_pnl': round(unrealized_pnl, 4),
                'realized_pnl': round(realized_pnl, 4),
                'entry_price': entry_price,
                'mark_price': mark_price,
                'liquidation_price': liquidation_price,
                'tp_sl': tp_sl,
                'trailing_stop': trailing_stop,
            })
        with positions_box:
            positions_rows.sort(key=lambda x: x['key'], reverse=True)
            if Elements.POSITIONS_TABLE not in g_bot_data.gui:
                ui.label('Positions')
                g_bot_data.gui[Elements.POSITIONS_TABLE] = table = ui.table(columns=positions_columns,
                                                                            rows=positions_rows,
                                                                            row_key='key',
                                                                            pagination=5).style("width: 1250px;")
                table.add_slot('body-cell-contract', '''
                     <q-td :props="props">
                         <a :href="props.row.exchange_link" target="_blank">{{ props.row.contract }}</a>
                     </q-td>
                ''')
            else:
                table = g_bot_data.gui[Elements.POSITIONS_TABLE]
                table.update_rows(positions_rows)

        open_orders_columns = [
            {'name': 'key', 'label': 'Key', 'field': 'key', 'align': 'center', 'sortable': True,
             'classes': 'hidden', 'headerClasses': 'hidden'},
            {'name': 'exchange_link', 'label': 'Exchange Link', 'field': 'exchange_link', 'align': 'center',
             'classes': 'hidden', 'headerClasses': 'hidden'},
            {'name': 'datetime', 'label': 'DateTime', 'field': 'datetime', 'align': 'center', 'sortable': True},
            {'name': 'contract', 'label': 'Contract', 'field': 'contract', 'align': 'center', 'sortable': True},
            {'name': 'real_size', 'label': 'Size', 'field': 'real_size', 'align': 'center', 'sortable': True,
             'classes': 'hidden', 'headerClasses': 'hidden'},
            {'name': 'size', 'label': 'Size', 'field': 'size', 'align': 'center', 'sortable': True,
             ':sort': '(a, b, rowA, rowB) => rowA.real_size - rowB.real_size'},
            {'name': 'side', 'label': 'Side', 'field': 'side', 'align': 'center', 'sortable': True},
            {'name': 'order', 'label': 'Order', 'field': 'order', 'align': 'center', 'sortable': True},
            {'name': 'status', 'label': 'Status', 'field': 'status', 'align': 'center', 'sortable': True},
            {'name': 'real_price', 'label': 'Price', 'field': 'real_price', 'align': 'center', 'sortable': True,
             'classes': 'hidden', 'headerClasses': 'hidden'},
            {'name': 'price', 'label': 'Price', 'field': 'price', 'align': 'center', 'sortable': True,
             ':sort': '(a, b, rowA, rowB) => rowA.real_price - rowB.real_price'},
            {'name': 'tp_sl', 'label': 'TP&SL', 'field': 'tp_sl', 'align': 'center', 'sortable': False},
            {'name': 'reduce_only', 'label': 'Reduce only', 'field': 'reduce_only', 'align': 'center',
             'sortable': False},
            {'name': 'time_in_force', 'label': 'Time in force', 'field': 'time_in_force', 'align': 'center',
             'sortable': False},
        ]
        open_orders_rows = []
        open_orders_data = trading_info['open_orders']
        for open_order in open_orders_data:
            symbol = get_symbol(open_order['symbol'])
            if not symbol:
                continue
            datetime_string = format_time(local_dt_from_timestamp(int(open_order['info']['updatedTime'])))
            contract = open_order['info']['symbol']
            contracts = Decimal(open_order['info']['leavesQty'] or 0)
            if not contracts:
                continue
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
            if stop_order_type or any(x in create_type for x in stop_types):
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
            size = f"{contracts}/{real_size:.2f}"
            tp_sl = ''
            if trigger_price:
                p = (price / entry_price - 1) * contracts / position_contracts * (-1 if side == 'Short' else 1)
                real_value = value / leverage
                real_base_value = p * real_value - mark_price * contracts * g_bot_data.fee
                tmp = real_base_value / real_value * 100
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
            open_orders_rows.append({
                'exchange_link': exchange_format(contract),
                'key': f"{datetime_string} {contract} {size} {side} {order_type}",
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
        with open_orders_box:
            open_orders_rows.sort(key=lambda x: x['key'], reverse=True)
            if Elements.OPEN_ORDERS_TABLE not in g_bot_data.gui:
                ui.label('Open orders')
                g_bot_data.gui[Elements.OPEN_ORDERS_TABLE] = table = ui.table(columns=open_orders_columns,
                                                                              rows=open_orders_rows, row_key='key',
                                                                              pagination=5).style("width: 1250px;")
                table.add_slot('body-cell-contract', '''
                             <q-td :props="props">
                                 <a :href="props.row.exchange_link" target="_blank">{{ props.row.contract }}</a>
                             </q-td>
                        ''')
            else:
                table = g_bot_data.gui[Elements.OPEN_ORDERS_TABLE]
                table.update_rows(open_orders_rows)

        closed_orders_columns = [
            {'name': 'key', 'label': 'Key', 'field': 'key', 'align': 'center', 'sortable': True,
             'classes': 'hidden', 'headerClasses': 'hidden'},
            {'name': 'exchange_link', 'label': 'Exchange Link', 'field': 'exchange_link', 'align': 'center',
             'classes': 'hidden', 'headerClasses': 'hidden'},
            {'name': 'datetime', 'label': 'DateTime', 'field': 'datetime', 'align': 'center', 'sortable': True},
            {'name': 'contract', 'label': 'Contract', 'field': 'contract', 'align': 'center', 'sortable': True},
            {'name': 'size', 'label': 'Size', 'field': 'size', 'align': 'center', 'sortable': False},
            {'name': 'side', 'label': 'Side', 'field': 'side', 'align': 'center', 'sortable': True},
            {'name': 'order', 'label': 'Order', 'field': 'order', 'align': 'center', 'sortable': True},
            {'name': 'status', 'label': 'Status', 'field': 'status', 'align': 'center', 'sortable': True},
            {'name': 'real_price', 'label': 'Price', 'field': 'real_price', 'align': 'center', 'sortable': True,
             'classes': 'hidden', 'headerClasses': 'hidden'},
            {'name': 'price', 'label': 'Price', 'field': 'price', 'align': 'center', 'sortable': True,
             ':sort': '(a, b, rowA, rowB) => rowA.real_price - rowB.real_price'},
            {'name': 'tp_sl', 'label': 'TP&SL', 'field': 'tp_sl', 'align': 'center',
             'sortable': False},
            {'name': 'commission', 'label': 'Commission', 'field': 'commission', 'align': 'center',
             'sortable': False},
            {'name': 'reduce_only', 'label': 'Reduce only', 'field': 'reduce_only', 'align': 'center',
             'sortable': False},
            {'name': 'time_in_force', 'label': 'Time in force', 'field': 'time_in_force', 'align': 'center',
             'sortable': False},
        ]
        closed_orders_rows = []
        closed_orders_data = trading_info['closed_orders']
        for closed_order in closed_orders_data:
            symbol = get_symbol(closed_order['symbol'])
            if not symbol:
                continue
            created_time = int(closed_order['info']['createdTime'])
            datetime_string = format_time(local_dt_from_timestamp(int(closed_order['info']['updatedTime'])))
            contract = closed_order['info']['symbol']
            contracts = Decimal(closed_order['info']['qty'] or 0)
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
            if stop_order_type or any(x in create_type for x in stop_types):
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
            closed_orders_rows.append({
                'exchange_link': exchange_format(contract),
                'key': f"{datetime_string} {contract} {size} {side} {order_type}",
                'datetime': datetime_string,
                'contract': contract,
                'real_size': real_size,
                'size': size,
                'side': side,
                'order': order_type,
                'status': status,
                'real_price': real_price,
                'price': price,
                'commission': commission,
                'tp_sl': "",
                'reduce_only': reduce_only,
                'time_in_force': time_in_force,
                'contracts': contracts,
                'created_time': created_time,
                'is_stop_type': is_stop_type,
                'symbol': symbol
            })
        try:
            closed_orders_rows.sort(key=lambda x: x['created_time'])
            d = dict()
            for closed_order in closed_orders_rows:
                contract = (closed_order['contract'], closed_order['side'])
                price = closed_order['real_price']
                side = closed_order['side']
                contracts = closed_order['contracts']
                commission = closed_order['commission']
                real_size = closed_order['real_size']
                base_currency = closed_order['symbol'][1]
                if closed_order['is_stop_type']:
                    old_price, old_contracts = d.get(contract, [0, 0])
                    new_contracts = old_contracts - contracts
                    if new_contracts > 0:
                        d[contract] = [old_price, new_contracts]
                    elif contract in d:
                        d.pop(contract)
                    p = old_price / price
                    real_base_value = real_size * (1 - p) * (-1 if side == 'Short' else 1) - commission
                    tmp = real_base_value * 100 / real_size
                    closed_order['tp_sl'] = f"{round(tmp, 2)}% ({round(real_base_value, 2)} {base_currency})"
                else:
                    old_price, old_contracts = d.get(contract, [0, 0])
                    new_price = (old_price * old_contracts + price * contracts) / (old_contracts + contracts)
                    new_contracts = old_contracts + contracts
                    d[contract] = [new_price, new_contracts]
                    tmp = commission / real_size * 100
                    closed_order['tp_sl'] = f"{-round(tmp, 4)}% ({-round(commission, 4)} {base_currency})"
        except Exception as e:
            log(f'[ERROR] {e}')
            traceback.print_exc()

        with closed_orders_box:
            closed_orders_rows.sort(key=lambda x: x['key'], reverse=True)
            if Elements.CLOSED_ORDERS_TABLE not in g_bot_data.gui:
                ui.label('Closed orders')
                g_bot_data.gui[Elements.CLOSED_ORDERS_TABLE] = table = ui.table(columns=closed_orders_columns,
                                                                                rows=closed_orders_rows, row_key='key',
                                                                                pagination=5).style("width: 1250px;")
                table.add_slot('body-cell-contract', '''
                                     <q-td :props="props">
                                         <a :href="props.row.exchange_link" target="_blank">{{ props.row.contract }}</a>
                                     </q-td>
                                ''')
            else:
                table = g_bot_data.gui[Elements.CLOSED_ORDERS_TABLE]
                table.update_rows(closed_orders_rows)


        #todo
        canceled_orders_columns = [
            {'name': 'key', 'label': 'Key', 'field': 'key', 'align': 'center', 'sortable': True,
             'classes': 'hidden', 'headerClasses': 'hidden'},
            {'name': 'exchange_link', 'label': 'Exchange Link', 'field': 'exchange_link', 'align': 'center',
             'classes': 'hidden', 'headerClasses': 'hidden'},
            {'name': 'datetime', 'label': 'DateTime', 'field': 'datetime', 'align': 'center', 'sortable': True},
            {'name': 'contract', 'label': 'Contract', 'field': 'contract', 'align': 'center', 'sortable': True},
            {'name': 'size', 'label': 'Size', 'field': 'size', 'align': 'center', 'sortable': False},
            {'name': 'side', 'label': 'Side', 'field': 'side', 'align': 'center', 'sortable': True},
            {'name': 'order', 'label': 'Order', 'field': 'order', 'align': 'center', 'sortable': True},
            {'name': 'reason', 'label': 'Reason', 'field': 'reason', 'align': 'center', 'sortable': True},
            {'name': 'real_price', 'label': 'Price', 'field': 'real_price', 'align': 'center', 'sortable': True,
             'classes': 'hidden', 'headerClasses': 'hidden'},
            {'name': 'price', 'label': 'Price', 'field': 'price', 'align': 'center', 'sortable': True,
             ':sort': '(a, b, rowA, rowB) => rowA.real_price - rowB.real_price'},
            {'name': 'reduce_only', 'label': 'Reduce only', 'field': 'reduce_only', 'align': 'center',
             'sortable': False},
            {'name': 'time_in_force', 'label': 'Time in force', 'field': 'time_in_force', 'align': 'center',
             'sortable': False},
        ]
        canceled_orders_rows = []
        canceled_orders_data = trading_info['canceled_orders']
        for canceled_order in canceled_orders_data:
            symbol = get_symbol(canceled_order['symbol'])
            if not symbol:
                continue
            datetime_string = format_time(local_dt_from_timestamp(int(canceled_order['info']['updatedTime'])))
            contract = canceled_order['info']['symbol']
            contracts = Decimal(canceled_order['info']['qty'] or 0)
            reason = canceled_order['info']['orderStatus']
            cancel_type = canceled_order['info']['cancelType'].replace('CancelBy', '')
            if reason == 'Cancelled':
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
            if stop_order_type or any(x in create_type for x in stop_types):
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
            canceled_orders_rows.append({
                'exchange_link': exchange_format(contract),
                'key': f"{datetime_string} {contract} {size} {side} {order_type}",
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
        with canceled_orders_box:
            canceled_orders_rows.sort(key=lambda x: x['key'], reverse=True)
            if Elements.CANCELED_ORDERS_TABLE not in g_bot_data.gui:
                ui.label('Canceled orders')
                g_bot_data.gui[Elements.CANCELED_ORDERS_TABLE] = table = ui.table(columns=canceled_orders_columns,
                                                                                  rows=canceled_orders_rows, row_key='key',
                                                                                  pagination=5).style("width: 1250px;")
                table.add_slot('body-cell-contract', '''
                                             <q-td :props="props">
                                                 <a :href="props.row.exchange_link" target="_blank">{{ props.row.contract }}</a>
                                             </q-td>
                                        ''')
            else:
                table = g_bot_data.gui[Elements.CANCELED_ORDERS_TABLE]
                table.update_rows(canceled_orders_rows)

        ledger_columns = [
            {'name': 'key', 'label': 'Key', 'field': 'key', 'align': 'center', 'sortable': True,
             'classes': 'hidden', 'headerClasses': 'hidden'},
            {'name': 'exchange_link', 'label': 'Exchange Link', 'field': 'exchange_link', 'align': 'center',
             'classes': 'hidden', 'headerClasses': 'hidden'},
            {'name': 'datetime', 'label': 'DateTime', 'field': 'datetime', 'align': 'center', 'sortable': True},
            {'name': 'contract', 'label': 'Contract', 'field': 'contract', 'align': 'center', 'sortable': True},
            {'name': 'type', 'label': 'Type', 'field': 'type', 'align': 'center', 'sortable': True},
            {'name': 'side', 'label': 'Side', 'field': 'side', 'align': 'center', 'sortable': True},
            {'name': 'quantity', 'label': 'Quantity', 'field': 'quantity', 'align': 'center', 'sortable': True},
            {'name': 'filled_price', 'label': 'Filled price', 'field': 'filled_price', 'align': 'center', 'sortable': True},
            {'name': 'funding', 'label': 'Funding', 'field': 'funding', 'align': 'center', 'sortable': True},
            {'name': 'fee_paid', 'label': 'Fee paid', 'field': 'fee_paid', 'align': 'center', 'sortable': True},
            {'name': 'cash_flow', 'label': 'Cash flow', 'field': 'cash_flow', 'align': 'center', 'sortable': True},
            {'name': 'change', 'label': 'Change', 'field': 'change', 'align': 'center', 'sortable': True},
            {'name': 'cash_balance', 'label': 'Cash balance', 'field': 'cash_balance', 'align': 'center', 'sortable': True},
        ]
        ledger_rows = []
        ledger_data = trading_info['ledger']
        for ledger in ledger_data:
            datetime_string = format_time(local_dt_from_timestamp(int(ledger['info']['transactionTime'])))
            contract = ledger['info']['symbol']
            transaction_type = ledger['info']['type']
            side = ledger['info']['side']
            quantity = Decimal(ledger['info']['qty'] or 0)
            filled_price = Decimal(ledger['info']['tradePrice'] or 0)
            funding = Decimal(ledger['info']['funding'] or 0)
            fee_paid = 0 if funding else Decimal(ledger['info']['feeRate'] or 0)
            cash_flow = Decimal(ledger['info']['cashFlow'] or 0)
            change = Decimal(ledger['info']['change'] or 0)
            cash_balance = Decimal(ledger['info']['cashBalance'] or 0)
            ledger_rows.append({
                'exchange_link': exchange_format(contract),
                'key': f"{datetime_string} {contract} {transaction_type} {side} {quantity} {filled_price}",
                'datetime': datetime_string,
                'contract': contract,
                'type': transaction_type,
                'side': side,
                'quantity': quantity,
                'filled_price': filled_price,
                'funding': round(funding, 5),
                'fee_paid': round(fee_paid, 5),
                'cash_flow': cash_flow,
                'change': round(change, 5),
                'cash_balance': round(cash_balance, 5)
            })
        with ledger_box:
            ledger_rows.sort(key=lambda x: x['key'], reverse=True)
            if Elements.LEDGER_TABLE not in g_bot_data.gui:
                ui.label('Transactions')
                g_bot_data.gui[Elements.LEDGER_TABLE] = table = ui.table(columns=ledger_columns,
                                                                         rows=ledger_rows,
                                                                         row_key='key',
                                                                         pagination=5).style("width: 1250px;")
                table.add_slot('body-cell-contract', '''
                                     <q-td :props="props">
                                         <a :href="props.row.exchange_link" target="_blank">{{ props.row.contract }}</a>
                                     </q-td>
                                ''')
            else:
                table = g_bot_data.gui[Elements.LEDGER_TABLE]
                table.update_rows(ledger_rows)

        # pprint.pprint(trading_info)


async def init():
    notification = ui.notification(timeout=8, close_button=True)
    notification.message = 'Connecting...'
    notification.spinner = True

    g_bot_data.fee = Decimal('0.001')
    g_bot_data.config4exchange['apiKey'] = g_bot_data.gui[Elements.API_KEY_INPUT].value or g_bot_data.config4exchange[
        'apiKey']
    g_bot_data.config4exchange['secret'] = g_bot_data.gui[Elements.API_SECRET_INPUT].value or \
                                           g_bot_data.config4exchange['secret']
    testnet = g_bot_data.gui[Elements.TESTNET_CHECKBOX].value or False

    try:
        g_bot_data.exchange = ccxt.bybit(g_bot_data.config4exchange)
        if testnet:
            g_bot_data.exchange.enable_demo_trading(True)
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, g_bot_data.exchange.fetch_balance)
    except Exception as e:
        log(f'[ERROR] {e}')
        traceback.print_exc()
        notification.message = f'{e}'
        notification.spinner = False
        notification.type = 'negative'
        await asyncio.sleep(5)
        notification.dismiss()
        return

    remove_from_gui(Elements.LOGIN_SPACE)
    notification.message = 'The connection is established!'
    notification.spinner = False
    notification.type = 'info'

    main_space = g_bot_data.gui[Elements.MAIN_SPACE]
    with main_space:
        with ui.tabs().classes('w-full') as tabs:
            balance_tab = ui.tab('Balance')
            markets_tab = ui.tab('Markets')
            trading_tab = ui.tab('Trading Info')
            trading_bots_tab = ui.tab('Trading Bots')
            log_tab = ui.tab('Log')
        with ui.tab_panels(tabs, value=balance_tab).classes('items-center'):
            with ui.tab_panel(balance_tab):
                g_bot_data.gui[Elements.BALANCE_SPACE] = ui.card().classes('items-center')
            with ui.tab_panel(markets_tab):
                g_bot_data.gui[Elements.MARKETS_SPACE] = ui.card().classes('items-center')
            with ui.tab_panel(trading_tab):
                g_bot_data.gui[Elements.TRADING_SPACE] = ui.card().classes('items-center')
            with ui.tab_panel(trading_bots_tab):
                g_bot_data.gui[Elements.TRADING_BOTS_SPACE] = ui.card().classes('items-center')
            with ui.tab_panel(log_tab):
                g_bot_data.gui[Elements.LOG_SPACE] = ui.log(max_lines=1000).classes('h-96').style("width: 800px;")

    log('The connection is established!')
    await update_balance()
    notification.dismiss()
    await update_trading_info()
    await setup_trading_bots()
    await update_markets()


def init_login_window():
    if Elements.MAIN_SPACE not in g_bot_data.gui:
        g_bot_data.gui[Elements.MAIN_SPACE] = main_space = ui.column().classes('w-full items-center')
    else:
        main_space = g_bot_data.gui[Elements.MAIN_SPACE]

    main_space.clear()

    with main_space:
        g_bot_data.gui[Elements.LOGIN_SPACE] = login_space = ui.card().classes('items-center')
    ui.colors(primary='#777')
    with login_space:
        ui.label('Trading Bots Platform v1 [Bybit]')
        with ui.grid(columns='auto auto').classes('justify-center items-center'):
            ui.label('API Key:')
            g_bot_data.gui[Elements.API_KEY_INPUT] = t = ui.input(value=g_bot_data.config4exchange['apiKey'],
                                                                  validation={'18 <= API KEY LENGTH <= 256': lambda
                                                                      value: 18 <= len(value) <= 256})
            ui.label('API Secret:')
            g_bot_data.gui[Elements.API_SECRET_INPUT] = ui.input(value=g_bot_data.config4exchange['secret'],
                                                                 validation={'36 <= API KEY LENGTH <= 256': lambda
                                                                     value: 36 <= len(value) <= 256})
        g_bot_data.gui[Elements.TESTNET_CHECKBOX] = ui.checkbox('Testnet', value=True)
        g_bot_data.gui[Elements.INIT_BUTTON] = ui.button('Connect', on_click=init)


def quit_action():
    try:
        for x in list(g_bot_data.gui):
            if x == Elements.MAIN_SPACE:
                continue
            g_bot_data.gui.pop(x)
        g_bot_data.gui[Elements.MAIN_SPACE].clear()
    except Exception as e:
        log(f'[ERROR] {e}')
        traceback.print_exc()
    init_login_window()


def main():
    ui.add_head_html('''
        <style type="text/tailwindcss">
            body {
                font-size: 100%;
            }
            .nicegui-link, a {
                color: #fff;
            }
            .q-table th, .q-table td {
                font-size: 100%;
            }
        </style>
    ''')
    init_login_window()
    ui.run(title='Trading Bot v1', dark=True, language='en-US', reload=False, endpoint_documentation='none',
           show_welcome_message=False)


if __name__ in {"__main__", "__mp_main__"}:
    print("Starting...")
    main()
