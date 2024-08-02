from threading import RLock
import traceback

from bots_platform.model.utils import TimeStamp, decimal_number
from bots_platform.model.workers import Worker
import ccxt


class MarginModes:
    ISOLATED = 'isolated'
    CROSS = 'cross'
    PORTFOLIO = 'portfolio'

    @staticmethod
    def get_margin_modes():
        return [MarginModes.ISOLATED, MarginModes.CROSS, MarginModes.PORTFOLIO]


class BalanceWorker(Worker):
    def __init__(self):
        super().__init__()
        self._balance_lock: RLock = RLock()
        self._balance_cache: dict = dict()
        self._balance_cache_ts: float = 0.
        self._margin_mode: str = ''
        self._unified_account: bool = True

    def get_margin_mode(self) -> str:
        return self._margin_mode

    def get_unified_account(self) -> bool:
        return self._unified_account

    async def upgrade_unified_trade_account(self):
        self.check()
        try:
            with self._balance_lock:
                self._connection.upgrade_unified_trade_account()
            self._logger.log(f'Unified trade account is upgraded, wait a minute!')
        except BaseException as e:
            traceback.print_exc()
            self._logger.log(*e.args)
            raise

    async def switch_margin_mode(self, *, new_margin_mode=None) -> str:
        self.check()
        try:
            if new_margin_mode is None:
                if self._margin_mode == MarginModes.ISOLATED:
                    new_margin_mode = MarginModes.CROSS
                elif self._margin_mode == MarginModes.CROSS:
                    new_margin_mode = MarginModes.ISOLATED
                elif self._margin_mode == MarginModes.PORTFOLIO:
                    new_margin_mode = MarginModes.CROSS
            with self._balance_lock:
                self._connection.set_margin_mode(new_margin_mode)
            self._logger.log(f'Margin mode switched to \"{new_margin_mode}\"!')
        except BaseException as e:
            traceback.print_exc()
            self._logger.log(*e.args)
            raise
        return new_margin_mode

    async def force_update_balance_info(self, *, only_reset=False):
        self.check()
        balance_dict = dict()
        try:
            if only_reset:
                with self._balance_lock:
                    self._balance_cache_ts = 0
                return
            balance = await self._async_run(self._connection.fetch_balance)
            balance: dict = dict(balance)
            if balance['info']['retMsg'] != 'OK':
                raise Exception('Fetching balance error')
            if balance['info']['result']['list'][0]['totalMarginBalance'] == '':
                self._margin_mode = MarginModes.ISOLATED
            else:
                self._margin_mode = MarginModes.CROSS
            _, unified_account = await self._async_run(self._connection.is_unified_enabled)
            self._unified_account = unified_account
            balance_dict['margin_mode'] = self._margin_mode
            balance_dict['unified_account'] = self._unified_account
            balance_dict['coins'] = list()
            for account_balance_list in balance['info']['result']['list']:
                if account_balance_list['accountType'] != 'UNIFIED':
                    continue
                for account_balance in account_balance_list['coin']:
                    coin_name = account_balance['coin']
                    wallet_balance = decimal_number(account_balance['walletBalance'] or 0)
                    total_order_im = decimal_number(account_balance['totalOrderIM'] or 0)
                    total_position_im = decimal_number(account_balance['totalPositionIM'] or 0)
                    locked = total_order_im + total_position_im
                    free = decimal_number(account_balance['availableToWithdraw'])
                    if wallet_balance == free:
                        free = wallet_balance - locked
                    total_pnl = decimal_number(account_balance['cumRealisedPnl'] or 0)
                    total_pnl = f"{round(total_pnl, 3):+}"
                    pnl = decimal_number(account_balance['unrealisedPnl'] or 0)
                    usd_value = decimal_number(account_balance['usdValue'] or 0)
                    if round(usd_value, 3) == 0:
                        continue
                    used_coin = f'{round(locked, 6)}{round(pnl, 3):+}' if pnl else f'{round(locked, 6)}'
                    free_coin = f'{round(free, 6)}'
                    total_coin = f'{round(locked + free + pnl, 6)}'
                    locked *= usd_value / (wallet_balance or 1)
                    pnl *= usd_value / (wallet_balance or 1)
                    free *= usd_value / (wallet_balance or 1)
                    used_usd = f'{round(locked, 6)}{round(pnl, 3):+}' if pnl else f'{round(locked, 6)}'
                    free_usd = f'{round(free, 6)}'
                    total_usd = f'{round(locked + free + pnl, 6)}'
                    used_usd_hidden = round(locked + pnl, 6)
                    free_usd_hidden = round(free, 6)
                    total_usd_hidden = round(locked + free + pnl, 6)
                    used_string = f'{used_coin} {coin_name} / ${used_usd}'
                    free_string = f'{free_coin} {coin_name} / ${free_usd}'
                    total_string = f'{total_coin} {coin_name} / ${total_usd}'
                    if not any(x in used_string for x in '123456789'):
                        used_string = '–'
                    if not any(x in free_string for x in '123456789'):
                        free_string = '–'
                    if not any(x in total_string for x in '123456789'):
                        total_string = '–'
                    if any(x in '123456789' for x in used_usd + free_usd):
                        balance_dict['coins'].append({
                            'coin': coin_name,
                            'used_str': used_string,
                            'free_str': free_string,
                            'total_str': total_string,
                            'total_pnl': total_pnl,
                            'used_usd': used_usd_hidden,
                            'free_usd': free_usd_hidden,
                            'total_usd': total_usd_hidden,
                        })
            now_timestamp = TimeStamp.get_local_dt_from_now().timestamp()
            with self._balance_lock:
                self._balance_cache = balance_dict
                self._balance_cache_ts = now_timestamp
        except ccxt.NetworkError as e:
            traceback.print_exc()
            self._logger.log(*e.args)
            await self._connection_aborted_callback()
            return
        except BaseException as e:
            traceback.print_exc()
            self._logger.log(*e.args)
            raise

    async def fetch_balance_info(self, *, force=False, number_of_seconds_to_update=5) -> dict:
        with self._balance_lock:
            if not force and self._balance_cache:
                now_timestamp = TimeStamp.get_local_dt_from_now().timestamp()
                n_seconds = number_of_seconds_to_update
                if now_timestamp < self._balance_cache_ts + n_seconds:
                    return self._balance_cache
            try:
                await self.force_update_balance_info()
            except:
                pass
            return self._balance_cache
