from utils import perc_change

STOP_LOSS_PERC = 2
PROFIT_FACTOR = 2
BLACKLIST = ["RUB","EUR","TRY","GBP","AUD","UAH","BRL","NGN","DAI","BIDR","IDRT","PAX","VAI","BTTC","PAXG"]
WHITELIST = ["AVAX","MATIC","AR","CRV","CHR","CVC","COS","NBS","SAND","DGB","DNT","ENJ","ERN","RAY","RUNE"]

def buy_condition(technicals):
    if not technicals:
        return False
    symbol, price, ema, macd, signal, hist, previous_hist, ma = technicals
    if price>ema and macd<0 and hist>0 and previous_hist<0:
        print("")
        return True
    else:
        return False

def sell_condition(buy_price,ma):

    #ma_diff = abs(perc_change(ma,buy_price))
    #if ma_diff>STOP_LOSS_PERC:
    stop = buy_price*((100-STOP_LOSS_PERC)/100)
    profit = buy_price*((100+(STOP_LOSS_PERC*PROFIT_FACTOR))/100)
    #else:
    #    stop = ma
    #    profit = buy_price*((100+(ma_diff*PROFIT_FACTOR)))/100

    return [stop,profit]
    