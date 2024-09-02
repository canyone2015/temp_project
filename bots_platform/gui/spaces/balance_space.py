from nicegui import ui
from typing import Union
import asyncio

from bots_platform.model.workers import BalanceWorker
from bots_platform.gui.spaces import Columns


class BalanceSpace:
    UNIFIED_INFO_COL = 'UNIFIED_INFO_COL'
    TRADING_ACCOUNT_LINK = 'TRADING_ACCOUNT_LINK'
    BALANCE_TABLE = 'BALANCE_TABLE'
    MARGIN_MODE_ROW = 'MARGIN_MODE_ROW'
    UPDATE_BALANCE_TIMER = 'UPDATE_BALANCE_TIMER'
    UPDATE_QUIT_ROW = 'UPDATE_QUIT_ROW'

    def __init__(self):
        self._balance_worker: Union[BalanceWorker, None] = None
        self._balance_space = None
        self._elements = dict()
        self._constructed = False
        self._quit_action = None

    async def init(self):
        self._elements.clear()
        if self._balance_space:
            self._balance_space.delete()
        self._balance_space = ui.card().classes('items-center')
        await self.update()
        self._constructed = True

    async def upgrade_unified_trade_account(self):
        if not self._constructed:
            return
        try:
            notification = ui.notification(timeout=25, close_button=True)
            notification.message = 'Wait 30 seconds...'
            notification.spinner = True
            await self._balance_worker.upgrade_unified_trade_account()
            await asyncio.sleep(30)
            notification.message = 'Done!'
            notification.spinner = False
            notification.dismiss()
            await asyncio.sleep(3)
            await self.quit()
        except Exception as e:
            ui.notify(f'Upgrade unified trade account error: {e}', type='negative', close_button=True)

    async def switch_margin_mode(self):
        if not self._constructed:
            return
        try:
            new_margin_mode = await self._balance_worker.switch_margin_mode()
            ui.notify(f'Margin mode switched to \"{new_margin_mode}\"!',
                      type='positive', close_button=True)
        except Exception as e:
            ui.notify(f'Margin mode switched error: {e}',
                      type='negative', close_button=True)
        await self.update()

    async def update(self):
        self._delete_update_balance_timer()
        notification = ui.notification(timeout=8, close_button=True)
        notification.message = 'Fetching balance...'
        notification.spinner = True

        async def dialog_yes():
            nonlocal dialog
            dialog.close()
            if not self._constructed:
                return
            await self.quit()

        async def dialog_no():
            nonlocal dialog
            dialog.close()

        async def update_balance_triggered(force=False):
            if not self._constructed:
                return
            self._constructed = False
            try:
                self._delete_update_balance_timer()
                if force:
                    await self._balance_worker.force_update_balance_info(only_reset=True)
                await self.update()
            except:
                pass
            self._constructed = True

        with self._balance_space:
            balance: dict = dict()
            try:
                balance = await self._balance_worker.fetch_balance_info()
            except:
                pass
            margin_mode = 'isolated'
            unified_account = True
            coins = []
            if balance:
                margin_mode = balance['margin_mode']
                unified_account = balance['unified_account']
                coins = balance['coins']
            if not unified_account:
                if BalanceSpace.UNIFIED_INFO_COL not in self._elements:
                    self._elements[BalanceSpace.UNIFIED_INFO_COL] = ui.column().classes('w-full items-center')
                unified_info_col = self._elements[BalanceSpace.UNIFIED_INFO_COL]
                unified_info_col.clear()
                with unified_info_col:
                    ui.label('Not unified account!')
                    ui.button('Upgrade to unified account',
                              on_click=lambda *_: self.upgrade_unified_trade_account())
                    with ui.dialog() as dialog, ui.card().classes('items-center'):
                        ui.label('Are you sure you want to quit?')
                        with ui.row():
                            ui.button('Yes', on_click=dialog_yes)
                            ui.button('No', on_click=dialog_no)
                    ui.button('Quit', on_click=dialog.open).classes("m-auto")
                return
            elif BalanceSpace.UNIFIED_INFO_COL in self._elements:
                self._elements.pop(BalanceSpace.UNIFIED_INFO_COL).delete()

            if BalanceSpace.TRADING_ACCOUNT_LINK not in self._elements:
                trading_account_link = ui.link(f'Trading Account',
                                               'https://www.bybit.com/user/assets/home/tradingaccount',
                                               new_tab=True)
                self._elements[BalanceSpace.TRADING_ACCOUNT_LINK] = trading_account_link

            rows = []
            for coin in coins:
                rows.append({
                    'coin': coin['coin'],
                    'used': coin['used_str'],
                    'free': coin['free_str'],
                    'total': coin['total_str'],
                    'total_pnl': coin['total_pnl'],
                    'used_hidden': coin['used_usd'],
                    'free_hidden': coin['free_usd'],
                    'total_hidden': coin['total_usd'],
                })
            if BalanceSpace.BALANCE_TABLE in self._elements:
                self._elements[BalanceSpace.BALANCE_TABLE].update_rows(rows)
            else:
                balance_table = ui.table(columns=Columns.BALANCE_TABLE_COLUMNS,
                                         rows=rows,
                                         row_key='coin').classes('col-span-2 justify-center '
                                                                 'items-center justify-self-center')
                self._elements[BalanceSpace.BALANCE_TABLE] = balance_table

            if BalanceSpace.MARGIN_MODE_ROW not in self._elements:
                self._elements[BalanceSpace.MARGIN_MODE_ROW] = ui.row()
            margin_mode_row = self._elements[BalanceSpace.MARGIN_MODE_ROW]
            margin_mode_row.clear()
            with margin_mode_row:
                if 'cross' in margin_mode:
                    s = 'Cross Margin'
                elif 'isolated' in margin_mode:
                    s = 'Isolated Margin'
                elif 'portfolio' in margin_mode:
                    s = 'Portfolio Margin'
                else:
                    s = 'Unknown Margin'
                ui.label(s).classes("m-auto")
                ui.button('switch', on_click=lambda *_: self.switch_margin_mode()).classes("m-auto")

            if BalanceSpace.UPDATE_QUIT_ROW not in self._elements:
                self._elements[BalanceSpace.UPDATE_QUIT_ROW] = update_quit_row = ui.row()
                with update_quit_row:
                    ui.button('Update', on_click=lambda *_: update_balance_triggered(True)).classes("m-auto")
                    with ui.dialog() as dialog, ui.card().classes('items-center'):
                        ui.label('Are you sure you want to quit?')
                        with ui.row():
                            ui.button('Yes', on_click=dialog_yes)
                            ui.button('No', on_click=dialog_no)
                    ui.button('Quit', on_click=dialog.open).classes("m-auto")

            self._elements[BalanceSpace.UPDATE_BALANCE_TIMER] = ui.timer(5.0,  # 5 seconds
                                                                         callback=lambda *_: update_balance_triggered(),
                                                                         once=True)
        notification.spinner = False
        notification.dismiss()

    def check(self):
        if self._balance_space is None or self._balance_worker is None or self._quit_action is None:
            raise Exception(f'{type(self).__name__} is not initialized')

    def set_balance_worker(self, balance_worker: BalanceWorker):
        self._balance_worker = balance_worker

    def set_quit_action(self, quit_action: callable):
        self._quit_action = quit_action

    def detach(self):
        try:
            self._delete_update_balance_timer()
            self._balance_space.delete()
        except:
            pass
        self._constructed = False
        self._elements.clear()
        self._balance_space = None

    async def quit(self):
        if self._quit_action:
            await self._quit_action()

    def _delete_update_balance_timer(self):
        if BalanceSpace.UPDATE_BALANCE_TIMER in self._elements:
            try:
                update_balance_timer = self._elements.pop(BalanceSpace.UPDATE_BALANCE_TIMER)
                update_balance_timer.cancel()
            except:
                pass
