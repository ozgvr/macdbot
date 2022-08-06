import json

def reset(account):
    trades_file = open("data.json","r+")
    data = json.loads(trades_file.read())
    data["account"]=account
    data["trades"]=[]
    data["winning_trades"]=0
    data["open_trades"]=0
    data["closed_trades"]=0
    data["profit"]=1
    trades_file.seek(0)
    json.dump(data,trades_file)
    trades_file.close()

if __name__ == "__main__":
    reset(input("Account size : "))
