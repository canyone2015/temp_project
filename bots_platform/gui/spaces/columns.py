class Columns:
    BALANCE_TABLE_COLUMNS = [
        {'name': 'coin', 'label': 'Coin', 'field': 'coin', 'align': 'center', 'sortable': True},
        {'name': 'used', 'label': 'Used', 'field': 'used', 'align': 'center', 'sortable': True,
         ':sort': '(a, b, rowA, rowB) => rowA.used_hidden - rowB.used_hidden'},
        {'name': 'free', 'label': 'Free', 'field': 'free', 'align': 'center', 'sortable': True,
         ':sort': '(a, b, rowA, rowB) => rowA.free_hidden - rowB.free_hidden'},
        {'name': 'total', 'label': 'Total', 'field': 'total', 'align': 'center', 'sortable': True,
         ':sort': '(a, b, rowA, rowB) => rowA.total_hidden - rowB.total_hidden'},
        {'name': 'total_pnl', 'label': 'Total P&L', 'field': 'total_pnl', 'align': 'center'},
        {'name': 'used_hidden', 'label': 'Used Hidden', 'field': 'used_hidden', 'align': 'center',
         'classes': 'hidden', 'headerClasses': 'hidden'},
        {'name': 'free_hidden', 'label': 'Free Hidden', 'field': 'free_hidden', 'align': 'center',
         'classes': 'hidden', 'headerClasses': 'hidden'},
        {'name': 'total_hidden', 'label': 'Total Hidden', 'field': 'total_hidden', 'align': 'center',
         'classes': 'hidden', 'headerClasses': 'hidden'},
    ]
    MARKETS_STATISTICS_COLUMNS = [
        {'name': 'metric', 'label': 'Metric', 'field': 'metric', 'align': 'center', 'sortable': False},
        {'name': 'value', 'label': 'Value', 'field': 'value', 'align': 'center', 'sortable': False},
    ]
    MARKETS_TABLE_COLUMNS = [
        {'name': 'key', 'label': 'Key', 'field': 'key', 'align': 'center', 'sortable': True,
         'classes': 'hidden', 'headerClasses': 'hidden'},
        {'name': 'tv_link', 'label': 'TV Link', 'field': 'tv_link', 'align': 'center',
         'classes': 'hidden', 'headerClasses': 'hidden'},
        {'name': 'exchange_link', 'label': 'Exchange Link', 'field': 'exchange_link', 'align': 'center',
         'classes': 'hidden', 'headerClasses': 'hidden'},
        {'name': 'type', 'label': 'Type', 'field': 'type', 'align': 'center', 'sortable': True},
        {'name': 'symbol', 'label': 'Symbol', 'field': 'symbol', 'align': 'center', 'sortable': True},
        {'name': 'last_trend', 'label': 'Last Trend', 'field': 'last_trend', 'align': 'center', 'sortable': True},
        {'name': 'open_price_24h', 'label': 'Open 24h', 'field': 'open_price_24h', 'align': 'center',
         'sortable': True},
        {'name': 'high_price_24h', 'label': 'High 24h', 'field': 'high_price_24h', 'align': 'center',
         'sortable': True},
        {'name': 'low_price_24h', 'label': 'Low 24h', 'field': 'low_price_24h', 'align': 'center',
         'sortable': True},
        {'name': 'close_price_24h', 'label': 'Close 24h', 'field': 'close_price_24h', 'align': 'center',
         'sortable': True},
        {'name': 'open_close_percent', 'label': 'Open-Close %', 'field': 'open_close_percent', 'align': 'center',
         'sortable': True},
        {'name': 'low_high_percent', 'label': 'Low-High %', 'field': 'low_high_percent', 'align': 'center',
         'sortable': True},
        {'name': 'volume_24h', 'label': 'Volume 24h', 'field': 'volume_24h', 'align': 'center',
         'classes': 'hidden', 'headerClasses': 'hidden'},
        {'name': 'volume_24h_fstring', 'label': 'Volume 24h', 'field': 'volume_24h_fstring', 'align': 'center',
         'sortable': True, ':sort': '(a, b, rowA, rowB) => rowA.volume_24h - rowB.volume_24h'},
        {'name': 'launch_datetime', 'label': 'Launch', 'field': 'launch_datetime', 'align': 'center', 'sortable': True},
        {'name': 'max_leverage', 'label': 'Max Leverage', 'field': 'max_leverage', 'align': 'center',
         'classes': 'hidden', 'headerClasses': 'hidden'},
        {'name': 'leverage', 'label': 'Leverage', 'field': 'leverage', 'align': 'center', 'sortable': True,
         ':sort': '(a, b, rowA, rowB) => rowA.max_leverage - rowB.max_leverage'},
        {'name': 'min_notional', 'label': 'Minimum notional', 'field': 'min_notional', 'align': 'center',
         'classes': 'hidden', 'headerClasses': 'hidden'},
        {'name': 'min_size', 'label': 'Minimum', 'field': 'min_size', 'align': 'center', 'sortable': True,
         ':sort': '(a, b, rowA, rowB) => rowA.min_notional - rowB.min_notional'},
        {'name': 'maker_taker', 'label': 'Maker/Taker', 'field': 'maker_taker', 'align': 'center'},
    ]
    POSITION_COLUMNS = [
        {'name': 'key', 'label': 'Key', 'field': 'key', 'align': 'center', 'sortable': True,
         'classes': 'hidden', 'headerClasses': 'hidden'},
        {'name': 'exchange_link', 'label': 'Exchange Link', 'field': 'exchange_link', 'align': 'center',
         'classes': 'hidden', 'headerClasses': 'hidden'},
        {'name': 'datetime', 'label': 'DateTime', 'field': 'datetime', 'align': 'center', 'sortable': True},
        {'name': 'contract', 'label': 'Contract', 'field': 'contract', 'align': 'center', 'sortable': True},
        {'name': 'real_size', 'label': 'Size', 'field': 'real_size', 'align': 'center',
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
        {'name': 'tp_sl', 'label': 'TP/SL', 'field': 'tp_sl', 'align': 'center'},
        {'name': 'trailing_stop', 'label': 'Trailing stop', 'field': 'trailing_stop', 'align': 'center'},
    ]
    OPEN_ORDERS_COLUMNS = [
        {'name': 'key', 'label': 'Key', 'field': 'key', 'align': 'center', 'sortable': True,
         'classes': 'hidden', 'headerClasses': 'hidden'},
        {'name': 'exchange_link', 'label': 'Exchange Link', 'field': 'exchange_link', 'align': 'center',
         'classes': 'hidden', 'headerClasses': 'hidden'},
        {'name': 'datetime', 'label': 'DateTime', 'field': 'datetime', 'align': 'center', 'sortable': True},
        {'name': 'contract', 'label': 'Contract', 'field': 'contract', 'align': 'center', 'sortable': True},
        {'name': 'real_size', 'label': 'Size', 'field': 'real_size', 'align': 'center',
         'classes': 'hidden', 'headerClasses': 'hidden'},
        {'name': 'size', 'label': 'Size', 'field': 'size', 'align': 'center', 'sortable': True,
         ':sort': '(a, b, rowA, rowB) => rowA.real_size - rowB.real_size'},
        {'name': 'side', 'label': 'Side', 'field': 'side', 'align': 'center', 'sortable': True},
        {'name': 'order', 'label': 'Order', 'field': 'order', 'align': 'center', 'sortable': True},
        {'name': 'status', 'label': 'Status', 'field': 'status', 'align': 'center', 'sortable': True},
        {'name': 'real_price', 'label': 'Price', 'field': 'real_price', 'align': 'center',
         'classes': 'hidden', 'headerClasses': 'hidden'},
        {'name': 'price', 'label': 'Price', 'field': 'price', 'align': 'center', 'sortable': True,
         ':sort': '(a, b, rowA, rowB) => rowA.real_price - rowB.real_price'},
        {'name': 'tp_sl', 'label': 'TP&SL', 'field': 'tp_sl', 'align': 'center'},
        {'name': 'reduce_only', 'label': 'Reduce only', 'field': 'reduce_only', 'align': 'center'},
        {'name': 'time_in_force', 'label': 'Time in force', 'field': 'time_in_force', 'align': 'center'},
    ]
    CLOSED_ORDERS_COLUMNS = [
        {'name': 'key', 'label': 'Key', 'field': 'key', 'align': 'center', 'sortable': True,
         'classes': 'hidden', 'headerClasses': 'hidden'},
        {'name': 'exchange_link', 'label': 'Exchange Link', 'field': 'exchange_link', 'align': 'center',
         'classes': 'hidden', 'headerClasses': 'hidden'},
        {'name': 'datetime', 'label': 'DateTime', 'field': 'datetime', 'align': 'center', 'sortable': True},
        {'name': 'contract', 'label': 'Contract', 'field': 'contract', 'align': 'center', 'sortable': True},
        {'name': 'real_size', 'label': 'Size', 'field': 'real_size', 'align': 'center',
         'classes': 'hidden', 'headerClasses': 'hidden'},
        {'name': 'size', 'label': 'Size', 'field': 'size', 'align': 'center', 'sortable': True,
         ':sort': '(a, b, rowA, rowB) => rowA.real_size - rowB.real_size'},
        {'name': 'side', 'label': 'Side', 'field': 'side', 'align': 'center', 'sortable': True},
        {'name': 'order', 'label': 'Order', 'field': 'order', 'align': 'center', 'sortable': True},
        {'name': 'status', 'label': 'Status', 'field': 'status', 'align': 'center', 'sortable': True},
        {'name': 'real_price', 'label': 'Price', 'field': 'real_price', 'align': 'center',
         'classes': 'hidden', 'headerClasses': 'hidden'},
        {'name': 'price', 'label': 'Price', 'field': 'price', 'align': 'center', 'sortable': True,
         ':sort': '(a, b, rowA, rowB) => rowA.real_price - rowB.real_price'},
        {'name': 'tp_sl', 'label': 'TP&SL', 'field': 'tp_sl', 'align': 'center'},
        {'name': 'commission', 'label': 'Commission', 'field': 'commission', 'align': 'center', 'sortable': True},
        {'name': 'reduce_only', 'label': 'Reduce only', 'field': 'reduce_only', 'align': 'center'},
        {'name': 'time_in_force', 'label': 'Time in force', 'field': 'time_in_force', 'align': 'center'},
    ]
    CANCELED_ORDERS_COLUMNS = [
        {'name': 'key', 'label': 'Key', 'field': 'key', 'align': 'center', 'sortable': True,
         'classes': 'hidden', 'headerClasses': 'hidden'},
        {'name': 'exchange_link', 'label': 'Exchange Link', 'field': 'exchange_link', 'align': 'center',
         'classes': 'hidden', 'headerClasses': 'hidden'},
        {'name': 'datetime', 'label': 'DateTime', 'field': 'datetime', 'align': 'center', 'sortable': True},
        {'name': 'contract', 'label': 'Contract', 'field': 'contract', 'align': 'center', 'sortable': True},
        {'name': 'real_size', 'label': 'Size', 'field': 'real_size', 'align': 'center',
         'classes': 'hidden', 'headerClasses': 'hidden'},
        {'name': 'size', 'label': 'Size', 'field': 'size', 'align': 'center', 'sortable': True,
         ':sort': '(a, b, rowA, rowB) => rowA.real_size - rowB.real_size'},
        {'name': 'side', 'label': 'Side', 'field': 'side', 'align': 'center', 'sortable': True},
        {'name': 'order', 'label': 'Order', 'field': 'order', 'align': 'center', 'sortable': True},
        {'name': 'reason', 'label': 'Reason', 'field': 'reason', 'align': 'center', 'sortable': True},
        {'name': 'real_price', 'label': 'Price', 'field': 'real_price', 'align': 'center',
         'classes': 'hidden', 'headerClasses': 'hidden'},
        {'name': 'price', 'label': 'Price', 'field': 'price', 'align': 'center', 'sortable': True,
         ':sort': '(a, b, rowA, rowB) => rowA.real_price - rowB.real_price'},
        {'name': 'reduce_only', 'label': 'Reduce only', 'field': 'reduce_only', 'align': 'center'},
        {'name': 'time_in_force', 'label': 'Time in force', 'field': 'time_in_force', 'align': 'center'},
    ]
    LEDGER_COLUMNS = [
        {'name': 'key', 'label': 'Key', 'field': 'key', 'align': 'center', 'sortable': True,
         'classes': 'hidden', 'headerClasses': 'hidden'},
        {'name': 'exchange_link', 'label': 'Exchange Link', 'field': 'exchange_link', 'align': 'center',
         'classes': 'hidden', 'headerClasses': 'hidden'},
        {'name': 'datetime', 'label': 'DateTime', 'field': 'datetime', 'align': 'center', 'sortable': True},
        {'name': 'contract', 'label': 'Contract', 'field': 'contract', 'align': 'center', 'sortable': True},
        {'name': 'type', 'label': 'Type', 'field': 'type', 'align': 'center', 'sortable': True},
        {'name': 'side', 'label': 'Side', 'field': 'side', 'align': 'center', 'sortable': True},
        {'name': 'quantity', 'label': 'Quantity', 'field': 'quantity', 'align': 'center', 'sortable': True},
        {'name': 'filled_price', 'label': 'Filled price', 'field': 'filled_price', 'align': 'center',
         'sortable': True},
        {'name': 'funding', 'label': 'Funding', 'field': 'funding', 'align': 'center', 'sortable': True,
         ':format': 'value => (value > 0) ? ("+" + value) : value'},
        {'name': 'fee_paid', 'label': 'Fee paid', 'field': 'fee_paid', 'align': 'center', 'sortable': True},
        {'name': 'cash_flow', 'label': 'Cash flow', 'field': 'cash_flow', 'align': 'center', 'sortable': True,
         ':format': 'value => (value > 0) ? ("+" + value) : value'},
        {'name': 'change', 'label': 'Change', 'field': 'change', 'align': 'center', 'sortable': True,
         ':format': 'value => (value > 0) ? ("+" + value) : value'},
        {'name': 'cash_balance', 'label': 'Cash balance', 'field': 'cash_balance', 'align': 'center',
         'sortable': True},
    ]
    STOCK_CHART = {
        'parameters': {
            'symbol': '',
            'fetch_option': '',
            'timeframe': '',
        },
        'rangeSelector': {
            'buttons': [
                {
                    'type': 'minute',
                    'count': 30,
                    'text': '1m'
                },
                {
                    'type': 'hour',
                    'count': 1,
                    'text': '1h'
                },
                {
                    'type': 'hour',
                    'count': 4,
                    'text': '4h'
                },
                {
                    'type': 'hour',
                    'count': 12,
                    'text': '12h'
                },
                {
                    'type': 'day',
                    'count': 1,
                    'text': '1d'
                },
                {
                    'type': 'week',
                    'count': 1,
                    'text': '1w'
                },
                {
                    'type': 'month',
                    'count': 1,
                    'text': '1M'
                },
                {
                    'type': 'year',
                    'count': 1,
                    'text': '1y'
                },
                {
                    'type': 'all',
                    'text': 'All'
                }
            ]
        },
        'title': {
            'text': 'Price'
        },
        'yAxis': [
            {
                'height': '80%',
                'plotLines': []
            },
            {
                'top': '80%',
                'height': '20%',
                'offset': 0,
                'plotLines': []
            }
        ],
        'series': [
            {
                'id': 'price',
                'type': 'candlestick',
                'name': 'Price',
                'data': [],
                'dataGrouping': {
                    'approximation': 'ohlc',
                    'units': [
                        ['minute', [1, 3, 5, 15, 30]],
                        ['hour', [1, 2, 4, 8, 6, 12]],
                        ['day', [1]],
                        ['week', [1]],
                        ['month', [1]],
                        ['year', [1]],
                    ],
                    'forced': True,
                    'enabled': True,
                    'groupAll': True
                },
                'yAxis': 0,
            },
            {
                'id': 'volume',
                'type': 'column',
                'name': 'Volume',
                'data': [],
                'yAxis': 1,
            }
        ],
        'plotOptions': {
            'candlestick': {
                'color': '#F23645',
                'lineColor': '#F23645',
                'upColor': '#089981',
                'upLineColor': '#089981',
            }
        }
    }
    CURRENT_PRICE_INDICATOR = [
        {
            'color': '#F0F0F3',
            'width': 1,
            'label': {
                'style': {
                    'color': '#F0F0F3',
                    'fontWeight': 'bold',
                },
                'align': 'right',
                'x': -30,
            }
        }
    ]
