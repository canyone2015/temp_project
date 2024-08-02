from typing import Union, Dict, Literal
from threading import RLock
from decimal import Decimal
import traceback


from bots_platform.model.utils import decimal_number, TimeStamp, get_symbol, make_brownian_motion
from bots_platform.model.workers import Worker
import ccxt


class TradingWorker(Worker):
    POSITIONS = 'positions'
    OPEN_ORDERS = 'open_orders'
    CLOSED_ORDERS = 'closed_orders'
    CANCELED_ORDERS = 'canceled_orders'
    LEDGER = 'ledger'

    def __init__(self):
        super().__init__()
        self._blocks_contracts: Dict[str, Dict[str, float]] = dict()
        self._blocks_balance: Dict[str, Decimal] = dict()
        self._blocks_lock: RLock = RLock()
        self._pol_lock: RLock = RLock()
        self._pol_cache: dict = {
            TradingWorker.POSITIONS: [],
            TradingWorker.OPEN_ORDERS: [],
            TradingWorker.CLOSED_ORDERS: [],
            TradingWorker.CANCELED_ORDERS: [],
            TradingWorker.LEDGER: []
        }
        self._pol_cache_ts: float = 0.
        self._max_fee: Decimal = decimal_number('0.0018')
        self._positions_markers: dict = dict()
        self._closed_orders_data: list = list()
        self._stop_types = frozenset({'close', 'closing', 'settle', 'stop',
                                      'take', 'liq', 'takeover', 'adl'})
        self._price_types = {}
        self._price_types_init()

    def get_max_fee(self) -> Decimal:
        return self._max_fee

    def get_timeframes(self):
        return self._connection.timeframes

    def get_price_types(self):
        return list(self._price_types)

    def _price_types_init(self):
        def fetch_ohlcv(symbol, timeframe, since, limit):
            return self._connection.fetch_ohlcv(symbol, timeframe, since, limit)

        def fetch_mark_ohlcv(symbol, timeframe, since, limit):
            return self._connection.fetch_mark_ohlcv(symbol, timeframe, since, limit)

        def fetch_index_ohlcv(symbol, timeframe, since, limit):
            return self._connection.fetch_index_ohlcv(symbol, timeframe, since, limit)

        def fetch_premium_index_ohlcv(symbol, timeframe, since, limit):
            return self._connection.fetch_premium_index_ohlcv(symbol, timeframe, since, limit)

        self._price_types = {
            'OHLCV': fetch_ohlcv,
            'MARK': fetch_mark_ohlcv,
            'INDEX': fetch_index_ohlcv,
            'PREMIUM_INDEX': fetch_premium_index_ohlcv,
        }

    @staticmethod
    def _get_positions_markers(positions_data):
        positions_markers = dict()
        for position in positions_data:
            contracts = decimal_number(position['info']['size'] or 0)
            if not contracts:
                continue
            contract = position['info']['symbol']
            side = 'Long' if position['info']['side'] == 'buy' else 'Short'
            value = decimal_number(position['info']['positionValue'] or 0)
            leverage = decimal_number(position['info']['leverage'] or 1)
            entry_price = decimal_number(position['info']['avgPrice'])
            mark_price = decimal_number(position['info']['markPrice'])
            positions_markers[(contract, side)] = {
                'contracts': contracts,
                'value': value,
                'leverage': leverage,
                'entry_price': entry_price,
                'mark_price': mark_price
            }
        return positions_markers

    async def _fetch_positions(self, *, usdc=True, _save_markers=False, _load_closed_orders_data=False):
        positions = []
        positions_data = await self._async_run(self._connection.fetch_positions,
                                               None, {'type': 'swap'})
        try:
            if usdc:
                if _load_closed_orders_data:
                    closed_orders_data = self._closed_orders_data
                else:
                    swap_closed_orders = await self._async_run(self._connection.fetch_closed_orders,
                                                               None, None, None, {'type': 'swap'})
                    spot_closed_orders = await self._async_run(self._connection.fetch_closed_orders,
                                                               None, None, None, {'type': 'spot'})
                    closed_orders_data = swap_closed_orders + spot_closed_orders
                perp_contracts = set()
                for x in closed_orders_data:
                    if x['info']['symbol'].endswith('PERP'):
                        perp_contracts.add(x['info']['symbol'])
                perp_contracts = list(perp_contracts)
                for symbol in perp_contracts:
                    try:
                        ps = await self._async_run(self._connection.fetch_positions,
                                                   symbol, {'type': 'swap'})
                        positions_data.extend(ps)
                    except BaseException as e:
                        traceback.print_exc()
                        self._logger.log(*e.args)
        except BaseException as e:
            traceback.print_exc()
            self._logger.log(*e.args)
        if _save_markers:
            self._positions_markers = TradingWorker._get_positions_markers(positions_data)
        for position in positions_data:
            contracts = decimal_number(position['info']['size'] or 0)
            if not contracts:
                continue
            contract = position['symbol']
            symbol = get_symbol(contract)
            if not symbol:
                continue
            updated_timestamp = int(position['info']['updatedTime'])
            datetime_string = TimeStamp.format_datetime(
                TimeStamp.get_local_dt_from_timestamp(updated_timestamp))
            value = decimal_number(position['info']['positionValue'] or 0)
            real_size = round(value, 4)
            size = f"{contracts}/{real_size}"
            side = 'Long' if position['info']['side'] == 'buy' else 'Short'
            leverage = decimal_number(position['info']['leverage'] or 1)
            status = position['info']['positionStatus']
            unrealized_pnl = decimal_number(position['info']['unrealisedPnl'] or 0)
            realized_pnl = decimal_number(position['info']['curRealisedPnl'] or 0)
            entry_price = decimal_number(position['info']['avgPrice'])
            mark_price = decimal_number(position['info']['markPrice'])
            pnl = unrealized_pnl + realized_pnl - mark_price * contracts * self._max_fee
            liquidation_price = decimal_number(position['info']['liqPrice'] or 0)
            take_profit_price = decimal_number(position['info']['takeProfit'] or 0)
            stop_loss_price = decimal_number(position['info']['stopLoss'] or 0)
            tp_sl = f'{take_profit_price or "-"}/{stop_loss_price or "-"}'
            trailing_stop = decimal_number(position['info']['trailingStop']) or '-'
            leverage = round(leverage, 2)
            pnl = round(pnl, 4)
            unrealized_pnl = round(unrealized_pnl, 4)
            realized_pnl = round(realized_pnl, 4)
            positions.append({
                'timestamp': updated_timestamp,
                'datetime': datetime_string,
                'contract': contract,
                'real_size': real_size,
                'size': size,
                'side': side,
                'leverage': leverage,
                'status': status,
                'pnl': pnl,
                'unrealized_pnl': unrealized_pnl,
                'realized_pnl': realized_pnl,
                'entry_price': entry_price,
                'mark_price': mark_price,
                'liquidation_price': liquidation_price,
                'tp_sl': tp_sl,
                'trailing_stop': trailing_stop,
                'type': symbol[-1]
            })
        return positions

    async def _fetch_open_orders(self, *, usdc=True, _load_markers=False, _load_closed_orders_data=False):
        open_orders = []
        positions_data = []
        if not _load_markers:
            positions_data = await self._async_run(self._connection.fetch_positions,
                                                   None, {'type': 'swap'})
        swap_open_orders = await self._async_run(self._connection.fetch_open_orders,
                                                   None, None, None, {'type': 'swap'})
        spot_open_orders = await self._async_run(self._connection.fetch_open_orders,
                                                   None, None, None, {'type': 'spot'})
        open_orders_data = swap_open_orders + spot_open_orders
        try:
            if usdc:
                if _load_closed_orders_data:
                    closed_orders_data = self._closed_orders_data
                else:
                    swap_closed_orders = await self._async_run(self._connection.fetch_closed_orders,
                                                               None, None, None, {'type': 'swap'})
                    spot_closed_orders = await self._async_run(self._connection.fetch_closed_orders,
                                                               None, None, None, {'type': 'spot'})
                    closed_orders_data = swap_closed_orders + spot_closed_orders
                perp_contracts = set()
                for x in closed_orders_data:
                    if x['info']['symbol'].endswith('PERP'):
                        perp_contracts.add(x['info']['symbol'])
                perp_contracts = list(perp_contracts)
                for symbol in perp_contracts:
                    if not _load_markers:
                        try:
                            ps = await self._async_run(self._connection.fetch_positions,
                                                       symbol, {'type': 'swap'})
                            positions_data.extend(ps)
                        except BaseException as e:
                            traceback.print_exc()
                            self._logger.log(*e.args)
                    try:
                        swap_open_orders = await self._async_run(self._connection.fetch_open_orders,
                                                                 symbol, None, None, {'type': 'swap'})
                        spot_open_orders = await self._async_run(self._connection.fetch_open_orders,
                                                                 symbol, None, None, {'type': 'spot'})
                        open_orders_data.extend(swap_open_orders + spot_open_orders)
                    except BaseException as e:
                        traceback.print_exc()
                        self._logger.log(*e.args)
        except BaseException as e:
            traceback.print_exc()
            self._logger.log(*e.args)
        if _load_markers:
            positions_markers = self._positions_markers
        else:
            positions_markers = TradingWorker._get_positions_markers(positions_data)
        for open_order in open_orders_data:
            contracts = decimal_number(open_order['info']['leavesQty'] or 0)
            if not contracts:
                continue
            contract = open_order['symbol']
            symbol = get_symbol(contract)
            if not symbol:
                continue
            updated_timestamp = int(open_order['info']['updatedTime'])
            datetime_string = TimeStamp.format_datetime(
                TimeStamp.get_local_dt_from_timestamp(updated_timestamp))
            status = open_order['info']['orderStatus']
            take_profit_price = decimal_number(open_order['info']['takeProfit'] or 0)
            take_profit_limit_price = decimal_number(open_order['info']['tpLimitPrice'] or 0)
            take_profit_trigger = open_order['info']['tpTriggerBy'].replace('Price', '')
            stop_loss_price = decimal_number(open_order['info']['stopLoss'] or 0)
            stop_loss_limit_price = decimal_number(open_order['info']['slLimitPrice'] or 0)
            stop_loss_trigger = open_order['info']['slTriggerBy'].replace('Price', '')
            trigger_price = decimal_number(open_order['info']['triggerPrice'] or 0)
            price = decimal_number(trigger_price or open_order['info']['price'] or 0)
            trigger_by = open_order['info']['triggerBy'].replace('Price', '')
            create_type = open_order['info'].get('createType', '').replace('CreateBy', '')
            create_type = create_type.replace('Closing', 'Close')
            if create_type == 'User':
                create_type = 'Open'
            side = open_order['info']['side']
            stop_order_type = open_order['info']['stopOrderType']
            if not create_type and symbol[-1] == 'spot':
                create_type = 'Open' if side == 'Buy' else 'Close'
            elif stop_order_type or any(x in create_type.lower() for x in self._stop_types):
                side = 'Short' if side == 'Buy' else 'Long'
            else:
                side = 'Long' if side == 'Buy' else 'Short'
            order_price_type = open_order['info']['orderType']
            order_type = create_type + bool(order_price_type) * (' ' + order_price_type)
            mark_price = entry_price = decimal_number(open_order['info']['lastPriceOnCreated'] or price)
            reduce_only = open_order['info']['reduceOnly']
            time_in_force = open_order['info']['timeInForce']
            if time_in_force == 'GTC':
                time_in_force = 'Good-Till-Canceled'
            elif time_in_force == 'IOC':
                time_in_force = 'Immediate-Or-Cancel'
            elif time_in_force == 'FOK':
                time_in_force = 'Fill-Or-Kill'
            leverage = 1
            position_contracts = contracts
            value = contracts * mark_price
            if (contract, side) in positions_markers:
                marker = positions_markers[(contract, side)]
                leverage = marker['leverage']
                mark_price = marker['mark_price']
                entry_price = marker['entry_price']
                position_contracts = marker['contracts']
                value = marker['value']
            real_size = contracts * mark_price
            size = f"{contracts}/{round(real_size, 3)}"
            tp_sl = ''
            if trigger_price:
                p = (price / entry_price - 1) * contracts / position_contracts * (-1 if side == 'Short' else 1)
                real_base_value = p * value - mark_price * contracts * self._max_fee
                tmp = real_base_value / value * 100
                base_currency = symbol[1].lower()
                tp_sl = f"{round(tmp, 2):+}% ({round(real_base_value, 2):+} {base_currency})"
            elif any([take_profit_limit_price, take_profit_price, stop_loss_limit_price, stop_loss_price]):
                if take_profit_limit_price:
                    tmp = (take_profit_limit_price / price - 1) * 100 * (-1 if side == 'Short' else 1)
                    tp_sl = f"{round(tmp, 2):+}% * L ({take_profit_trigger})"
                elif take_profit_price:
                    tmp = (take_profit_price / price - 1) * 100 * (-1 if side == 'Short' else 1)
                    tp_sl = f"{round(tmp, 2):+}% * L ({take_profit_trigger})"
                else:
                    tp_sl = "-"
                if stop_loss_limit_price:
                    tmp = (stop_loss_limit_price / price - 1) * 100 * (-1 if side == 'Short' else 1)
                    tp_sl += f" / {round(tmp, 2):+}% * L ({stop_loss_trigger})"
                elif stop_loss_price:
                    tmp = (stop_loss_price / price - 1) * 100 * (-1 if side == 'Short' else 1)
                    tp_sl += f" / {round(tmp, 2):+}% * L ({stop_loss_trigger})"
                else:
                    tp_sl += " / -"
            real_price = price
            price = f"{price} ({trigger_by if trigger_by else 'Last'})"
            open_orders.append({
                'timestamp': updated_timestamp,
                'datetime': datetime_string,
                'contract': contract,
                'real_size': real_size,
                'size': size,
                'side': side,
                'order': order_type,
                'status': status,
                'real_price': real_price,
                'price': price,
                'tp_sl': tp_sl,
                'reduce_only': reduce_only,
                'time_in_force': time_in_force,
                'type': symbol[-1]
            })
        return open_orders

    async def _fetch_closed_orders(self, *, _save_closed_orders_data=False):
        closed_orders = []
        swap_closed_orders = await self._async_run(self._connection.fetch_closed_orders,
                                                   None, None, None, {'type': 'swap'})
        spot_closed_orders = await self._async_run(self._connection.fetch_closed_orders,
                                                   None, None, None, {'type': 'spot'})
        closed_orders_data = swap_closed_orders + spot_closed_orders
        if _save_closed_orders_data:
            self._closed_orders_data = closed_orders_data
        for closed_order in closed_orders_data:
            contracts = decimal_number(closed_order['info']['cumExecQty'] or 0)
            if not contracts:
                continue
            contract = closed_order['symbol']
            symbol = get_symbol(contract)
            if not symbol:
                continue
            updated_timestamp = int(closed_order['info']['updatedTime'])
            datetime_string = TimeStamp.format_datetime(
                TimeStamp.get_local_dt_from_timestamp(updated_timestamp))
            status = closed_order['info']['orderStatus']
            average_price = decimal_number(closed_order['info']['avgPrice'] or 0)
            trigger_price = decimal_number(closed_order['info']['triggerPrice'] or 0)
            price = decimal_number(average_price or trigger_price or closed_order['info']['price'] or 0)
            trigger_by = closed_order['info']['triggerBy'].replace('Price', '')
            create_type = closed_order['info'].get('createType', '').replace('CreateBy', '')
            create_type = create_type.replace('Closing', 'Close')
            if create_type == 'User':
                create_type = 'Open'
            side = closed_order['info']['side']
            stop_order_type = closed_order['info']['stopOrderType']
            is_stop_type = False
            if not create_type and symbol[-1] == 'spot':
                create_type = 'Open' if side == 'Buy' else 'Close'
                if any(x in create_type.lower() for x in self._stop_types):
                    is_stop_type = True
            elif stop_order_type or any(x in create_type.lower() for x in self._stop_types):
                side = 'Short' if side == 'Buy' else 'Long'
                is_stop_type = True
            else:
                side = 'Long' if side == 'Buy' else 'Short'
            order_price_type = closed_order['info']['orderType']
            order_type = create_type + bool(order_price_type) * (' ' + order_price_type)
            mark_price = price
            fee_cost = decimal_number(closed_order['fee']['cost'] or 0)
            fee_currency = closed_order['fee']['currency']
            if symbol[0] == fee_currency:
                commission = price * fee_cost
            else:
                commission = fee_cost
            commission = round(commission, 4)
            reduce_only = closed_order['info']['reduceOnly']
            time_in_force = closed_order['info']['timeInForce']
            if time_in_force == 'GTC':
                time_in_force = 'Good-Till-Canceled'
            elif time_in_force == 'IOC':
                time_in_force = 'Immediate-Or-Cancel'
            elif time_in_force == 'FOK':
                time_in_force = 'Fill-Or-Kill'
            real_size = contracts * mark_price
            size = f"{contracts}/{round(real_size, 2)}"
            real_price = price
            price = f"{price} ({trigger_by if trigger_by else 'Last'})"
            closed_orders.append({
                'timestamp': updated_timestamp,
                'datetime': datetime_string,
                'contract': contract,
                'real_size': real_size,
                'size': size,
                'side': side,
                'order': order_type,
                'status': status,
                'real_price': real_price,
                'price': price,
                'tp_sl': '',
                'commission': commission,
                'reduce_only': reduce_only,
                'time_in_force': time_in_force,
                'contracts': contracts,
                'is_stop_type': is_stop_type,
                'symbol': symbol,
                'type': symbol[-1]
            })
        try:
            closed_orders.sort(key=lambda x: (x['timestamp'], x['is_stop_type']))
            d = dict()
            for closed_order in closed_orders:
                if closed_order['symbol'][-1] == 'spot':
                    contract = closed_order['contract']
                else:
                    contract = (closed_order['contract'], closed_order['side'])
                price = closed_order['real_price']
                side = closed_order['side']
                contracts = closed_order['contracts']
                commission = closed_order['commission']
                real_size = closed_order['real_size']
                base_currency = closed_order['symbol'][1]
                if closed_order['is_stop_type']:
                    old_price, old_contracts = d.get(contract, [0, 0])
                    if old_contracts == 0:
                        d[contract] = [0, 0]
                        closed_order['tp_sl'] = '-'
                        continue
                    new_contracts = max(0, old_contracts - contracts)
                    if new_contracts > 0:
                        d[contract] = [old_price, new_contracts]
                    elif contract in d:
                        d.pop(contract)
                    real_size = min(real_size, price * old_contracts)
                    p = old_price / price
                    real_base_value = real_size * (1 - p) * (-1 if side == 'Short' else 1) - commission
                    tmp = real_base_value * 100 / real_size
                    tp_sl = f"{round(tmp, 2):+}% ({round(real_base_value, 2):+} {base_currency})"
                    closed_order['tp_sl'] = any(x in '123456789' for x in tp_sl) and tp_sl or ''
                else:
                    old_price, old_contracts = d.get(contract, [0, 0])
                    new_price = (old_price * old_contracts + price * contracts) / (old_contracts + contracts)
                    new_contracts = old_contracts + contracts
                    d[contract] = [new_price, new_contracts]
                    tmp = commission / real_size * 100
                    tp_sl = f"{-round(tmp, 4):+}% ({-round(commission, 4):+} {base_currency})"
                    closed_order['tp_sl'] = any(x in '123456789' for x in tp_sl) and tp_sl or ''
        except Exception as e:
            traceback.print_exc()
            self._logger.log(*e.args)
        return closed_orders

    async def _fetch_canceled_orders(self):
        canceled_orders = []
        swap_canceled_orders = await self._async_run(self._connection.fetch_canceled_orders,
                                                     None, None, None, {'type': 'swap'})
        spot_canceled_orders = await self._async_run(self._connection.fetch_canceled_orders,
                                                     None, None, None, {'type': 'spot'})
        canceled_orders_data = swap_canceled_orders + spot_canceled_orders
        for canceled_order in canceled_orders_data:
            contracts = decimal_number(canceled_order['info']['qty'] or 0)
            if not contracts:
                continue
            contract = canceled_order['symbol']
            symbol = get_symbol(contract)
            if not symbol:
                continue
            updated_timestamp = int(canceled_order['info']['updatedTime'])
            datetime_string = TimeStamp.format_datetime(
                TimeStamp.get_local_dt_from_timestamp(updated_timestamp))
            reason = canceled_order['info']['orderStatus']
            cancel_type = canceled_order['info']['cancelType'].replace('CancelBy', '')
            if reason in ('Cancelled', 'Canceled'):
                if cancel_type == 'UNKNOWN':
                    reason = canceled_order['info']['rejectReason'].replace('EC_', '')
                else:
                    reason = f"{reason} by {cancel_type}"
            average_price = decimal_number(canceled_order['info']['avgPrice'] or 0)
            trigger_price = decimal_number(canceled_order['info']['triggerPrice'] or 0)
            price = decimal_number(average_price or trigger_price or canceled_order['info']['price'] or 0)
            trigger_by = canceled_order['info']['triggerBy'].replace('Price', '')
            create_type = canceled_order['info'].get('createType', '').replace('CreateBy', '')
            create_type = create_type.replace('Closing', 'Close')
            if create_type == 'User':
                create_type = 'Open'
            side = canceled_order['info']['side']
            stop_order_type = canceled_order['info']['stopOrderType']
            if not create_type and symbol[-1] == 'spot':
                create_type = 'Open' if side == 'Buy' else 'Close'
            elif stop_order_type or any(x in create_type.lower() for x in self._stop_types):
                side = 'Short' if side == 'Buy' else 'Long'
            else:
                side = 'Long' if side == 'Buy' else 'Short'
            order_price_type = canceled_order['info']['orderType']
            order_type = create_type + bool(order_price_type) * (' ' + order_price_type)
            mark_price = price
            reduce_only = canceled_order['info']['reduceOnly']
            time_in_force = canceled_order['info']['timeInForce']
            if time_in_force == 'GTC':
                time_in_force = 'Good-Till-Canceled'
            elif time_in_force == 'IOC':
                time_in_force = 'Immediate-Or-Cancel'
            elif time_in_force == 'FOK':
                time_in_force = 'Fill-Or-Kill'
            real_size = contracts * mark_price
            size = f"{contracts}/{round(real_size, 2)}"
            real_price = price
            price = f"{price} ({trigger_by if trigger_by else 'Last'})"
            canceled_orders.append({
                'timestamp': updated_timestamp,
                'datetime': datetime_string,
                'contract': contract,
                'real_size': real_size,
                'size': size,
                'side': side,
                'order': order_type,
                'reason': reason,
                'real_price': real_price,
                'price': price,
                'reduce_only': reduce_only,
                'time_in_force': time_in_force,
                'type': symbol[-1]
            })
        return canceled_orders

    async def _fetch_ledger(self):
        ledger_result = []
        ledger_data = await self._async_run(self._connection.fetch_ledger)
        for ledger in ledger_data:
            transaction_timestamp = int(ledger['info']['transactionTime'])
            datetime_string = TimeStamp.format_datetime(
                TimeStamp.get_local_dt_from_timestamp(transaction_timestamp))
            contract = ledger['info']['symbol']
            transaction_type = ledger['info']['type']
            side = ledger['info']['side']
            quantity = decimal_number(ledger['info']['qty'] or 0)
            filled_price = decimal_number(ledger['info']['tradePrice'] or 0)
            funding = decimal_number(ledger['info']['funding'] or 0)
            fee_paid = 0 if funding else decimal_number(ledger['info']['feeRate'] or 0) * filled_price * quantity
            cash_flow = decimal_number(ledger['info']['cashFlow'] or 0)
            change = decimal_number(ledger['info']['change'] or 0)
            cash_balance = decimal_number(ledger['info']['cashBalance'] or 0)
            funding = round(funding, 5)
            fee_paid = round(fee_paid, 5)
            change = round(change, 5)
            cash_balance = round(cash_balance, 5)
            ledger_result.append({
                'timestamp': transaction_timestamp,
                'datetime': datetime_string,
                'contract': contract,
                'type': transaction_type,
                'side': side,
                'quantity': quantity,
                'filled_price': filled_price,
                'funding': funding,
                'fee_paid': fee_paid,
                'cash_flow': cash_flow,
                'change': change,
                'cash_balance': cash_balance
            })
        return ledger_result

    async def force_update_trading_data(self, *, only_reset=False):
        self.check()
        try:
            if only_reset:
                with self._pol_lock:
                    self._pol_cache_ts = 0
                return
            closed_orders = await self._fetch_closed_orders(_save_closed_orders_data=True)
            positions = await self._fetch_positions(usdc=True, _save_markers=True,
                                                    _load_closed_orders_data=True)
            open_orders = await self._fetch_open_orders(usdc=True, _load_markers=True,
                                                        _load_closed_orders_data=True)
            canceled_orders = await self._fetch_canceled_orders()
            ledger = await self._fetch_ledger()
            now_timestamp = TimeStamp.get_local_dt_from_now().timestamp()
            trading_data = {
                TradingWorker.POSITIONS: positions,
                TradingWorker.OPEN_ORDERS: open_orders,
                TradingWorker.CLOSED_ORDERS: closed_orders,
                TradingWorker.CANCELED_ORDERS: canceled_orders,
                TradingWorker.LEDGER: ledger
            }
            with self._pol_lock:
                self._pol_cache = trading_data
                self._pol_cache_ts = now_timestamp
        except ccxt.NetworkError as e:
            traceback.print_exc()
            self._logger.log(*e.args)
            await self._connection_aborted_callback()
            return
        except BaseException as e:
            traceback.print_exc()
            self._logger.log(*e.args)
            raise

    async def fetch_trading_data(self, *, force=False, number_of_seconds_to_update=5) -> dict:
        with self._pol_lock:
            if not force and self._pol_cache:
                now_timestamp = TimeStamp.get_local_dt_from_now().timestamp()
                n_seconds = number_of_seconds_to_update
                if now_timestamp < self._pol_cache_ts + n_seconds:
                    return self._pol_cache
            try:
                await self.force_update_trading_data()
            except:
                pass
            return self._pol_cache

    async def block(self, *,
                    name: str,
                    balance: Decimal,
                    contracts: set,
                    clear_before: bool = False) -> tuple[set, Decimal]:
        with self._blocks_lock:
            contracts_init = contracts.copy()
            tmp_dict = self._blocks_contracts.get(name, dict())
            if not clear_before:
                contracts.update(tmp_dict.keys())
            for k, v in self._blocks_contracts.items():
                if k != name:
                    contracts.difference_update(v)
            now_timestamp = TimeStamp.get_local_dt_from_now().timestamp()
            contracts_dict = dict()
            for x in contracts:
                if x in tmp_dict and x not in contracts_init:
                    timestamp = tmp_dict[x]
                else:
                    timestamp = now_timestamp
                contracts_dict[x] = timestamp
            if balance < 0:
                balance = Decimal(0)
            self._blocks_contracts[name] = contracts_dict
            self._blocks_balance[name] = balance
            return set(self._blocks_contracts[name].keys()), self._blocks_balance[name]

    def unblock(self, *, name: str, contracts: Union[set, None] = None) -> tuple[set, Decimal]:
        with self._blocks_lock:
            if contracts is None or name not in self._blocks_contracts or name not in self._blocks_balance:
                if name in self._blocks_contracts:
                    self._blocks_contracts.pop(name)
                if name in self._blocks_balance:
                    self._blocks_balance.pop(name)
                return set(), Decimal(0)
            block_contracts = self._blocks_contracts[name]
            for x in contracts:
                if x in block_contracts:
                    block_contracts.pop(x)
            return set(self._blocks_contracts[name].keys()), self._blocks_balance[name]

    def get_block(self, *, name: str) -> tuple[set, Decimal]:
        with self._blocks_lock:
            contracts = dict()
            balance = Decimal(0)
            if name in self._blocks_contracts:
                contracts = self._blocks_contracts[name]
            if name in self._blocks_balance:
                balance = self._blocks_balance[name]
            return set(contracts.keys()), balance

    async def _fetch_data_by_name(self, name: str, data_type: str):
        with self._pol_lock:
            if name is None:
                trading_data = await self.fetch_trading_data()
                return trading_data[data_type]
            data = []
            contracts_dict = self._blocks_contracts.get(name, dict())
            if not contracts_dict:
                return data
            trading_data = await self.fetch_trading_data()
            current_data = trading_data[data_type]
            for data_item in current_data:
                timestamp = TimeStamp.normalize_timestamp(data_item['timestamp'])
                contract = data_item['contract']
                if contract in contracts_dict and timestamp >= contracts_dict[contract]:
                    data.append(data_item)
            return data

    async def fetch_positions(self, name: Union[str, None]):
        await self._fetch_data_by_name(name, TradingWorker.POSITIONS)

    async def fetch_open_orders(self, name: Union[str, None]):
        await self._fetch_data_by_name(name, TradingWorker.OPEN_ORDERS)

    async def fetch_closed_orders(self, name: Union[str, None]):
        await self._fetch_data_by_name(name, TradingWorker.CLOSED_ORDERS)

    async def fetch_canceled_orders(self, name: Union[str, None]):
        await self._fetch_data_by_name(name, TradingWorker.CANCELED_ORDERS)

    async def fetch_ledger(self, name: Union[str, None]):
        await self._fetch_data_by_name(name, TradingWorker.LEDGER)

    async def _fetch_ohlcv(self, *,
                           contract: str,
                           timeframe: str,
                           date_from_timestamp: int,
                           date_to_timestamp: int,
                           price_type: Literal['OHLCV', 'MARK', 'INDEX', 'PREMIUM_INDEX'] = 'OHLCV',
                           old_ohlc_data: list = None,
                           old_volume_data: list = None,
                           in_place: bool = False) -> (list, list, float):
        self.check()
        if old_ohlc_data is None:
            old_ohlc_data = []
        if old_volume_data is None:
            old_volume_data = []

        method_func = self._price_types.get(price_type) or self._price_types[next(iter(self._price_types))]

        candles = TimeStamp.get_number_of_candles(timeframe,
                                                  date_from_timestamp,
                                                  date_to_timestamp)
        candles_needed = candles - len(old_ohlc_data) + bool(len(old_ohlc_data) == candles) + 1
        if candles_needed == 0:
            return old_ohlc_data, old_volume_data, date_from_timestamp

        full_data = []
        current_timestamp = TimeStamp.convert_local_to_utc_timestamp(
            old_ohlc_data[-1][0] if old_ohlc_data else date_from_timestamp)
        while True:
            if contract.lower() != 'random':
                data = method_func(symbol=contract,
                                   timeframe=timeframe,
                                   since=current_timestamp,
                                   limit=candles_needed)
            else:
                data = make_brownian_motion(date_from_ts=current_timestamp,
                                            timeframe=timeframe,
                                            count=candles_needed)
            if not data:
                break
            if not full_data and not old_ohlc_data and date_from_timestamp < data[0][0]:
                date_from_timestamp = data[0][0]
                candles = TimeStamp.get_number_of_candles(timeframe,
                                                          date_from_timestamp,
                                                          date_to_timestamp)
                candles_needed = candles - len(old_ohlc_data) + bool(len(old_ohlc_data) == candles) + 1
                if candles_needed == 0:
                    return old_ohlc_data, old_volume_data, date_from_timestamp
                continue
            full_data.extend(data)
            candles_needed -= len(data)
            if candles_needed <= 0:
                break
            timestamp = current_timestamp
            current_timestamp = data[-1][0]
            if timestamp == current_timestamp:
                break
        tmp_data = []
        for x in full_data:
            if not tmp_data or tmp_data[-1][0] < x[0]:
                tmp_data.append(x)
        full_data = tmp_data
        new_candles = []
        new_volumes = []
        for x in full_data:
            timestamp, *ohlcv = x
            timestamp = TimeStamp.convert_utc_to_local_timestamp(timestamp)
            open, high, low, close, volume = map(decimal_number, ohlcv)
            new_candles.append([timestamp, open, high, low, close])
            new_volumes.append([timestamp, volume])
        if not in_place:
            old_ohlc_data = old_ohlc_data.copy()
            old_volume_data = old_volume_data.copy()
        if old_ohlc_data and new_candles and old_ohlc_data[-1][0] == new_candles[0][0]:
            old_ohlc_data.pop(-1)
            old_volume_data.pop(-1)
        old_ohlc_data.extend(new_candles)
        old_volume_data.extend(new_volumes)
        real_date_from_timestamp = date_from_timestamp
        return old_ohlc_data, old_volume_data, real_date_from_timestamp

    async def fetch_ohlcv(self, *,
                          contract: str,
                          timeframe: str = '1m',
                          date_from_timestamp: int,
                          date_to_timestamp: int,
                          price_type: Literal['OHLCV', 'MARK', 'INDEX', 'PREMIUM_INDEX'] = 'OHLCV',
                          old_ohlc_data: list = None,
                          old_volume_data: list = None,
                          in_place: bool = False):
        try:
            return await self._fetch_ohlcv(
                contract=contract,
                timeframe=timeframe,
                date_from_timestamp=date_from_timestamp,
                date_to_timestamp=date_to_timestamp,
                price_type=price_type,
                old_ohlc_data=old_ohlc_data,
                old_volume_data=old_volume_data,
                in_place=in_place
            )
        except BaseException as e:
            traceback.print_exc()
            self._logger.log(*e.args)
        return old_ohlc_data, old_volume_data, date_from_timestamp
