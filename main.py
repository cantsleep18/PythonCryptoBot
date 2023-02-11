import ccxt
import pprint
import pandas as pd
import time
import datetime
import volatility
import math

# binance = ccxt.binance()
# btc_ohlcv = binance.fetch_ohlcv("BTC/USDT", "1d", limit=10)

# df = pd.DataFrame(
#     btc_ohlcv, columns=["datetime", "open", "high", "low", "close", "volume"]
# )
# df["datetime"] = pd.to_datetime(df["datetime"], unit="ms")
# df.set_index("datetime", inplace=True)
# print(df)

# orderbook = binance.fetch_order_book("ETH/USDT")
# print(orderbook["asks"])
# print(orderbook["bids"])

with open("binance.key") as f:
    lines = f.readlines()
    api_key = lines[0].strip()
    api_secret = lines[1].strip()

binance = ccxt.binance(
    config={
        "apiKey": api_key,
        "secret": api_secret,
        "enableRateLimit": True,
        "options": {"defaultType": "future"},
    }
)

symbol = "BTC/USDT"
long_target, short_target = volatility.cal_target(binance, symbol)
balance = binance.fetch_balance()
usdt = balance["total"]["USDT"]
op_mode = False
position = {"type": None, "amount": 0}


def cal_amount(usdt_balance, cur_price):
    portion = 0.1
    usdt_trade = usdt_balance * portion
    amount = math.floor((usdt_trade * 100000) / cur_price) / 100000
    return amount


def enter_position(
    exchange, symbol, cur_price, long_target, short_target, amount, position
):
    if cur_price > long_target:
        position["type"] = "long"
        position["amount"] = amount
        exchange.create_market_buy_order(symbol=symbol, amount=amount)
    elif cur_price < short_target:
        position["type"] = "short"
        position["amount"] = amount
        exchange.create_market_sell_order(symbol=symbol, amount=amount)


def exit_position(exchange, symbol, position):
    amount = position["amount"]
    if position["type"] == "long":
        exchange.create_market_sell_order(symbol=symbol, amount=amount)
        position["type"] = None
    elif position["type"] == "short":
        exchange.create_market_buy_order(symbol=symbol, amount=amount)
        position["type"] = None


while True:
    now = datetime.datetime.now()

    if now.hour == 8 and now.minute == 50 and (0 <= now.second < 10):
        if op_mode and position["type"] is not None:
            exit_position(binance, symbol, position)
            op_mode = False

    # update target price
    if now.hour == 9 and now.minute == 0 and (20 <= now.second < 30):
        long_target, short_target = volatility.cal_target(binance, symbol)
        balance = binance.fetch_balance()
        usdt = balance["total"]["USDT"]
        op_mode = True
        time.sleep(10)

    ticker = binance.fetch_ticker(symbol)
    cur_price = ticker["last"]
    amount = cal_amount(usdt, cur_price)

    if op_mode and position["type"] is None:
        enter_position(
            binance, symbol, cur_price, long_target, short_target, amount, position
        )

    print(now, cur_price)
    time.sleep(1)
