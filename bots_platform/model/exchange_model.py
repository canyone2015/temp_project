from typing import Union
from threading import RLock
import ccxt
import asyncio
import traceback

from bots_platform.model.utils import TimeStamp
from bots_platform.model.logger import Logger
from bots_platform.model.workers import (BalanceWorker, ChartsWorker, MarketsWorker,
                                         TradingWorker, TradingBotsWorker)


class ExchangeModel:
    def __init__(self):
        self._logger = Logger()
        self._exchange = None
        self._config = None
        self._api_key = None
        self._api_secret = None
        self._is_testnet = None
        self._connection: Union[ccxt.bybit, None] = None
        self._balance_worker = None
        self._markets_worker = None
        self._trading_worker = None
        self._charts_worker = None
        self._trading_bots_worker = None
        self.__lock = RLock()
        self.__reconnected_timestamp = 0

    async def connect(self,
                      exchange: str,
                      api_key: str,
                      api_secret: str,
                      is_testnet: bool,
                      **config_parameters):
        with self.__lock:
            try:
                self._exchange = exchange
                self._api_key = api_key
                self._api_secret = api_secret
                self._is_testnet = is_testnet
                self._config = {
                    'apiKey': self._api_key,
                    'secret': self._api_secret,
                }
                self._config.update(config_parameters)
                connection = self._new_connection()
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, connection.fetch_balance)
                self._connection = connection
                self._init_workers()
            except BaseException as e:
                self._exchange = None
                self._connection = None
                traceback.print_exc()
                self._logger.log(*e.args)
                raise
            self._logger.log('Connected!')

    async def reconnect(self):
        with self.__lock:
            timestamp = TimeStamp.get_local_dt_from_now().timestamp()
            if timestamp - self.__reconnected_timestamp < 5:  # 5 seconds
                self._logger.log('Reconnect is skipped!')
                return
            self.__reconnected_timestamp = timestamp
            self._connection = self._new_connection()
            self._update_workers_connection()
            self._logger.log('Reconnected!')

    def disconnect(self):
        with self.__lock:
            self._exchange = None
            self._config = dict()
            self._api_key = ''
            self._api_secret = ''
            self._is_testnet = False
            self._detach_workers()
            self._logger.log('Disconnected!')

    def check(self):
        with self.__lock:
            if self._connection is None or self._exchange is None:
                raise Exception('There is no connection.')

    def get_balance_worker(self):
        return self._balance_worker

    def get_markets_worker(self):
        return self._markets_worker

    def get_trading_worker(self):
        return self._trading_worker

    def get_charts_worker(self):
        return self._charts_worker

    def get_trading_bots_worker(self):
        return self._trading_bots_worker

    def get_logger(self):
        return self._logger

    def _new_connection(self):
        connection = getattr(ccxt, self._exchange)(self._config)
        if self._is_testnet:
            connection.enable_demo_trading(True)
        return connection

    def _init_workers(self):
        self._balance_worker = BalanceWorker()
        self._markets_worker = MarketsWorker()
        self._trading_worker = TradingWorker()
        self._charts_worker = ChartsWorker()
        self._trading_bots_worker = TradingBotsWorker()
        self._update_workers_connection()
        self._balance_worker.set_logger(self._logger)
        self._markets_worker.set_logger(self._logger)
        self._trading_worker.set_logger(self._logger)
        self._charts_worker.set_logger(self._logger)
        self._trading_bots_worker.set_logger(self._logger)
        self._balance_worker.set_connection_aborted_callback(self.reconnect)
        self._markets_worker.set_connection_aborted_callback(self.reconnect)
        self._trading_worker.set_connection_aborted_callback(self.reconnect)
        self._charts_worker.set_connection_aborted_callback(self.reconnect)
        self._trading_bots_worker.set_connection_aborted_callback(self.reconnect)
        self._charts_worker.set_trading_worker(self._trading_worker)
        self._charts_worker.set_markets_worker(self._markets_worker)

    def _update_workers_connection(self):
        with self.__lock:
            self._balance_worker.set_connection(self._connection)
            self._markets_worker.set_connection(self._connection)
            self._trading_worker.set_connection(self._connection)
            self._charts_worker.set_connection(self._connection)
            self._trading_bots_worker.set_connection(self._connection)

    def _detach_workers(self):
        self._balance_worker.detach()
        self._markets_worker.detach()
        self._trading_worker.detach()
        self._charts_worker.detach()
        self._trading_bots_worker.detach()
        self._balance_worker = None
        self._markets_worker = None
        self._trading_worker = None
        self._charts_worker = None
        self._trading_bots_worker = None
