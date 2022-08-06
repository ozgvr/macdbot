import json

def reset(account):
    trades_file = open("data.json","w")
    data = {}
    data["account"]=account
    data["profit"]=1
    data["winning_trades"]=0
    data["open_trades"]=0
    data["closed_trades"]=0
    data["trades"]=[]
    json.dump(data,trades_file, indent=2)
    trades_file.close()

if __name__ == "__main__":
    reset(input("Account size : "))
