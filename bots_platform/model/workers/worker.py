import asyncio
import inspect
from urllib.request import Request, urlopen
from typing import Union


import ccxt
from bots_platform.model.logger import Logger


class Worker:
    def __init__(self):
        self._connection: Union[ccxt.bybit, None] = None
        self._logger: Union[Logger, None] = None
        self._connection_aborted_callback: callable = None

    def detach(self):
        self._logger = None
        self.set_connection_aborted_callback(lambda: None)
        self._connection = None

    def check(self):
        if self._connection is None or self._logger is None or self._connection_aborted_callback is None:
            raise Exception(f'{self.__class__.__name__} There is no connection.')

    def set_connection(self, connection: ccxt.Exchange):
        self._connection = connection

    def set_logger(self, logger: Logger):
        self._logger = logger

    def set_connection_aborted_callback(self, func: callable):
        async def awaitable_func():
            return self._await_or_run(func)
        self._connection_aborted_callback = awaitable_func

    async def _async_run(self, func, *args):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, func, *args)

    async def _await_or_run(self, obj, *args, **kwargs):
        b1 = inspect.isawaitable(obj)
        b2 = callable(obj)
        if b1 and b2:
            await obj(*args, **kwargs)
        elif b1:
            await obj
        elif b2:
            obj(*args, **kwargs)

    async def _load_text(self, url: str, headers: dict) -> str:
        request_site = Request(url, headers=headers)
        data = await self._async_run(urlopen, request_site)
        return data.read().decode('utf-8')
