from nicegui import ui
from typing import Union

from bots_platform.gui.spaces import BalanceSpace, MarketsSpace, TradingSpace
from bots_platform.gui.spaces import TradingBotsSpace, ChartsSpace, LogSpace
from bots_platform.model import ExchangeModel


class UserSpace:
    BALANCE_SPACE = 'BALANCE_SPACE'
    MARKETS_SPACE = 'MARKETS_SPACE'
    TRADING_SPACE = 'TRADING_SPACE'
    TRADING_BOTS_SPACE = 'TRADING_BOTS_SPACE'
    CHARTS_SPACE = 'CHARTS_SPACE'
    LOG_SPACE = 'LOG_SPACE'
    BALANCE_TIMER = 'BALANCE_TIMER'
    MARKETS_TIMER = 'MARKETS_TIMER'
    TRADING_TIMER = 'TRADING_TIMER'
    TRADING_BOTS_TIMER = 'TRADING_BOTS_TIMER'
    CHARTS_TIMER = 'CHARTS_TIMER'
    LOG_TIMER = 'LOG_TIMER'

    def __init__(self):
        self._exchange_model: Union[ExchangeModel, None] = None
        self._user_space = None
        self._elements = dict()
        self._logout_space = None

    async def init(self):
        self._elements.clear()
        if self._user_space:
            self._user_space.delete()
        self._user_space = ui.column().classes('w-full items-center')
        with self._user_space:
            with ui.tabs().classes('w-full') as tabs:
                balance_tab = ui.tab('Balance')
                markets_tab = ui.tab('Markets')
                trading_tab = ui.tab('Trading Info')
                trading_bots_tab = ui.tab('Trading Bots')
                charts_tab = ui.tab('Charts')
                log_tab = ui.tab('Log')
            with ui.tab_panels(tabs, value=balance_tab).classes('items-center'):
                with ui.tab_panel(balance_tab):
                    try:
                        self._elements[UserSpace.BALANCE_SPACE] = balance_space = BalanceSpace()
                        balance_space.set_exchange_model(self._exchange_model)
                        balance_space.set_quit_action(self.quit)
                        self._elements[UserSpace.BALANCE_TIMER] = ui.timer(0.0,
                                                                           callback=lambda: balance_space.init(),
                                                                           once=True)
                    except:
                        pass
                with ui.tab_panel(markets_tab):
                    try:
                        self._elements[UserSpace.MARKETS_SPACE] = markets_space = MarketsSpace()
                        markets_space.set_exchange_model(self._exchange_model)
                        self._elements[UserSpace.MARKETS_TIMER] = ui.timer(0.0,
                                                                           callback=lambda: markets_space.init(),
                                                                           once=True)
                    except:
                        pass
                with ui.tab_panel(trading_tab):
                    try:
                        self._elements[UserSpace.TRADING_SPACE] = trading_space = TradingSpace()
                        trading_space.set_exchange_model(self._exchange_model)
                        self._elements[UserSpace.TRADING_TIMER] = ui.timer(0.0,
                                                                           callback=lambda: trading_space.init(),
                                                                           once=True)
                    except:
                        pass
                with ui.tab_panel(trading_bots_tab):
                    try:
                        self._elements[UserSpace.TRADING_BOTS_SPACE] = trading_bots_space = TradingBotsSpace()
                        trading_bots_space.set_exchange_model(self._exchange_model)
                        self._elements[UserSpace.TRADING_BOTS_TIMER] = ui.timer(0.0,
                                                                                callback=lambda: trading_bots_space.init(),
                                                                                once=True)
                    except:
                        pass
                with ui.tab_panel(charts_tab):
                    try:
                        self._elements[UserSpace.CHARTS_SPACE] = charts_space = ChartsSpace()
                        try:
                            trading_space.set_charts_space(charts_space)
                        except:
                            pass
                        charts_space.set_exchange_model(self._exchange_model)
                        self._elements[UserSpace.CHARTS_TIMER] = ui.timer(0.0,
                                                                          callback=lambda: charts_space.init(),
                                                                          once=True)
                    except:
                        pass
                with ui.tab_panel(log_tab):
                    try:
                        self._elements[UserSpace.LOG_SPACE] = log_space = LogSpace()
                        log_space.set_logger(self._exchange_model.logger)
                        self._elements[UserSpace.LOG_TIMER] = ui.timer(0.0,
                                                                       callback=lambda: log_space.init(),
                                                                       once=True)
                    except:
                        pass

    def check(self):
        if self._user_space is None or self._exchange_model is None or self._logout_space is None:
            raise Exception(f'{type(self).__name__} is not initialized')

    def set_exchange_model(self, model: ExchangeModel):
        self._exchange_model = model

    def set_logout_space(self, logout_space: callable):
        self._logout_space = logout_space

    async def quit(self):
        if UserSpace.BALANCE_TIMER not in self._elements or self._elements[UserSpace.BALANCE_TIMER].callback:
            return
        if UserSpace.MARKETS_TIMER not in self._elements or self._elements[UserSpace.MARKETS_TIMER].callback:
            return
        if UserSpace.TRADING_TIMER not in self._elements or self._elements[UserSpace.TRADING_TIMER].callback:
            return
        if UserSpace.TRADING_BOTS_TIMER not in self._elements or self._elements[UserSpace.TRADING_BOTS_TIMER].callback:
            return
        if UserSpace.CHARTS_TIMER not in self._elements or self._elements[UserSpace.CHARTS_TIMER].callback:
            return
        if UserSpace.LOG_TIMER not in self._elements or self._elements[UserSpace.LOG_TIMER].callback:
            return
        self._elements[UserSpace.BALANCE_SPACE].detach()
        self._elements[UserSpace.MARKETS_SPACE].detach()
        self._elements[UserSpace.TRADING_SPACE].detach()
        self._elements[UserSpace.TRADING_BOTS_SPACE].detach()
        self._elements[UserSpace.CHARTS_SPACE].detach()
        self._elements[UserSpace.LOG_SPACE].detach()
        self._exchange_model.disconnect()
        self._user_space.delete()
        self._user_space = None
        self._elements.clear()

        await self._logout_space()
