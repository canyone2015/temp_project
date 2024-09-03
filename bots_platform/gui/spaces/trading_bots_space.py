from nicegui import ui
from typing import Union

from bots_platform.gui.utils import Notification
from bots_platform.model.workers import TradingBotsWorker


class TradingBotsSpace:
    def __init__(self):
        self._trading_bots_worker: Union[TradingBotsWorker, None] = None
        self._trading_bots_space = None
        self._elements = dict()
        self._constructed = False
        self._trading_bots = {
            'Bot-1': {

            },
            'Bot-2': {

            }
        }
        notification = ui.notification(timeout=None, close_button=False)
        notification.message = 'Fetching trading bots...'
        notification.spinner = True
        self.__notification = Notification(notification)

    async def init(self):
        self._elements.clear()
        if self._trading_bots_space:
            self._trading_bots_space.delete()
        self._trading_bots_space = ui.card().classes('items-center')
        await self.update()
        self._constructed = True

    async def update(self):
        self.__notification.show()
        with self._trading_bots_space:
            tabs = []
            with ui.tabs().classes('w-full') as tabs_gui:
                for x in self._trading_bots:
                    tabs.append((x, ui.tab(x)))
            if tabs:
                with ui.tab_panels(tabs_gui, value=tabs[0][1]).classes('items-center'):
                    for tab_name, tab_element in tabs:
                        with ui.tab_panel(tab_element):
                            card = ui.card().classes('items-center')
        self.__notification.hide()

    def check(self):
        if self._trading_bots_space is None or self._trading_bots_worker is None:
            raise Exception(f'{type(self).__name__} is not initialized')

    def set_trading_bots_worker(self, trading_bots_worker: TradingBotsWorker):
        self._trading_bots_worker = trading_bots_worker

    def detach(self):
        try:
            self._trading_bots_space.delete()
        except:
            pass
        self._constructed = False
        self._elements.clear()
        self._trading_bots_space = None
