from nicegui import ui
from typing import Union

from bots_platform.gui.spaces import LoginSpace, UserSpace
from bots_platform.model import ExchangeModel


class PlatformGui:
    BALANCE_SPACE = 'BALANCE_SPACE'
    MARKETS_SPACE = 'MARKETS_SPACE'
    TRADING_SPACE = 'TRADING_SPACE'
    TRADING_BOTS_SPACE = 'TRADING_BOTS_SPACE'
    LOG_SPACE = 'LOG_SPACE'

    def __init__(self, title):
        self._exchange_model: Union[ExchangeModel, None] = None
        self._main_space = ui.column().classes('w-full items-center')
        self._login_space: Union[LoginSpace, None] = LoginSpace(title)
        self._user_space: Union[UserSpace, None] = UserSpace()

    def init(self):
        ui.timer(0.0,
                 callback=lambda: self.enter_login_space(),
                 once=True)

    async def enter_login_space(self):
        self.check_model()
        with self._main_space:
            self._login_space.set_exchange_model(self._exchange_model)
            self._login_space.set_enter_user_space(self.enter_user_space)
            await self._login_space.init()

    async def enter_user_space(self):
        self.check_model()
        with self._main_space:
            self._user_space.set_exchange_model(self._exchange_model)
            self._user_space.set_logout_space(self.enter_login_space)
            await self._user_space.init()

    def check_model(self):
        if self._exchange_model is None:
            raise Exception('Model is invalid')

    def set_exchange_model(self, model: ExchangeModel):
        self._exchange_model = model
