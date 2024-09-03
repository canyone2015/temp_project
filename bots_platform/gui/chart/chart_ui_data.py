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
        'baseTheme': 'dark',
        'price_precision': 6,
        'volume_precision': 6,
        'data': [],
        'styles': {
            'crosshair': {
                'show': True,
                'horizontal': {
                    'text': {
                        'size': 14,
                    }
                },
                'vertical': {
                    'text': {
                        'size': 14,
                    }
                },
            },
            'xAxis': {
                'tickText': {
                    'size': 14,
                }
            },
            'yAxis': {
                'position': 'right',
                'inside': False,
                'type': 'normal',
                'tickText': {
                    'size': 14,
                }
            },
            'priceMark': {
                'tickText': {
                    'size': 14,
                }
            },
            'candle': {
                'type': 'candle_solid',
                'tooltip': {
                    'showRule': 'follow_cross',
                    'custom': [
                        {'title': 'Time: ', 'value': '{time}'},
                        {'title': 'Open: ', 'value': '{open}'},
                        {'title': 'High: ', 'value': '{high}'},
                        {'title': 'Low: ', 'value': '{low}'},
                        {'title': 'Close: ', 'value': '{close}'},
                        {'title': 'Volume: ', 'value': '{volume}'}
                    ],
                    'text': {
                        'size': 16,
                        'color': '#D9D9D9'
                    }
                },
                'priceMark': {
                    'high': {
                        'textSize': 14,
                    },
                    'low': {
                        'textSize': 14,
                    },
                    'last': {
                        'text': {
                            'size': 14,
                        }
                    }
                }
            },
            'indicator': {
                'tooltip': {
                    'showRule': 'follow_cross',
                    'text': {
                        'size': 14,
                    }
                },
                'lastValueMark': {
                    'show': True,
                    'text': {
                        'size': 14,
                    }
                }
            },
            'overlay': {
                'text': {
                    'size': 14
                },
                'rectText': {
                    'size': 14
                }
            }
        },
        'timezone': 'Africa/Monrovia',  # UTC
        'locale': 'en',
    }

    @staticmethod
    def make_marker(*,
                    timestamp,
                    value,
                    label_text: str,
                    label_color: str = '#68b8ee',
                    label_background_color: str = '#121212'):
        return {
            'currentStep': -1,
            'points': [
                {
                    'timestamp': timestamp,
                    'value': value,
                },
            ],
            'styles': {
                'point': {
                    'radius': 0,
                },
                'line': {
                    'color': label_background_color,
                    'size': 2,
                },
                'text': {
                    'color': label_color,
                    'backgroundColor': label_background_color,
                },
            },
            'extendData': {'text': label_text},
            'name': 'marker',
            'lock': True,
            'visible': True,
            'paneId': 'candle_pane'
        }

    @staticmethod
    def make_line(*,
                  value: Union[int, float, Decimal],
                  label_text: str,
                  label_color: str = '#F0F0F3',
                  label_background_color: str = '#121212',
                  line_color: str = '#F0F0F3',
                  line_width: int = 1,
                  align: str = 'right'):
        return {
            'currentStep': -1,
            'points': [
                {
                    'value': value,
                },
            ],
            'styles': {
                'point': {
                    'radius': 0,
                },
                'line': {
                    'color': line_color,
                    'size': line_width,
                },
                'text': {
                    'color': label_color,
                    'backgroundColor': label_background_color,
                },
            },
            'extendData': {'text': label_text, 'align': align},
            'name': 'price_line',
            'lock': True,
            'visible': True,
            'paneId': 'candle_pane'
        }
