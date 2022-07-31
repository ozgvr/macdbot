import config
import telegram

import talib
import numpy as np

import json
import time
import datetime
import requests

from binance.client import Client
from binance.enums import * 

client = Client(config.API_KEY, config.API_SECRET, tld='com')

stop_loss_perc = 2
profit_perc = 2
status = "OPEN"
blacklist = ["RUB","EUR","TRY","GBP","AUD","UAH","BRL","NGN","DAI","BIDR","IDRT","PAX","VAI","BTTC"]
whitelist = ["AVAX","MATIC","AR","CRV","CHR","CVC","COS","NBS","SAND","DGB","DNT","ENJ","ERN","RAY","RUNE"]

def perc_change(a,b):
    return ((a-b)/b)*100

def get_sell_quantity(sq,symbol):
    stepsizes = []
    for f in client.get_symbol_info(symbol)["filters"]:
        if (f["filterType"]=="LOT_SIZE" or f["filterType"]=="MARKET_LOT_SIZE"):
            stepsizes.append(f["stepSize"])
    print(stepsizes)
    return convert_precision(sq,get_precision(float(max(stepsizes))))
    
def get_precision(step):
    precision = 0
    if(step==0):
        return 200
    while(step!=1.0):
        step = step * 10
        precision = precision + 1
    return precision
    
def convert_precision(value, precision):
    if(precision==200):
        return value
    dot = ""
    whole,decimal = str(value).split('.')
    if(precision==0):
        return int(whole)
    else:
        dot = "."
        return str(whole)+str(dot)+str(decimal)[:precision]

def buy_order(symbol):
    buy_quantity = client.get_asset_balance("USDT")['free']
    try:
        return client.create_order(symbol=symbol, side="BUY", type=ORDER_TYPE_MARKET, quoteOrderQty=buy_quantity)
    except Exception as e:
        return e

def sell_order(symbol):

    sell_quantity = client.get_asset_balance(symbol[:-4])['free']
    sell_quantity = get_sell_quantity(sell_quantity,symbol)
    print(sell_quantity)
    try:
        return client.create_order(symbol=symbol, side="SELL", type=ORDER_TYPE_MARKET, quantity=sell_quantity)
    except Exception as e:
        return e

def klines(symbol):
    candles = [float(x[4]) for x in client.get_klines(symbol=symbol, interval=Client.KLINE_INTERVAL_15MINUTE, limit=200)]
    if len(candles)==200:
        return candles
    else:
        return None

def technicals(symbol):
    candles = klines(symbol)
    if candles is not None:
        close = np.array(candles)
        macd, macdsignal, macdhist = talib.MACDEXT(close, fastperiod=12, fastmatype=talib.MA_Type.EMA, slowperiod=26, slowmatype=talib.MA_Type.EMA, signalperiod=9, signalmatype=talib.MA_Type.EMA)
        ema = talib.EMA(close, timeperiod=200)
        
        return [symbol,float(close[-1]),float(ema[-1]),float(macd[-1]),float(macdsignal[-1]),float(macdhist[-1]),float(macdhist[-2])]
    else:
        return None


def sell(symbol,position_price,close):
    status = "OPEN"
    print("SELL {}".format(symbol))
    f = open("data.json","r+")
    data = json.loads(f.read())
    data["trades"][0].update({
            "position_sell_price":float(close),
            "position_type":"close",
            "sell_timestamp":str(datetime.datetime.now())
        }) 
    if(float(close)>position_price):
        data["winning_trades"]+=1
    data["open_trades"]-=1
    data["closed_trades"]+=1
    data["profit"]=float(data["profit"])*((float(close)/position_price)-0.075)
    telegram.send_alert(data)
    f.seek(0)
    json.dump(data,f)
    f.close()

def monitor(symbol,position_price,ema):
    if abs(perc_change(ema,position_price))>stop_loss_perc:
        stop = position_price*((100-stop_loss_perc)/100)
    else: 
        stop = ema
    if abs(perc_change(ema,position_price))>stop_loss_perc:
        profit = position_price*((100+(stop_loss_perc*profit_perc))/100)
    else:
        profit = position_price*((100+(abs(perc_change(ema,position_price))*profit_perc))/100)
    
    while True:
        close = float(client.get_symbol_ticker(symbol=symbol)["price"]) 
        print("{}|{}|{}".format(stop,close,profit))
        if close>=profit or close<=stop:
            sell(symbol,position_price,close)
            return
        else:
            time.sleep(30)

def buy(symbol,price,ema):
    print("BUY {}".format(symbol))
    status = "CLOSE"

    f = open("data.json","r+")
    data = json.loads(f.read())
    new_data = {}
    new_data.update({
            "ticker":str(symbol),
            "position_buy_price":float(price),
            "position_type":"open",
            "buy_timestamp":str(datetime.datetime.now())
        }) 
    data["trades"].insert(0,new_data)
    data["open_trades"]+=1
    telegram.send_alert(data)
    f.seek(0)
    json.dump(data,f)
    f.close()

    monitor(symbol,price,ema)

def list_tickers():
    list = json.loads(requests.get('https://api.binance.com/api/v3/exchangeInfo').text)
    stablecoins = ["USDC","BUSD","USDP","TUSD"]
    pairs = []

    for pair in list['symbols']:
        if pair['baseAsset'] not in stablecoins and pair['baseAsset'] not in blacklist and pair['status'] == "TRADING" and pair['quoteAsset'] == "USDT" and pair['baseAsset'][-4:] != "DOWN" and pair['baseAsset'][-4:] != "BEAR" and pair['baseAsset'][-2:] != "UP" and pair['baseAsset'][-4:] != "BULL":
            pairs.append(pair['symbol'])
        
    return pairs

def condition(technicals):
    symbol, price, ema, macd, signal, hist, previous_hist = technicals
    if price>ema and macd<0 and hist>0 and previous_hist<0 and status=="OPEN":
        return buy(symbol,price,ema)
    else:
        return False

def check():
    start = time.time()
    for ticker in list_tickers():
        technical = technicals(ticker)
        condition(technical)
    print(time.time()-start, "seconds")

while True:
    check()
    print("No new candle")