def avg_price(data):
    return sum([float(fill["price"])*float(fill["qty"]) for fill in data["fills"]])/sum([float(fill["qty"]) for fill in data["fills"]])

def perc_change(num_1,num_2):
    return ((num_1-num_2)/num_2)*100

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