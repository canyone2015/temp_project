from nicegui import ui
from typing import Union
import asyncio

from bots_platform.model import ExchangeModel


class DefaultApiParameters:
    API_KEY = '8MOZNveF4mxaOINkZE'
    API_SECRET = '9sT5mCZondAz0WijmQOBdDCVM9KqJBu4JLv7'
    IS_TESTNET = True


class LoginSpace:
    API_KEY_INPUT = 'API_KEY_INPUT'
    API_SECRET_INPUT = 'API_SECRET_INPUT'
    TESTNET_CHECKBOX = 'TESTNET_CHECKBOX'
    INIT_BUTTON = 'INIT_BUTTON'

    def __init__(self, title):
        self._exchange_model: Union[ExchangeModel, None] = None
        self._login_space = None
        self._elements = dict()
        self._enter_user_space = None
        self._title = title

    async def init(self):
        self._elements.clear()
        if self._login_space:
            self._login_space.delete()
        self._login_space = ui.card().classes('items-center')
        with self._login_space:
            ui.label(self._title)
            with ui.grid(columns='auto auto').classes('justify-center items-center'):
                ui.label('API Key:')
                validation = {'18 <= API KEY LENGTH <= 256': lambda value: 18 <= len(value) <= 256}
                self._elements[LoginSpace.API_KEY_INPUT] = ui.input(value=DefaultApiParameters.API_KEY,
                                                                    validation=validation)
                ui.label('API Secret:')
                validation = {'36 <= API SECRET LENGTH <= 256': lambda value: 36 <= len(value) <= 256}
                self._elements[LoginSpace.API_SECRET_INPUT] = ui.input(value=DefaultApiParameters.API_SECRET,
                                                                       validation=validation)
            self._elements[LoginSpace.TESTNET_CHECKBOX] = ui.checkbox('Testnet',
                                                                      value=DefaultApiParameters.IS_TESTNET)
            self._elements[LoginSpace.INIT_BUTTON] = ui.button('Connect', on_click=self.connect)

    def check(self):
        if self._login_space is None or self._exchange_model is None or self._enter_user_space is None:
            raise Exception(f'{type(self).__name__} is not initialized')

    def set_exchange_model(self, model: ExchangeModel):
        self._exchange_model = model

    def set_enter_user_space(self, enter_user_space: callable):
        self._enter_user_space = enter_user_space

    def detach(self):
        try:
            self._login_space.delete()
        except:
            pass
        self._elements.clear()
        self._login_space = None

    async def connect(self):
        self.check()
        notification = ui.notification(timeout=8, close_button=True)
        notification.message = 'Connecting...'
        notification.spinner = True

        api_key = self._elements[LoginSpace.API_KEY_INPUT].value
        api_secret = self._elements[LoginSpace.API_SECRET_INPUT].value
        is_testnet = self._elements[LoginSpace.TESTNET_CHECKBOX].value
        try:
            await self._exchange_model.connect(
                exchange='bybit',
                api_key=api_key,
                api_secret=api_secret,
                is_testnet=is_testnet,
            )
            DefaultApiParameters.API_KEY = api_key
            DefaultApiParameters.API_SECRET = api_secret
            DefaultApiParameters.IS_TESTNET = is_testnet
        except BaseException as e:
            notification.message = f'{e}'
            notification.spinner = False
            notification.type = 'negative'
            await asyncio.sleep(5)
            notification.dismiss()
            return

        notification.message = 'The connection is established!'
        notification.spinner = False
        notification.type = 'info'

        self.detach()

        await self._enter_user_space()
        notification.dismiss()
