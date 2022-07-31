import requests
import config

def send_alert(trades):
    total_profit = str(round(((trades["profit"]-1)*100),2))+"%"
    winrate = str(round((trades["winning_trades"]/trades["closed_trades"])*100,2))+"%"
    symbol = trades["trades"][0]["ticker"][:-4]
    buy_price = trades["trades"][0]["position_buy_price"]
    if("position_sell_price" not in trades["trades"][0]):
        message = "BUY {} AT {}".format(symbol,buy_price)
    else:
        sell_price = trades["trades"][0]["position_sell_price"]
        if(sell_price>buy_price):
            result = "WIN"
        else:
            result = "LOSS"
        message = "SELL {} {} {} WR {} AC {}".format(symbol,result,str(round((sell_price-buy_price)/buy_price*100,2))+"%",winrate,total_profit)

    data = {"chat_id":config.CHAT_ID,"text":message}   
    requests.post(url="https://api.telegram.org/"+config.BOT_API+"/sendMessage",data=data)
