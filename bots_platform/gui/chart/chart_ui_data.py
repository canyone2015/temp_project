from typing import Literal, Union
from decimal import Decimal


class ChartUiData:
    BLUE_COLOR = '#68b8ee'
    CYAN_COLOR = '#68eee1'
    GREEN_COLOR = '#b8ee68'
    ORANGE_COLOR = '#ee9e68'
    PINK_COLOR = '#e168ee'
    PURPLE_COLOR = '#9e68ee'
    RED_COLOR = '#ee6875'
    YELLOW_COLOR = '#eee168'
    LIGHT_COLOR = '#f0f0f3'
    DARK_COLOR = '#2b2b35'
    BLACK_COLOR = '#000000'
    GRAY_COLOR = '#ababab'
    WHITE_COLOR = '#ffffff'

    STOCK_CHART = {
        'parameters': {
            'contract': '',
            'date_from': '',
            'date_to': '',
            'timeframe': '',
            'price_type': '',
            'real_date_from': '',
        },
        'rangeSelector': {
            'buttons': [
                {
                    'type': 'minute',
                    'count': 30,
                    'text': '30m'
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
        'xAxis': {
            'plotLines': [],
            'dataGrouping': {
                'units': [
                    ['minute', [1, 3, 5, 15, 30]],
                    ['hour', [1, 2, 4, 6, 12]],
                    ['day', [1]],
                    ['week', [1]],
                    ['month', [1]],
                    ['year', [1]],
                ],
            },
        },
        'yAxis': [
            {
                'height': '80%',
                'plotLines': [],
                'crosshair': {
                    'snap': False,
                    'label': {
                        'enabled': True
                    }
                },
            },
            {
                'top': '80%',
                'height': '20%',
                'offset': 0,
                'plotLines': [],
                'crosshair': {
                    'snap': False,
                    'label': {
                        'enabled': True
                    }
                },
            }
        ],
        'series': [
            {
                'id': 'ohlc',
                'type': 'candlestick',
                'name': 'OHLC',
                'data': [],
                'yAxis': 0,
                'groupPadding': 0.18,
                'pointPadding': 0.1,
            },
            {
                'id': 'volume',
                'type': 'column',
                'name': 'Volume',
                'data': [],
                'yAxis': 1,
                'groupPadding': 0.18,
                'pointPadding': 0.1,
            },
        ],
        'plotOptions': {
            'candlestick': {
                'color': '#F23645',
                'lineColor': '#F23645',
                'upColor': '#089981',
                'upLineColor': '#089981',
            },
            'ohlc': {
                'color': '#F23645',
                'lineColor': '#F23645',
                'upColor': '#089981',
                'upLineColor': '#089981',
                'lineWidth': '3',
            },
        }
    }

    @staticmethod
    def make_marker(*,
                    target: Union[Literal['ohlc', 'volume'], int],
                    marker_id: str,
                    marker_name: str,
                    data: list,
                    marker_type: str = 'line',
                    color='#68b8ee',
                    radius=1):
        return {
            'id': marker_id,
            'type': marker_type,
            'name': marker_name,
            'data': data,
            'yAxis': target if isinstance(target, int) else (0 if target == 'ohlc' else 1),
            'marker': {
                'enabled': radius > 0,
                'radius': max(radius, 0),
                'fillColor': color
            }
        }

    @staticmethod
    def make_line(*,
                  value: Union[int, float, Decimal],
                  label_text: str,
                  label_color: str = '#F0F0F3',
                  label_align: str = 'left',
                  line_color: str = '#F0F0F3',
                  line_width: int = 1):
        return {
            'value': value,
            'color': line_color,
            'width': line_width,
            'label': {
                'text': label_text,
                'style': {
                    'color': label_color,
                    'fontWeight': 'bold',
                },
                'align': label_align,
            },
        }
