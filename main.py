import os
import json
import threading
import time
import file_handler

import talib
import numpy as np
from binance.client import Client
from binance.enums import *
from config import DEBUG, API_KEY, API_SECRET

if not DEBUG:
    API_KEY = os.getenv("API_KEY")
    API_SECRET = os.getenv("API_SECRET")

from utils import avg_price, perc_change, convert_precision, get_precision
from strategy import *
import telegram

client = Client(API_KEY, API_SECRET, tld='com')

IN_TRADE = False
SCANNING = False


def get_sell_quantity(sq, symbol):
    stepsizes = []
    for filters in client.get_symbol_info(symbol)["filters"]:
        if (filters["filterType"] == "LOT_SIZE" or filters["filterType"] == "MARKET_LOT_SIZE"):
            stepsizes.append(filters["stepSize"])
    return convert_precision(sq, get_precision(float(max(stepsizes))))

def buy_order(symbol):
    buy_quantity = client.get_asset_balance("USDT")['free']
    try:
        return client.create_order(symbol=symbol, side="BUY", type=ORDER_TYPE_MARKET, quoteOrderQty=buy_quantity)
    except Exception as e:
        print(e)
        return e

def sell_order(symbol):

    balance_available = client.get_asset_balance(symbol[:-4])['free']
    sell_quantity = get_sell_quantity(balance_available,symbol)

    try:
        return client.create_order(symbol=symbol, side="SELL", type=ORDER_TYPE_MARKET, quantity=sell_quantity)
    except Exception as e:
        print(e)
        return e

def klines(symbol):
    try:
        return [float(x[4]) for x in client.get_klines(symbol=symbol, interval=Client.KLINE_INTERVAL_15MINUTE, limit=1000)]
    except:
        return []

def get_technicals(symbol):
    candles = klines(symbol)
    if candles:
        close = np.array(candles)
        macd, macdsignal, macdhist = talib.MACDEXT(close, fastperiod=12, fastmatype=talib.MA_Type.EMA, slowperiod=26, slowmatype=talib.MA_Type.EMA, signalperiod=9, signalmatype=talib.MA_Type.EMA)
        ema = talib.EMA(close, timeperiod=200)
        ma = talib.SMA(close, timeperiod=200)
        
        return [symbol,float(close[-2]),float(ema[-2]),float(macd[-2]),float(macdsignal[-2]),float(macdhist[-2]),float(macdhist[-3]), float(ma[-2])]
    else:
        return []

def sell(symbol,buy_price):
    global IN_TRADE
    try:
        sell_price = float(str(avg_price(sell_order(symbol=symbol)))[:len(str(buy_price))])
    except Exception as e:
        print(e)
        return
    IN_TRADE = False
    print(f"------ SELL {symbol}")
    data = file_handler.update_sell(sell_price, buy_price)
    telegram.send_alert(data)

def monitor(symbol,buy_price,ma):

    stop, profit = sell_condition(buy_price, ma)
    file_handler.update_stop_profit(stop,profit)

    while True:
        try:
            close = float(client.get_symbol_ticker(symbol=symbol)["price"])
            print(f"------- {symbol} P: {close}| SL: {stop} | TP: {profit} | PNL: %{perc_change(close,buy_price)}")
        except Exception as e:
            print(e)
        if close>=profit or close<=stop:
            print("")
            sell(symbol,buy_price)
            return
        else:
            time.sleep(5)
            

def buy(symbol,close,ma):
    global IN_TRADE
    try:
        price = float(str(avg_price(buy_order(symbol=symbol)))[:len(str(close))])
    except Exception as e:
        print(e)
        return
    print(f"------ BUY {symbol}")
    IN_TRADE = True
    data = file_handler.update_buy(symbol,close,ma)
    telegram.send_alert(data)

    monitor(symbol,price,ma)

def list_tickers():
    tickers = client.get_exchange_info()
    stablecoins = ["USDC","BUSD","USDP","TUSD"]
    pairs = []

    for pair in tickers['symbols']:
        if (pair['baseAsset'] not in stablecoins and pair['baseAsset'] not in BLACKLIST
        and pair['status'] == "TRADING" and pair['quoteAsset'] == "USDT"
        and pair['baseAsset'][-4:] != "DOWN" and pair['baseAsset'][-4:] != "BEAR"
        and pair['baseAsset'][-2:] != "UP" and pair['baseAsset'][-4:] != "BULL"
        ):
            pairs.append(pair['symbol'])
    return pairs

def scan():
    global SCANNING
    SCANNING = True
    print("---- Checking signals")
    tickers = list_tickers()
    for count, ticker in enumerate(tickers):
        print("----- Checking tickers : " + str(count+1) + "/" + str(len(tickers)), end="\r")
        technicals = get_technicals(ticker)
        if technicals:
            if buy_condition(technicals):
                symbol = technicals[0]
                price = technicals[1]
                ma = technicals[-1]
                buy(symbol,price,ma)
                SCANNING = False
                return
    print("")
    print("---- No signal")
    SCANNING = False
    return

if __name__ == "__main__":
    print("- Bot started")
    print("-- Checking for open trades")

    open_trade = file_handler.get_open_trade()
    if open_trade:
        IN_TRADE = True
        print("--- Open trade found")
        print("------ BUY {}".format(open_trade[0]))
        monitor(open_trade[0],open_trade[1],open_trade[2])
    else:
        print("--- No open trade found")
    
    print("-- Starting candle timer")
    while True:
        if not SCANNING and not IN_TRADE:
            if int(time.time())%900 == 0:
                print("")
                print(f"--- New candle close")
                x = threading.Thread(target=scan, daemon=True)
                x.start()
        time.sleep(0.5)
