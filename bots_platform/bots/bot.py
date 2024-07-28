from copy import deepcopy
from typing import Union
import json


from bots_platform.model import ExchangeModel


class Bot:
    def __init__(self):
        self._model: Union[ExchangeModel, None] = None
        self._settings_template = [
            {
                'name': 'number of grids',
                'type': '',
                # checkbox|switch|number|input|textarea|toggle|select
                'validation': lambda x: x >= 10,
                'convert': lambda x: int(x),
                'values': 5,
                'values': [],

                # bool value (ui.checkbox; ui.switch);
                # number value (ui.number);
                # string value (ui.input);
                # multistring value (ui.textarea);
                # multiple values (ui.toggle, ui.select)
                'default_value': 5
            }
        ]
        self._settings = dict()
        self._orders = []
        self._positions = []
        self._filename = 'bot_settings.json'

    def get_settings_template(self):
        return deepcopy(self._settings_template)

    def save_settings(self):
        with open(self._filename, 'w+', encoding='utf-8') as fp:
            json.dump(self._settings, fp, sort_keys=True)

    def load_settings(self):
        with open(self._filename, 'r+', encoding='utf-8') as fp:
            self._settings = json.load(fp, sort_keys=True)

        self.settings_changed_signal()

    def get_settings(self):
        return deepcopy(self._settings)

    def set_settings(self, settings):
        self._settings = settings

    def settings_changed_signal(self):
        return

    def init(self, connection):
        self._connection = connection

    def open_long(self):
        pass

    def open_short(self):
        pass

    def close_long(self):
        pass

    def close_short(self):
        pass

    def short(self):
        pass

