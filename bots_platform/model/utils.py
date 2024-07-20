quote_coins = frozenset({
    'USDT', 'USD', 'USDC', 'PERP', 'USDE', 'EUR', 'BRL', 'BTC', 'ETH', 'DAI', 'BRZ', 'FDUSD'
})


def get_symbol(contract):
    global quote_coins
    market_type = 'spot'
    symbol = ''.join(x for x in contract.upper() if x.isalnum() or x in '/-:').split('/')
    if len(symbol) == 1:
        symbol = symbol[0]
        for coin in quote_coins:
            if symbol.endswith(coin):
                market_type = 'linear'
                return [symbol[:symbol.rfind(coin)] or symbol, coin if coin != 'PERP' else 'USDC', market_type]
        return []
    base_coin = symbol[0]
    quote_base_coin = symbol[1]
    p = quote_base_coin.find(':')
    if p != -1:
        quote_coin = quote_base_coin[p + 1:]
        quote_base_coin = quote_base_coin[:p]
        if quote_coin.startswith(base_coin) and not quote_coin[len(base_coin):len(base_coin)+1].isalnum():
            market_type = 'inverse'
        else:
            market_type = 'linear'
    return [base_coin, quote_base_coin, market_type]


def get_market_type(contract):
    return get_symbol(contract)[-1]


def get_trading_view_url(contract):
    try:
        base_coin, quote_coin, market_type = get_symbol(contract)
    except:
        return ''
    if market_type == 'spot':
        return f"https://ru.tradingview.com/symbols/{base_coin}{quote_coin}/?exchange=BYBIT"
    elif market_type == 'linear' or market_type == 'inverse':
        return f"https://ru.tradingview.com/symbols/{base_coin}{quote_coin}.P/?exchange=BYBIT"
    return ''


def get_exchange_trade_url(contract):
    global quote_coins
    try:
        base_coin, quote_coin, market_type = get_symbol(contract)
    except:
        return ''
    if market_type == 'spot':
        return f"https://www.bybit.com/trade/spot/{base_coin}/{quote_coin}"
    elif market_type == 'linear':
        if quote_coin == 'USDT':
            return f"https://www.bybit.com/trade/usdt/{base_coin}{quote_coin}"
        for coin in quote_coins:
            if coin == quote_coin:
                if quote_coin == 'USDC':
                    quote_coin = 'PERP'
                return f"https://www.bybit.com/trade/futures/{coin.lower()}/{base_coin}-{quote_coin}"
    elif market_type == 'inverse':
        return f"https://www.bybit.com/trade/inverse/{base_coin}{quote_coin}"
    return ''


def strip_tags(string):
    in_tag = False
    result = ''
    prev = ''
    for x in string:
        if prev != '\\' and x == '>':
            in_tag = False
        elif prev != '\\' and x == '<':
            in_tag = True
        elif not in_tag:
            result += x
        prev = x
    return result
