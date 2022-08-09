import json
from os import scandir
import threading
import time
import datetime

import talib
import numpy as np
import requests

from binance.client import Client
from binance.enums import *

import config
import telegram

client = Client(config.API_KEY, config.API_SECRET, tld='com')

stop_loss_perc = 2
profit_perc = 2
in_trade = False
scanning = False
blacklist = ["RUB","EUR","TRY","GBP","AUD","UAH","BRL","NGN","DAI","BIDR","IDRT","PAX","VAI","BTTC"]
whitelist = ["AVAX","MATIC","AR","CRV","CHR","CVC","COS","NBS","SAND","DGB","DNT","ENJ","ERN","RAY","RUNE"]

def avg_price(data):
    return sum([float(fill["price"])*float(fill["qty"]) for fill in data["fills"]])/sum([float(fill["qty"]) for fill in data["fills"]])

def perc_change(num_1,num_2):
    return ((num_1-num_2)/num_2)*100

def get_sell_quantity(sq,symbol):
    stepsizes = []
    for filters in client.get_symbol_info(symbol)["filters"]:
        if (filters["filterType"]=="LOT_SIZE" or filters["filterType"]=="MARKET_LOT_SIZE"):
            stepsizes.append(filters["stepSize"])
    return convert_precision(sq,get_precision(float(max(stepsizes))))

def get_precision(step):
    precision = 0
    if step==0:
        return 200
    while step!=1.0:
        step = step * 10
        precision = precision + 1
    return precision

def convert_precision(value, precision):
    if precision==200 :
        return value
    dot = ""
    whole,decimal = str(value).split('.')
    if precision==0:
        return int(whole)
    else:
        dot = "."
        return str(whole)+str(dot)+str(decimal)[:precision]

def buy_order(symbol):
    buy_quantity = client.get_asset_balance("USDT")['free']
    try:
        return client.create_order(symbol=symbol, side="BUY", type=ORDER_TYPE_MARKET, quoteOrderQty=buy_quantity)
    except Exception as exception:
        return exception

def sell_order(symbol):

    sell_quantity = client.get_asset_balance(symbol[:-4])['free']
    sell_quantity = get_sell_quantity(sell_quantity,symbol)
    try:
        return client.create_order(symbol=symbol, side="SELL", type=ORDER_TYPE_MARKET, quantity=sell_quantity)
    except Exception as e:
        return e

def klines(symbol):
    try:
        candles = [float(x[4]) for x in client.get_klines(symbol=symbol, interval=Client.KLINE_INTERVAL_15MINUTE, limit=1000)]
    except:
        return None
    return candles

def technicals(symbol):
    candles = klines(symbol)
    if candles is not None:
        close = np.array(candles)
        macd, macdsignal, macdhist = talib.MACDEXT(close, fastperiod=12, fastmatype=talib.MA_Type.EMA, slowperiod=26, slowmatype=talib.MA_Type.EMA, signalperiod=9, signalmatype=talib.MA_Type.EMA)
        ema = talib.EMA(close, timeperiod=200)
        ema3 = talib.EMA(close, timeperiod=200)[-2]<talib.EMA(close, timeperiod=100)[-2] and talib.EMA(close, timeperiod=50)[-2]>talib.EMA(close, timeperiod=100)[-2]

        return [symbol,float(close[-2]),float(ema[-2]),float(macd[-2]),float(macdsignal[-2]),float(macdhist[-2]),float(macdhist[-3]), ema3]
    else:
        return None


def sell(symbol,buy_price):
    global in_trade
    sell_price = float(str(avg_price(sell_order(symbol=symbol)))[:len(str(buy_price))])
    in_trade = False
    print(f"SELL {symbol}")
    trades_file = open("data.json","r+")
    data = json.loads(trades_file.read())
    data["trades"][0].update({
            "position_sell_price":float(sell_price),
            "position_type":"close",
            "sell_timestamp":str(datetime.datetime.now())
        })
    if float(sell_price)>buy_price:
        data["winning_trades"]+=1
    data["open_trades"]-=1
    data["closed_trades"]+=1
    data["profit"]=float(data["profit"])*((float(sell_price)*0.99925/buy_price*1.00075))
    telegram.send_alert(data)
    trades_file.seek(0)
    json.dump(data,trades_file)
    trades_file.close()

def monitor(symbol,buy_price,ema):
    if abs(perc_change(ema,buy_price))>stop_loss_perc:
        stop = buy_price*((100-stop_loss_perc)/100)
    else:
        stop = ema
    if abs(perc_change(ema,buy_price))>stop_loss_perc:
        profit = buy_price*((100+(stop_loss_perc*profit_perc))/100)
    else:
        profit = buy_price*((100+(abs(perc_change(ema,buy_price))*profit_perc))/100)

    while True:
        close = float(client.get_symbol_ticker(symbol=symbol)["price"])
        print(f"{stop}|{close}|{profit}", end = "\r")
        if close>=profit or close<=stop:
            sell(symbol,buy_price)
            return
        else:
            time.sleep(3)

def buy(symbol,close,ema):
    global in_trade
    price = float(str(avg_price(buy_order(symbol=symbol)))[:len(str(close))])
    print(f"BUY {symbol}")
    in_trade = True
    trades_file = open("data.json","r+")
    data = json.loads(trades_file.read())
    new_data = {}
    new_data.update({
            "ticker":str(symbol),
            "position_buy_price":float(price),
            "position_type":"open",
            "buy_timestamp":str(datetime.datetime.now()),
            "ema":float(ema)
        })
    data["trades"].insert(0,new_data)
    data["open_trades"]+=1
    telegram.send_alert(data)
    trades_file.seek(0)
    json.dump(data,trades_file)
    trades_file.close()

    monitor(symbol,price,ema)

def list_tickers():
    tickers = json.loads(requests.get('https://api.binance.com/api/v3/exchangeInfo').text)
    stablecoins = ["USDC","BUSD","USDP","TUSD"]
    pairs = []

    for pair in tickers['symbols']:
        if (pair['baseAsset'] not in stablecoins and pair['baseAsset'] not in blacklist
        and pair['status'] == "TRADING" and pair['quoteAsset'] == "USDT"
        and pair['baseAsset'][-4:] != "DOWN" and pair['baseAsset'][-4:] != "BEAR"
        and pair['baseAsset'][-2:] != "UP" and pair['baseAsset'][-4:] != "BULL"
        ):
            pairs.append(pair['symbol'])
    return pairs


def condition(technicals):
    symbol, price, ema, macd, signal, hist, previous_hist, ema3 = technicals
    print(technicals)
    if price>ema and macd<0 and hist>0 and previous_hist<0 and ema3:
        buy(symbol,price,ema)

def scan():
    global scanning
    scanning = True
    print("-- Checking signals --")
    for ticker in list_tickers():
        condition(technicals(ticker))
        scanning = False
        return
    print("-- No signal --")

def start_scan_thread():
    global scanning
    global in_trade
    if not scanning and not in_trade:
        x = threading.Thread(target=scan, daemon=True)
        x.start()

if __name__ == "__main__":
    candle_time = int(str(json.loads(requests.get("https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=15m&limit=1").text)[0][6])[:-3])
    print(candle_time)
    trades_file = open("data.json","r+")
    data = json.loads(trades_file.read())
    if data["open_trades"] == 1:
        monitor(data["trades"][0]["ticker"],data["trades"][0]["position_buy_price"],data["trades"][0]["ema"])
    trades_file.close()

    while True:
        print(int(time.time()), end = "\r")
        if int(time.time())>candle_time:
            print("True")
            start_scan_thread()
            candle_time = candle_time + 900
            print(candle_time)
        time.sleep(0.5)
