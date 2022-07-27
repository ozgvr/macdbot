import json
from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def dashboard():
    return render_template('dashboard.html')

@app.route("/api/trades")
def data():
    f = open("data.json","r").read()
    data = json.loads(f)
    return data
    #return "<p>Hello, World!</p>"


if __name__ =='__main__':  
    app.run(debug = True)