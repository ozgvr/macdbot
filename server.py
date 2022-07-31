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

if __name__ =='__main__':
    app.run(host="localhost", port="80",debug = True)
