from bs4 import BeautifulSoup
import requests
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
from time import sleep
from collections import defaultdict
import os

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

from flask import Flask, jsonify, request, redirect, url_for

def init():
    global tags
    global index
    global data
    for i in tags.keys():
        sleep(3)
        d = {}
        url = f"https://www.screener.in/company/{i}/consolidated"
        d["name"] = i
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        div = soup.find('ul', {'id': 'top-ratios'})
        print(i)
        nums = div.find_all('span', {'class': 'number'})
        cap = int("".join(str(nums[0]).split("</")[0][21:].split(",")))
        d["market_cap"] = cap
        price = int("".join(str(nums[1]).split("</")[0][21:].split(",")))
        d["price"] = price
        high = int("".join(str(nums[2]).split("</")[0][21:].split(",")))
        d["high"] = high
        low = int("".join(str(nums[3]).split("</")[0][21:].split(",")))
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

def alert(name, action):
    msg = EmailMessage()
    msg['Subject'] = f'Stock Action Alert - {action} {name}'
    msg['From'] = 'nk1804417@gmail.com'
    msg['To'] = 'kishor2376@gmail.com'
    msg.set_content(
        f"Stock data for {name} has triggered an {action} alert."
    )
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login('nk1804417@gmail.com', 'ootd rwtk hxyh ygod')
        smtp.send_message(msg)


app = Flask(__name__)


@app.route("/", methods=["GET","POST"])
def home():
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

        if i in holdings.keys():
            if holdings[i][-1] * (1+k) < price:
                alert(i, "Buy", 0)
            elif holdings[i][-1] * (1-k) > price:
                alert(i, "Sell", 1)


    return "done"

@app.route("/background", methods=["GET","POST"])
def background():
    print("exec2")
    global tags
    global index
    global data
    for i in tags.keys():
        sleep(1)
        url = f"https://www.screener.in/company/{i}/consolidated"
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        div = soup.find('ul', {'id': 'top-ratios'})
        nums = div.find_all('span', {'class': 'number'})
        cap = int("".join(str(nums[0]).split("</")[0][21:].split(",")))
        high = int("".join(str(nums[2]).split("</")[0][21:].split(",")))
        low = int("".join(str(nums[3]).split("</")[0][21:].split(",")))
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
    tags[query] = tk
    global index
    global data
    index[query] = len(data) 
    url = f"https://www.screener.in/company/{query}/consolidated"
    d = {}
    d["name"] = query
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    div = soup.find('ul', {'id': 'top-ratios'})
    nums = div.find_all('span', {'class': 'number'})
    cap = int("".join(str(nums[0]).split("</")[0][21:].split(",")))
    d["market_cap"] = cap
    price = int("".join(str(nums[1]).split("</")[0][21:].split(",")))
    d["price"] = price
    high = int("".join(str(nums[2]).split("</")[0][21:].split(",")))
    d["high"] = high
    low = int("".join(str(nums[3]).split("</")[0][21:].split(",")))
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
    url = f"https://www.screener.in/api/company/{tags[query]}/peers"
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
    global data
    global index
    global holdings
    if query not in index.keys():
        return "Stock not in monitoring list"
    if holdings[query] == []:
        holdings[query] = [data[index[query]]['price']]
    else:
        holdings[query].append(data[index[query]]['price'])
    
    return redirect("/portfolio")

@app.route('/sell', methods=["GET","POST"])
def sell():
    query = request.args.get('q')
    global holdings
    if holdings[query] != []:
        holdings[query].pop(-1)
        return redirect("/portfolio")
    else:
        return "no stock to sell"

@app.route('/portfolio', methods=["GET","POST"])
def port():
    global holdings
    return holdings





scheduler = BackgroundScheduler()
scheduler.add_job(func=update, trigger="interval", minutes=5)
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
