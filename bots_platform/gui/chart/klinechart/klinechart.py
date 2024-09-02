from typing import Dict, Union
from nicegui import ui


"""
OPTIONS
{
    'data': [
        {
            'timestamp': 0,
            'open': 0,
            'high': 0,
            'low': 0,
            'close': 0,
            'volume': 0,
        },
    ],
    'price_precision': 6,
    'volume_precision': 6,
    'baseTheme': 'light'|'dark',
    'styles': {  # https://klinecharts.com/en-US/guide/styles
        'yAxis': {
            'position': 'left'|'right',
            'type': 'normal'|'percentage'|'log',
            'inside': true|false,
            'inverse': true|false,
            # ...
        },
        'candle': {
            'type': 'candle_solid'|'candle_stroke'|'candle_up_stroke'|'candle_down_stroke'|'ohlc'|'area',
            'tooltip': {
                'showRule': 'always'|'follow_cross'|'none',
                'showType': 'standard'|'rect',
            },
            # ...
        },
    },
    'timezone': 'Europe/Istanbul',  # Intl.supportedValuesOf('timeZone')
    'locale': 'en',  # https://en.wikipedia.org/wiki/List_of_ISO_639_language_codes
}
"""

# todo: indicators
"""
    'indicators': [
        'averagePrice', 'awesomeOscillator', 'bias', 'bollingerBands',
        'brar', 'bullAndBearIndex', 'commodityChannelIndex', 'currentRatio',
        'differentOfMovingAverage', 'directionalMovementIndex', 'easeOfMovementValue',
        'exponentialMovingAverage', 'momentum', 'movingAverage',
        'movingAverageConvergenceDivergence', 'onBalanceVolume',
        'priceAndVolumeTrend', 'psychologicalLine', 'rateOfChange',
        'relativeStrengthIndex', 'simpleMovingAverage', 'stoch',
        'stopAndReverse', 'tripleExponentiallySmoothedAverage',
        'volume', 'volumeRatio', 'williamsR'
    ],
"""


class KLineChart(ui.element,
                 component='klinechart.js',
                 libraries=['klinecharts.min.js'],
                 dependencies=['klinecharts.min.js']):
    DRAWINGS_GROUP = 'drawings'
    AUTO_DRAWINGS_GROUP = 'auto_drawings'

    def __init__(self, options: Dict) -> None:
        super().__init__()
        self._props['libraries'] = ['klinecharts.min.js']
        self._props['options'] = options

    @property
    def options(self) -> Dict:
        return self._props['options']

    def add_overlay(self, overlay: Union[str, dict], group_id: str = None):
        if isinstance(overlay, str):
            overlay = {'name': overlay, 'groupId': group_id or KLineChart.DRAWINGS_GROUP}
            self.run_method('add_overlay', overlay)
        elif isinstance(overlay, dict):
            overlay['groupId'] = group_id or overlay.get('groupId') or KLineChart.AUTO_DRAWINGS_GROUP
            if 'points' in overlay and self._props['options'].get('data'):
                points = overlay['points']
                last_timestamp = self._props['options']['data'][-1]['timestamp']
                for point in points:
                    if point.get('dataIndex') is None and\
                            (point.get('timestamp') is None or point['timestamp'] != point['timestamp']):
                        point['timestamp'] = last_timestamp
                    elif point.get('timestamp') is not None and point['timestamp'] > last_timestamp:
                        point['timestamp'] = last_timestamp
            self.run_method('add_overlay', overlay)

    def remove_overlay(self, group_id: str):
        self.run_method('remove_overlay', group_id)

    def update(self) -> None:
        super().update()
        self.run_method('update_chart')

    def duplicate(self):
        new_chart = KLineChart(self.options)
        return new_chart
