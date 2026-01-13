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
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def connect_db():
    conn = sqlite3.connect('db.db')
    return conn

import smtplib
from email.message import EmailMessage

data = []
index = {}
tags = {}
alias = {}
rows =  requests.get("https://scportm.pythonanywhere.com/monitors").json()
for row in rows:
    tags[row[1]] = row[3]
    if row[2] != "NA":
        alias[row[1]] = row[2]
        
k1 = 0.1
k2 = 0.1
key=""

holdings = defaultdict(list)

rows = requests.get("https://scportm.pythonanywhere.com/holding").json()
rows.sort(key=lambda row: row[0])
for row in rows:
    holdings[row[1]].append([row[3], row[0]])


from flask import Flask, jsonify, request, redirect, url_for, render_template, Response


def init():
    global tags
    global index
    global data
    for i in tags.keys():
        sleep(10)
        d = {}
        url = f"https://www.screener.in/company/{i}/"
        logger.info(i)
        d["name"] = i
        d["num"] = len(holdings[i]) if i in holdings.keys() else 0
        if i in alias.keys():
            d["alias"] = alias[i]
        while True:
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()  # catches 4xx / 5xx
        
                soup = BeautifulSoup(response.text, 'html.parser')
        
                # success → break loop
                break
        
            except requests.exceptions.HTTPError as e:
                status = e.response.status_code
        
                if status == 404:
                    logger.info(f"404 Not Found → {url}")
                    return "error"   # do NOT retry
        
                logger.info(f"HTTP {status}. Retrying in 60s...")
                time.sleep(60)
        
            except requests.exceptions.RequestException as e:
                # timeout, DNS, connection reset, etc.
                logger.info(f"Network error: {e}. Retrying in 60s...")
                time.sleep(60)
        try:
            soup = BeautifulSoup(response.text, 'html.parser')
            div = soup.find('ul', {'id': 'top-ratios'})
        except Exception as e:
            logger.info(f"73err {e}")
        try:
            nums = div.find_all('span', {'class': 'number'})
        except Exception as e:
            logger.info(e)
        try:
            cap = int("".join(str(nums[0]).split("</")[0][21:].split(",")))
            d["market_cap"] = cap
        except Exception as e:
            d["market_cap"] = -1
            logger.info(f"79err {e}")
        try:
            price = float("".join(str(nums[1]).split("</")[0][21:].split(",")))
            d["price"] = price
        except Exception as e:
            d["price"] = -1
            logger.info(f"84err {e}")
        try:
            high = float("".join(str(nums[2]).split("</")[0][21:].split(",")))
            d["high"] = high
        except Exception as e:
            d["high"] = -1
            logger.info(f"89err {e}")
        try:
            low = float("".join(str(nums[3]).split("</")[0][21:].split(",")))
            d["low"] = low
        except Exception as e:
            d["low"] = -1
            logger.info(f"94err {e}")
        try:
            pe = float("".join(str(nums[4]).split("</")[0][21:].split(",")))
            d["pe"] = pe
        except Exception as e:
            d["pe"] = -1
            logger.info(f"99err {e}")
        try:
            book = float("".join(str(nums[5]).split("</")[0][21:].split(","))) if str(nums[5]).split("</")[0][21:]!="" else 0
            d["book"] = book 
        except Exception as e:
            d["book"] = -1
            logger.info(f"104err {e}")
        try:
            roce = float("".join(str(nums[7]).split("</")[0][21:].split(",")))
            d["roce"] = roce
        except Exception as e:
            d["roce"] = -1
            logger.info(f"109err {e}")
        try:
            roe = float("".join(str(nums[8]).split("</")[0][21:].split(",")))
            d["roe"] = roe
        except Exception as e:
            d["roe"] = -1
            logger.info(f"114err {e}")
        try:
            div1 = soup.find('span', {'class': 'font-size-12 down margin-left-4'})
            div2 = soup.find('span', {'class': 'font-size-12 up margin-left-4'})
            dev = str(div1 if div1 is not None else div2)[90:].split("</")[0].strip()[:-1]
            d["deviation"] = float(dev)
        except Exception as e:
            d["deviation"] = -1
            logger.info(f"121err {e}")

        
        url = f"https://www.screener.in/api/company/{tags[i]}/peers"
        while True:
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()  # catches 4xx / 5xx
        
                soup = BeautifulSoup(response.text, 'html.parser')
        
                break
        
            except requests.exceptions.HTTPError as e:
                status = e.response.status_code
        
                if status == 404:
                    logger.info(f"404 Not Found → {url}")
                    return "error"   # do NOT retry
        
                logger.info(f"HTTP {status}. Retrying in 60s...")
                time.sleep(60)
        
            except requests.exceptions.RequestException as e:
                # timeout, DNS, connection reset, etc.
                logger.info(f"Network error: {e}. Retrying in 60s...")
                time.sleep(60)
        soup = BeautifulSoup(response.text, 'html.parser')
        rows = soup.find_all("tr", attrs={"data-row-company-id": True})
        for j in rows:
            if i in str(j):
                try:
                    table = str(j).split("\n")[5].split("</td>")
                    npqtr = float(table[4][4:])
                    qtrpv = float(table[5][4:])
                    sqtr = float(table[6][4:])
                    qtrsv = float(table[7][4:])
                    d["np_qtr"] = npqtr
                    d["qtr_profit_var"] = qtrpv
                    d["sales_qtr"] = sqtr
                    d["qtr_sales_var"] = qtrsv
                except Exception as e:
                    d["np_qtr"] = -1
                    d["qtr_profit_var"] = -1
                    d["sales_qtr"] = -1
                    d["qtr_sales_var"] = -1
                    logger.info(f"166err {e}")

        try:
            data.append(d)
            index[i] = len(data)-1
        except Exception as e:
            logger.info(f"172err {e}")

init()

def alert(name, action, id):
    try:
        msg = EmailMessage()
        msg['Subject'] = f'Stock Action Alert - {action} {name}'
        msg['From'] = 'nk1804417@gmail.com'
        msg['To'] = 'rickxzo.perz@gmail.com' #'kishor2376@gmail.com'
        msg.set_content(
            f"Stock data for {name} has triggered an {action} alert for lot ID {id}."
        )
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login('nk1804417@gmail.com', 'ootd rwtk hxyh ygod')
            smtp.send_message(msg)
        logger.info("Success 132")
    except Exception as e:
        logger.info(f"Error 134 {e}")
        return "error"


app = Flask(__name__, template_folder='.', static_folder='static')
app.secret_key = "something"


@app.route("/", methods=["GET","POST"])
def home():
    return render_template("index.html")

@app.route('/reset', methods=['GET', 'POST'])
def reset():
    try:
        global key
        rows = requests.get(f"https://scportm.pythonanywhere.com/holding?key={key}").json()
        rows.sort(key=lambda row: row[0])
        holding = defaultdict(list)
        for row in rows:
            holding[row[1]].append([row[3], row[0]])
        global holdings
        holdings = holding
        for item in data:
            item["num"] = len(holding.get(item["name"], []))
        return "done"
    except Exception as e:
        logger.info(f"err 243 {e}")
        return "err"
    

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

@app.route('/sk', methods=["GET","POST"])
def set_key():
    global key 
    key = request.args.get('q')
    return 'done'

@app.route("/update", methods=["GET","POST"])
def update():
    logger.info("exec1")
    global tags
    global data
    global index
    global holdings
    global k1
    global k2
    for i in tags.keys():
        sleep(10)
        url = f"https://www.screener.in/company/{i}/"
        logger.info(f"Updating {i}")
        while True:
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()  # catches 4xx / 5xx
        
                soup = BeautifulSoup(response.text, 'html.parser')
        
                # success → break loop
                break
        
            except requests.exceptions.HTTPError as e:
                status = e.response.status_code
        
                if status == 404:
                    logger.info(f"404 Not Found → {url}")
                    break
        
                logger.info(f"HTTP {status}. Retrying in 60s...")
                time.sleep(60)

            except requests.exceptions.RequestException as e:
                # timeout, DNS, connection reset, etc.
                logger.info(f"Network error: {e}. Retrying in 60s...")
                time.sleep(60)

        try:
            soup = BeautifulSoup(response.text, 'html.parser')
            div = soup.find('ul', {'id': 'top-ratios'})
            nums = div.find_all('span', {'class': 'number'})
        except Exception as e:
            logger.info(f"263err {e}")

        try:
            price = float("".join(str(nums[1]).split("</")[0][21:].split(",")))
            logger.info(f"Price change from {data[index[i]]["price"]} to {price}")
            data[index[i]]["price"] = price
        except Exception as e:
            data[index[i]]["price"] = -1
            logger.info(f"269err {e}")
        try:
            div1 = soup.find('span', {'class': 'font-size-12 down margin-left-4'})
            div2 = soup.find('span', {'class': 'font-size-12 up margin-left-4'})
            dev = str(div1 if div1 is not None else div2)[90:].split("</")[0].strip()[:-1]
            data[index[i]]["deviation"] = float(dev)
        except Exception as e:
            data[index[i]]["deviation"] = -1
            logger.info(f"276err {e}")

        try:
            if price <= 0.6 * data[index[i]]["high"]:
                data[index[i]]["tag"] = 1
    
            elif price >= 0.985 * data[index[i]]["high"]:
                data[index[i]]["tag"] = -1
    
            else:
                data[index[i]]["tag"] = 0
                
        except Exception as e:
            data[index[i]]["tag"] = -2
            logger.info(f"305err {e}")

        try:
            '''
            if i in holdings.keys():
                for j in holdings[i]:
                    logger.info(f'alert conditions: {j[0]} {1+k1} {1-k2}')
                    if float(j[0]) * (1+k1) < float(price):
                        action = "Sell"
                        name = i
                        id = j[1]
                        try:
                            url = "https://scportm.pythonanywhere.com/mail"
                            params = {
                                "a": action,
                                "n": name,
                                "i": id
                            }
                            response = requests.get(url, params=params)
                            logger.info(response.json())  
                        except Exception as e:
                            logger.info(f"Error 134 {e}")
                            break
                    elif float(j[0]) * (1-k2) > float(price):
                        try:
                            action = "Buy"
                            name = i
                            id = j[1]
                            url = "https://scportm.pythonanywhere.com/mail"
                            params = {
                                "a": action,
                                "n": name,
                                "i": id
                            }
                            response = requests.get(url, params=params)
                            logger.info(response.json())  
                        except Exception as e:
                            logger.info(f"Error 134 {e}")
                            break
            '''
            if i in holdings.keys():
                bdiff = float(holdings[i][0][0]) * k1
                sdiff = float(holdings[i][0][0]) * k2
                bn = len(holdings[i])
                ppoint = float(holdings[i][bn-1][0])
                if ppoint + sdiff < price:
                    action = "Sell"
                    name = i
                    id = holdings[i][bn-1][1]
                    try:
                        url = "https://scportm.pythonanywhere.com/mail"
                        params = {
                            "a": action,
                            "n": name,
                            "i": id
                        }
                        response = requests.get(url, params=params)
                        logger.info(response.json())  
                    except Exception as e:
                        logger.info(f"Error 134 {e}")
                        break
                elif ppoint - bdiff > price:
                    action = "Buy"
                    name = i
                    id = holdings[i][bn-1][1]
                    try:
                        url = "https://scportm.pythonanywhere.com/mail"
                        params = {
                            "a": action,
                            "n": name,
                            "i": id
                        }
                        response = requests.get(url, params=params)
                        logger.info(response.json())  
                    except Exception as e:
                        logger.info(f"Error 134 {e}")
                        break
                        
            
        except Exception as e:
            logger.info(f"315err {e}")
            
    return "done"

@app.route("/background", methods=["GET","POST"])
def background():
    print("exec2")
    global tags
    global index
    global data
    for i in tags.keys():
        sleep(10)
        url = f"https://www.screener.in/company/{i}/"
        while True:
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()  # catches 4xx / 5xx
        
                soup = BeautifulSoup(response.text, 'html.parser')
        
                # success → break loop
                break
        
            except requests.exceptions.HTTPError as e:
                status = e.response.status_code
        
                if status == 404:
                    logger.info(f"404 Not Found → {url}")
                    return "error"   # do NOT retry
        
                logger.info(f"HTTP {status}. Retrying in 60s...")
                time.sleep(60)
        
            except requests.exceptions.RequestException as e:
                # timeout, DNS, connection reset, etc.
                logger.info(f"Network error: {e}. Retrying in 60s...")
                time.sleep(60)

        try:
            soup = BeautifulSoup(response.text, 'html.parser')
            div = soup.find('ul', {'id': 'top-ratios'})
            nums = div.find_all('span', {'class': 'number'})
        except Exception as e:
            logger.info(f"338err {e}")
        try:
            cap = int("".join(str(nums[0]).split("</")[0][21:].split(",")))
            high = float("".join(str(nums[2]).split("</")[0][21:].split(",")))
            low = float("".join(str(nums[3]).split("</")[0][21:].split(",")))
            pe = float("".join(str(nums[4]).split("</")[0][21:].split(",")))
            book = float("".join(str(nums[5]).split("</")[0][21:].split(","))) if str(nums[5]).split("</")[0][21:]!="" else 0
            roce = float("".join(str(nums[7]).split("</")[0][21:].split(",")))
            roe = float("".join(str(nums[8]).split("</")[0][21:].split(",")))
        except Exception as e:
            logger.into(f"348err {e}")

        try:
            data[index[i]]["market_cap"] = cap
            data[index[i]]["high"] = high
            data[index[i]]["low"] = low
            data[index[i]]["pe"] = pe
            data[index[i]]["book"] = book
            data[index[i]]["roce"] = roce
            data[index[i]]["roe"] = roe
        except Exception as e:
            data[index[i]]["market_cap"] = -1
            data[index[i]]["high"] = -1
            data[index[i]]["low"] = -1
            data[index[i]]["pe"] = -1
            data[index[i]]["book"] = -1
            data[index[i]]["roce"] = -1
            data[index[i]]["roe"] = -1
            logger.info(f"359err {e}")

        url = f"https://www.screener.in/api/company/{tags[i]}/peers"
        while True:
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()  # catches 4xx / 5xx
        
                soup = BeautifulSoup(response.text, 'html.parser')
        
                # success → break loop
                break
        
            except requests.exceptions.HTTPError as e:
                status = e.response.status_code
        
                if status == 404:
                    logger.info(f"404 Not Found → {url}")
                    return "error"   # do NOT retry
        
                logger.info(f"HTTP {status}. Retrying in 60s...")
                time.sleep(60)
        
            except requests.exceptions.RequestException as e:
                # timeout, DNS, connection reset, etc.
                logger.info(f"Network error: {e}. Retrying in 60s...")
                time.sleep(60)

        try:
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
        except Exception as e:
            data[index[i]]["np_qtr"] = -1
            data[index[i]]["qtr_profit_var"] = -1
            data[index[i]]["sales_qtr"] = -1
            data[index[i]]["qtr_sales_var"] = -1
            logger.info(f"402err {e}")

    return "done"

@app.route("/mk", methods=["GET","POST"])
def mk():
    query = request.args.get('q')
    tk = request.args.get('tk')
    global tags
    global index
    global data
    url = f"https://www.screener.in/company/{query}"
    d = {}
    d["name"] = query
    while True:
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()  # catches 4xx / 5xx
    
            soup = BeautifulSoup(response.text, 'html.parser')
    
            # success → break loop
            break
    
        except requests.exceptions.HTTPError as e:
            status = e.response.status_code
    
            if status == 404:
                logger.info(f"404 Not Found → {url}")
                return "err"  # do NOT retry
    
            logger.info(f"HTTP {status}. Retrying in 60s...")
            time.sleep(60)
    
        except requests.exceptions.RequestException as e:
            # timeout, DNS, connection reset, etc.
            logger.info(f"Network error: {e}. Retrying in 60s...")
            time.sleep(60)

    try:
        
        global key
        url = "https://scportm.pythonanywhere.com/add_monitor"
        params = {
            "name": query,
            "id": tk,
            "key": key
        }
        api_add = requests.get(url, params=params)
        if api_add.json() == []:
            return "err"
        soup = BeautifulSoup(response.text, 'html.parser')
        div = soup.find('ul', {'id': 'top-ratios'})
        logger.info(div)
        nums = div.find_all('span', {'class': 'number'})
    except Exception as e:
        logger.info(f"446err {e}")

    try:
        cap = int("".join(str(nums[0]).split("</")[0][21:].split(",")))
        d["market_cap"] = cap
    except Exception as e:
        d["market_cap"] = -1
        logger.info(f"453err {e}")
    try:
        price = float("".join(str(nums[1]).split("</")[0][21:].split(",")))
        d["price"] = price
    except Exception as e:
        logger.info(f"458err {e}")
    try:
        high = float("".join(str(nums[2]).split("</")[0][21:].split(",")))
        d["high"] = high
    except Exception as e:
        logger.info(f"463err {e}")
    try:
        low = float("".join(str(nums[3]).split("</")[0][21:].split(",")))
        d["low"] = low
    except Exception as e:
        logger.info(f"468err {e}")
    try:
        pe = float("".join(str(nums[4]).split("</")[0][21:].split(",")))
        d["pe"] = pe
    except Exception as e:
        logger.info(f"473err {e}")
    try:
        book = float("".join(str(nums[5]).split("</")[0][21:].split(","))) if str(nums[5]).split("</")[0][21:]!="" else 0
        d["book"] = book 
    except Exception as e:
        logger.info(f"478err {e}")
    try:
        roce = float("".join(str(nums[7]).split("</")[0][21:].split(",")))
        d["roce"] = roce
    except Exception as e:
        logger.info(f"483err {e}")
    try:
        roe = float("".join(str(nums[8]).split("</")[0][21:].split(",")))
        d["roe"] = roe
    except Exception as e:
        logger.info(f"488err {e}")
    try:
        div1 = soup.find('span', {'class': 'font-size-12 down margin-left-4'})
        div2 = soup.find('span', {'class': 'font-size-12 up margin-left-4'})
        dev = str(div1 if div1 is not None else div2)[90:].split("</")[0].strip()[:-1]
        d["deviation"] = float(dev)
    except Exception as e:
        logger.info(f"446err {e}")
    url = f"https://www.screener.in/api/company/{tk}/peers"
    while True:
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()  # catches 4xx / 5xx
    
            soup = BeautifulSoup(response.text, 'html.parser')
    
            # success → break loop
            break
    
        except requests.exceptions.HTTPError as e:
            status = e.response.status_code
    
            if status == 404:
                logger.info(f"404 Not Found → {url}")
                return "error"   # do NOT retry
    
            logger.info(f"HTTP {status}. Retrying in 60s...")
            time.sleep(60)
    
        except requests.exceptions.RequestException as e:
            # timeout, DNS, connection reset, etc.
            logger.info(f"Network error: {e}. Retrying in 60s...")
            time.sleep(60)
    try:
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
    except Exception as e:
        logger.info(f"536err {e}")

    try:
        data.append(d)
        
        tags[query] = tk
        index[query] = len(data) - 1
    except Exception as e:
        logger.into(f"446err {e}")
    return "done"
    
@app.route("/rm", methods=["GET","POST"])
def rm():
    try:
        query = request.args.get('q')
        global key
        url = "https://scportm.pythonanywhere.com/delete_monitor"
        params = {
            "name": query,
            "key": key
        }
        response = requests.get(url, params=params)
        if response.json() == []:
            return "err"
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
    except Exception as e:
        logger.info(f"Error 405 {e}")
        return "error"
    
@app.route("/ckbuy", methods=["GET", "POST"])
def ck1():
    try:
        query = request.args.get('q')
        global k1
        if query == "NC":
            return str(k1)
        k1 = float(query)
        return f"done : {k1}"
    except Exception as e:
        logger.info(f"Error 418 {e}")
        return "error"

@app.route("/cksell", methods=["GET", "POST"])
def ck2():
    try:
        query = request.args.get('q')
        global k2
        if query == "NC":
            return str(k2)
        k2 = float(query)
        return f"done : {k2}"
    except Exception as e:
        logger.info(f"Error 418 {e}")
        return "error"

@app.route("/buy", methods=["GET","POST"])
def buy():
    try:
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

        global key
        url = "https://scportm.pythonanywhere.com/buy"
        params = {
            "q": query,
            "p": data[index[query]]['price'] if price=="-1" else float(price),
            "n": int(num),
            "d": date,
            "key": key
        }
        res = requests.get(url, params=params)
        dat = res.json()
        if dat == []:
            return "err"
        id = dat['id']
        holding = defaultdict(list)
        rows = requests.get(f"https://scportm.pythonanywhere.com/holding?key={key}").json()
        for row in rows:
            holding[row[1]].append([row[3], row[0]])
        holdings = holding
        
        for i in data:
            if i['name'] == query:
                i['num'] = i.get('num', 0) + 1
        return redirect("/portfolio")
    except Exception as e:
        logger.info(f"Error 450 {e}")
        return "error"

@app.route('/sell', methods=["GET","POST"])
def sell():
    try:
        query = request.args.get('q')
        id = request.args.get('n')
        price = request.args.get('p')
        date = request.args.get('d')
        day = datetime.now() - timedelta(days=int(date)) if date!="0" else datetime.now()
        global holdings
        if int(id) not in [j[1] for j in holdings[query]]:
            return "No such holding exists"
        global key
        url = "https://scportm.pythonanywhere.com/sell"
        params = {
            "q": query,
            "p": data[index[query]]['price'] if price=="-1" else float(price),
            "n": id,
            "d": date,
            "key": key
        }
        res = requests.get(url, params=params)
        if res.json() == []:
            return "err"
        holdings[query] = [j for j in holdings[query] if j[1] != int(id)]
        for i in data:
            if i['name'] == query:
                i['num'] = i.get('num', 0) - 1
        return redirect("/portfolio")
    except Exception as e:
        logger.info(f"Error 503 {e}")
        return "error"

@app.route('/portfolio', methods=["GET","POST"])
def port():
    return render_template("port.html")

@app.route('/holding', methods=["GET","POST"])
def holding():
    try:
        global key
        url = f"https://scportm.pythonanywhere.com/holding?key={key}"
        res = requests.get(url)
        rows = res.json()
        for i in rows:
            if i[1] in alias.keys():
                i.append(alias[i[1]])
        return jsonify(rows)
    except Exception as e:
        logger.info(f"Error 532 {e}")
        return "error"

@app.route('/history', methods=["GET","POST"])
def hist():
    return render_template("history.html")

@app.route('/hist_data', methods=["GET","POST"])
def history():
    try:
        global key
        url = f"https://scportm.pythonanywhere.com/history?key={key}"
        res = requests.get(url)
        rows = res.json()
        for row in rows:
            if row[0] in alias.keys():
                row.append(alias[row[0]])
        return jsonify(rows)
    except Exception as e:
        logger.info(f"Error 557 {e}")
        return "error"

@app.route('/hide', methods=["GET","POST"])
def hide():
    try:
        query = request.args.get('q')
        url = "https://scportm.pythonanywhere.com/hide"
        params = {
            "q": query,
        }
        res = requests.get(url, params=params)
        return redirect("/history")
    except Exception as e:
        logger.info("Error 574")
        return "error"

@app.route('/salias', methods=["GET","POST"])
def salias():
    try:
        query = request.args.get('q')
        alias = request.args.get('a')
        global data
        global index
        name = query
        data[index[name]]['alias'] = alias
        url = "https://scportm.pythonanywhere.com/alias"
        params = {
            "q": query,
            "a": alias,
        }
        res = requests.get(url, params=params)
        return "done"
    except Exception as e:
        logger.info(f"Error 834 {e}")
        return "error"

@app.route('/manual', methods=['GET','POST'])
def manual():
    text = """\
    Change buy alert variable:
      /ckbuy?q=VALUE        (20% -> VALUE = 0.2)
    
    Change sell alert variable:
      /cksell?q=VALUE       (20% -> VALUE = 0.2)
    
    Set alias for monitor:
      /salias?q=NAME&a=ALIAS
      (NAME must be the original ticker input)
    
    Change Auth Key:
      /sk?q=KEY
      (Restricts portfolio, history, buy/sell/remove actions)

    USE AFTER ALL APP DOWNTIME:
      /reset
      (Resets lost holding data with auth, needs /sk set prior)
    """
    return Response(text, mimetype="text/plain")


scheduler = BackgroundScheduler()
scheduler.add_job(func=update, trigger="interval", minutes=45)
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













































































