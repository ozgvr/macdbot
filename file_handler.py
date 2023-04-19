import json
import datetime

def update_sell(sell_price, buy_price):

    with open("data.json","r+") as file:
        data = json.loads(file.read())
    
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

    with open("data.json","w") as file:
        file.write(json.dumps(data))

    return data
    
def update_buy(symbol, price, ma): 

    with open("data.json","r+") as file:
        data = json.loads(file.read())

    new_data = {
    "ticker":str(symbol),
    "position_buy_price":float(price),
    "position_type":"open",
    "buy_timestamp":str(datetime.datetime.now()),
    "ma":float(ma)
    }

    data["trades"].insert(0,
        {"ticker":str(symbol),
        "position_buy_price":float(price),
        "position_type":"open",
        "buy_timestamp":str(datetime.datetime.now()),
        "ma":float(ma)
        })
    data["open_trades"]+=1

    with open("data.json","w") as file:
        file.write(json.dumps(data))

    return data

def update_stop_profit(stop,profit):

    with open("data.json","r+") as file:
        data = json.loads(file.read())

    data["trades"][0].update({
            "stop_loss":float(stop),
            "take_profit":float(profit),
        })
    
    with open("data.json","w") as file:
        file.write(json.dumps(data))

    return data

def get_open_trade():
    
    with open("data.json","r") as file:
        data = json.loads(file.read())
    if data["open_trades"] == 1:
        return [data["trades"][0]["ticker"], data["trades"][0]["position_buy_price"], data["trades"][0]["ma"]]
    else:
        return []
    