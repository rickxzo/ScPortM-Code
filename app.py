from bs4 import BeautifulSoup
import requests
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
from time import sleep
from collections import defaultdict
import os
import sqlite3
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def connect_db():
    conn = sqlite3.connect('db.db')
    return conn

import smtplib
from email.message import EmailMessage

data = []
index = {}
tags = {
    'RELIANCE': 6598251,
    'BEL': 6595017,
    'HARIOMPIPE': 138160777,
    'TARIL': 6599283
}
k = 0.1
holdings = defaultdict(list)

from flask import Flask, jsonify, request, redirect, url_for, render_template

def init():
    global tags
    global index
    global data
    for i in tags.keys():
        sleep(10)
        d = {}
        url = f"https://www.screener.in/company/{i}/consolidated"
        d["name"] = i
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        logger.info(soup)
        div = soup.find('ul', {'id': 'top-ratios'})
        print(i)
        nums = div.find_all('span', {'class': 'number'})
        cap = int("".join(str(nums[0]).split("</")[0][21:].split(",")))
        d["market_cap"] = cap
        price = float("".join(str(nums[1]).split("</")[0][21:].split(",")))
        d["price"] = price
        high = float("".join(str(nums[2]).split("</")[0][21:].split(",")))
        d["high"] = high
        low = float("".join(str(nums[3]).split("</")[0][21:].split(",")))
        d["low"] = low
        pe = float("".join(str(nums[4]).split("</")[0][21:].split(",")))
        d["pe"] = pe
        book = float("".join(str(nums[5]).split("</")[0][21:].split(","))) if str(nums[5]).split("</")[0][21:]!="" else 0
        d["book"] = book 
        roce = float("".join(str(nums[7]).split("</")[0][21:].split(",")))
        d["roce"] = roce
        roe = float("".join(str(nums[8]).split("</")[0][21:].split(",")))
        d["roe"] = roe
        div1 = soup.find('span', {'class': 'font-size-12 down margin-left-4'})
        div2 = soup.find('span', {'class': 'font-size-12 up margin-left-4'})
        dev = str(div1 if div1 is not None else div2)[90:].split("</")[0].strip()[:-1]
        d["deviation"] = float(dev)

        url = f"https://www.screener.in/api/company/{tags[i]}/peers"
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        rows = soup.find_all("tr", attrs={"data-row-company-id": True})
        for j in rows:
            if i in str(j):
                table = str(j).split("\n")[5].split("</td>")
                npqtr = float(table[4][4:])
                qtrpv = float(table[5][4:])
                sqtr = float(table[6][4:])
                qtrsv = float(table[7][4:])
                d["np_qtr"] = npqtr
                d["qtr_profit_var"] = qtrpv
                d["sales_qtr"] = sqtr
                d["qtr_sales_var"] = qtrsv

        data.append(d)
        index[i] = len(data)-1
    print("Data uploaded")

init()

def alert(name, action, id):
    msg = EmailMessage()
    msg['Subject'] = f'Stock Action Alert - {action} {name}'
    msg['From'] = 'nk1804417@gmail.com'
    msg['To'] = 'kishor2376@gmail.com'
    msg.set_content(
        f"Stock data for {name} has triggered an {action} alert for lot ID {id}."
    )
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login('nk1804417@gmail.com', 'ootd rwtk hxyh ygod')
        smtp.send_message(msg)


app = Flask(__name__, template_folder='.', static_folder='static')


@app.route("/", methods=["GET","POST"])
def home():
    return render_template("index.html")

@app.route('/index', methods=["GET","POST"])
def get_index():
    global index
    return index

@app.route('/hold', methods=["GET","POST"])
def get_holding():
    global holdings
    return holdings

@app.route('/tags', methods=["GET","POST"])
def get_tags():
    global tags
    return tags




@app.route("/data", methods=["GET","POST"])
def all_data():
    global data
    return jsonify(data)

@app.route("/update", methods=["GET","POST"])
def update():
    print("exec1")
    global tags
    global data
    global index
    global holdings
    global k
    for i in tags.keys():
        sleep(10)
        url = f"https://www.screener.in/company/{i}/consolidated"
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        div = soup.find('ul', {'id': 'top-ratios'})
        nums = div.find_all('span', {'class': 'number'})
        price = int("".join(str(nums[1]).split("</")[0][21:].split(",")))
        data[index[i]]["price"] = price
        div1 = soup.find('span', {'class': 'font-size-12 down margin-left-4'})
        div2 = soup.find('span', {'class': 'font-size-12 up margin-left-4'})
        dev = str(div1 if div1 is not None else div2)[90:].split("</")[0].strip()[:-1]
        data[index[i]]["deviation"] = float(dev)

        if price <= 0.6 * data[index[i]]["high"]:
            data[index[i]]["tag"] = 1

        elif price >= 0.985 * data[index[i]]["high"]:
            data[index[i]]["tag"] = -1

        else:
            data[index[i]]["tag"] = 0
        '''
        if i in holdings.keys():
            if holdings[i][-1] * (1+k) < price:
                alert(i, "Buy", 0)
            elif holdings[i][-1] * (1-k) > price:
                alert(i, "Sell", 1)

        '''
        if i in holdings.keys():
            for j in holdings[i]:
                if j[0] * (1+k) < price:
                    alert(i, "Buy", j[1])
                elif j[0] * (1-k) > price:
                    alert(i, "Sell", j[1])
    return "done"

@app.route("/background", methods=["GET","POST"])
def background():
    print("exec2")
    global tags
    global index
    global data
    for i in tags.keys():
        sleep(10)
        url = f"https://www.screener.in/company/{i}/consolidated"
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        div = soup.find('ul', {'id': 'top-ratios'})
        nums = div.find_all('span', {'class': 'number'})
        cap = int("".join(str(nums[0]).split("</")[0][21:].split(",")))
        high = float("".join(str(nums[2]).split("</")[0][21:].split(",")))
        low = float("".join(str(nums[3]).split("</")[0][21:].split(",")))
        pe = float("".join(str(nums[4]).split("</")[0][21:].split(",")))
        book = float("".join(str(nums[5]).split("</")[0][21:].split(","))) if str(nums[5]).split("</")[0][21:]!="" else 0
        roce = float("".join(str(nums[7]).split("</")[0][21:].split(",")))
        roe = float("".join(str(nums[8]).split("</")[0][21:].split(",")))
        
        data[index[i]]["market_cap"] = cap
        data[index[i]]["high"] = high
        data[index[i]]["low"] = low
        data[index[i]]["pe"] = pe
        data[index[i]]["book"] = book
        data[index[i]]["roce"] = roce
        data[index[i]]["roe"] = roe

        url = f"https://www.screener.in/api/company/{tags[i]}/peers"
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        rows = soup.find_all("tr", attrs={"data-row-company-id": True})
        for j in rows:
            if i in str(j):
                table = str(j).split("\n")[5].split("</td>")
                npqtr = float(table[4][4:])
                qtrpv = float(table[5][4:])
                sqtr = float(table[6][4:])
                qtrsv = float(table[7][4:])
                data[index[i]]["np_qtr"] = npqtr
                data[index[i]]["qtr_profit_var"] = qtrpv
                data[index[i]]["sales_qtr"] = sqtr
                data[index[i]]["qtr_sales_var"] = qtrsv

    return "done"

@app.route("/list", methods=["GET","POST"])
def list():
    global tags
    return tags

@app.route("/mk", methods=["GET","POST"])
def mk():
    query = request.args.get('q')
    tk = request.args.get('tk')
    global tags
    global index
    global data
    url = f"https://www.screener.in/company/{query}/consolidated"
    d = {}
    d["name"] = query
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    div = soup.find('ul', {'id': 'top-ratios'})
    nums = div.find_all('span', {'class': 'number'})
    cap = int("".join(str(nums[0]).split("</")[0][21:].split(",")))
    d["market_cap"] = cap
    price = float("".join(str(nums[1]).split("</")[0][21:].split(",")))
    d["price"] = price
    high = float("".join(str(nums[2]).split("</")[0][21:].split(",")))
    d["high"] = high
    low = float("".join(str(nums[3]).split("</")[0][21:].split(",")))
    d["low"] = low
    pe = float("".join(str(nums[4]).split("</")[0][21:].split(",")))
    d["pe"] = pe
    book = float("".join(str(nums[5]).split("</")[0][21:].split(","))) if str(nums[5]).split("</")[0][21:]!="" else 0
    d["book"] = book 
    roce = float("".join(str(nums[7]).split("</")[0][21:].split(",")))
    d["roce"] = roce
    roe = float("".join(str(nums[8]).split("</")[0][21:].split(",")))
    d["roe"] = roe
    div1 = soup.find('span', {'class': 'font-size-12 down margin-left-4'})
    div2 = soup.find('span', {'class': 'font-size-12 up margin-left-4'})
    dev = str(div1 if div1 is not None else div2)[90:].split("</")[0].strip()[:-1]
    d["deviation"] = float(dev)
    url = f"https://www.screener.in/api/company/{tk}/peers"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    rows = soup.find_all("tr", attrs={"data-row-company-id": True})
    for j in rows:
        if query in str(j):
            table = str(j).split("\n")[5].split("</td>")
            npqtr = float(table[4][4:])
            qtrpv = float(table[5][4:])
            sqtr = float(table[6][4:])
            qtrsv = float(table[7][4:])
            d["np_qtr"] = npqtr
            d["qtr_profit_var"] = qtrpv
            d["sales_qtr"] = sqtr
            d["qtr_sales_var"] = qtrsv

    data.append(d)
    
    tags[query] = tk
    index[query] = len(data) - 1
    return "done"

@app.route("/rm", methods=["GET","POST"])
def rm():
    query = request.args.get('q')
    global data
    global index
    global tags
    print(index)
    n = index[query]
    for i in range(n, len(data)):
        index[data[i]["name"]] -= 1
    index.pop(query)

    data.pop(n)
    tags.pop(query)
    return "done"
    
@app.route("/ck", methods=["GET", "POST"])
def ck():
    query = request.args.get('q')
    global k
    if query == "NC":
        return str(k)
    k = float(query)
    return f"done : {k}"

@app.route("/buy", methods=["GET","POST"])
def buy():
    query = request.args.get('q')
    num = request.args.get('n')
    price = request.args.get('p')
    date = request.args.get('d')
    day = datetime.now() - timedelta(days=int(date)) if date!="0" else datetime.now()
    global data
    global index
    global holdings
    if query not in index.keys():
        return "Stock not in monitoring list"
    
    conn = connect_db()
    c = conn.cursor()
    c.execute(
        '''
        INSERT INTO Buy (name, price, amt, date) VALUES (?,?,?,?)
        ''', (query, data[index[query]]['price'] if price=="-1" else float(price), int(num), day.strftime("%Y-%m-%d %H:%M:%S"))
    )
    id = c.lastrowid
    conn.commit()
    conn.close()
    if holdings[query] == []:
        holdings[query] = [[data[index[query]]['price'], id]]
    else:
        holdings[query].append([data[index[query]]['price'], id])
    for i in data:
        if i['name'] == query:
            i['num'] = i.get('num', 0) + 1
    return redirect("/portfolio")

@app.route('/sell', methods=["GET","POST"])
def sell():
    query = request.args.get('q')
    id = request.args.get('n')
    price = request.args.get('p')
    date = request.args.get('d')
    day = datetime.now() - timedelta(days=int(date)) if date!="0" else datetime.now()
    global holdings
    if int(id) not in [j[1] for j in holdings[query]]:
        return "No such holding exists"
    holdings[query] = [j for j in holdings[query] if j[1] != int(id)]

    conn = connect_db()
    c = conn.cursor()
    c.execute(
        "SELECT date, price, amt FROM Buy WHERE lid = ?", (int(id),)
    )
    row = c.fetchone()
    buy_price = row[1]
    sell_price = data[index[query]]['price'] if price=="-1" else float(price)
    profit = (sell_price - buy_price) * row[2]
    c.execute(
        '''
        INSERT INTO Sell (lid, profit, sell_price, date) VALUES (?,?,?,?)
        ''', (int(id), profit, sell_price, day.strftime("%Y-%m-%d %H:%M:%S"))
    )
    conn.commit()
    c.execute(
        "SELECT Sell.date, Buy.date FROM Sell JOIN Buy ON Sell.lid = Buy.lid WHERE Sell.lid = ?", (int(id),)
    )
    row = c.fetchone()
    buy_date_str = row[1]
    sell_date_str = row[0]

    buy_date = datetime.strptime(buy_date_str, "%Y-%m-%d %H:%M:%S")
    sell_date = datetime.strptime(sell_date_str, "%Y-%m-%d %H:%M:%S")
    print(buy_date, sell_date)
    duration = (sell_date - buy_date).days
    print(duration)
    c.execute(
        "UPDATE Sell SET duration = ? WHERE lid = ?", (duration, int(id))
    )
    conn.commit()
    conn.close()
    for i in data:
        if i['name'] == query:
            i['num'] = i.get('num', 0) - 1
    return redirect("/portfolio")

@app.route('/portfolio', methods=["GET","POST"])
def port():
    return render_template("port.html")

@app.route('/holding', methods=["GET","POST"])
def holding():
    global holdings
    ids = []
    for i in holdings.keys():
        for j in holdings[i]:
            ids.append(j[1])
    placeholders = ', '.join('?' for _ in ids)
    conn = connect_db()
    c = conn.cursor()
    c.execute(
        f'''
        SELECT * FROM Buy
        WHERE lid IN ({placeholders})
        ''', ids
    )
    rows = c.fetchall()
    print(rows)
    conn.close()
    return jsonify(rows)

@app.route('/history', methods=["GET","POST"])
def hist():
    return render_template("history.html")

@app.route('/hist_data', methods=["GET","POST"])
def history():
    conn = connect_db()
    c = conn.cursor()
    c.execute(
        '''
        SELECT Buy.name, Buy.date, Buy.price, Buy.amt, Sell.date, Sell.profit, Sell.duration, Sell.sell_price, Sell.sid
        FROM Buy
        LEFT JOIN Sell ON Buy.lid = Sell.lid
        WHERE Sell.hidden IS NULL OR Sell.hidden = 0
        ORDER BY Buy.name ASC
        '''
    )
    rows = c.fetchall()
    conn.close()
    return jsonify(rows)

@app.route('/hide', methods=["GET","POST"])
def hide():
    query = request.args.get('q')
    conn = connect_db()
    c = conn.cursor()
    c.execute(
        '''
        UPDATE Sell SET hidden = 1 WHERE sid = ?''', (int(query),)
    )
    conn.commit()
    conn.close()
    return redirect("/history")


scheduler = BackgroundScheduler()
scheduler.add_job(func=update, trigger="interval", minutes=1)
scheduler.add_job(
    func=background,
    trigger="cron",
    hour=00,
    minute=30,
    id="daily_task_job"
)
scheduler.start()
atexit.register(lambda: scheduler.shutdown())


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))  
    app.run(host='0.0.0.0', port=port, debug=True)




















