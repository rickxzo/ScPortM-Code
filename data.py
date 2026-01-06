from flask import Flask, jsonify, request
from datetime import datetime, timedelta

app = Flask(__name__)

sk = ""


import mysql.connector

def connect_db():
    conn = mysql.connector.connect(
        host="SCPortM.mysql.pythonanywhere-services.com",
        user="SCPortM",
        password="",
        database="SCPortM$default"
    )
    return conn

@app.route('/', methods=['POST', 'GET'])
def index():
    return "Hello vaii"

@app.route('/monitors', methods=['POST', 'GET'])
def monitors():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Monitor")
    monitors = cursor.fetchall()
    conn.close()
    return jsonify(monitors)


@app.route('/add_monitor', methods=['POST', 'GET'])
def add_monitor():
    key = request.args.get('key')
    if key!=sk:
        return []
    name = request.args.get('name')
    id = request.args.get('id')
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO Monitor (name, id) VALUES (%s, %s)", (name, id))
    conn.commit()
    conn.close()
    return jsonify({"status": "Monitor added successfully"})

@app.route('/delete_monitor', methods=['POST', 'GET'])
def delete_monitor():
    key = request.args.get('key')
    if key!=sk:
        return []
    name = request.args.get('name')
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Monitor WHERE name = %s", (name,))
    conn.commit()
    conn.close()
    return jsonify({"status": "Monitor deleted successfully"})

@app.route('/holding', methods=['GET', 'POST'])
def holding():
    key = request.args.get('key')
    if key!=sk:
        return []
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Buy WHERE sold = 0 ORDER BY name ASC")
    rows = cursor.fetchall()
    conn.close()
    return jsonify(rows)

@app.route('/buy', methods=['GET','POST'])
def buy():
    key = request.args.get('key')
    if key!=sk:
        return []
    query = request.args.get('q')
    num = request.args.get('n')
    price = request.args.get('p')
    date = request.args.get('d')
    day = datetime.now() - timedelta(days=int(date)) if date!="0" else datetime.now()
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(
            '''
            INSERT INTO Buy (name, price, amt, date) VALUES (%s,%s,%s,%s)
            ''', (query, price, int(num), day.strftime("%Y-%m-%d %H:%M:%S"))
        )
    conn.commit()
    id = cursor.lastrowid
    conn.close()
    return jsonify({"id": id})

@app.route('/sell', methods=['GET', 'POST'])
def sell():
    key = request.args.get('key')
    if key!=sk:
        return []
    query = request.args.get('q')
    id = request.args.get('n')
    price = request.args.get('p')
    date = request.args.get('d')
    day = datetime.now() - timedelta(days=int(date)) if date!="0" else datetime.now()
    conn = connect_db()
    c = conn.cursor()
    c.execute(
        "UPDATE Buy SET sold = 1 WHERE lid = %s", (int(id),)
    )
    conn.commit()
    c.execute(
        "SELECT date, price, amt FROM Buy WHERE lid = %s", (int(id),)
    )
    row = c.fetchone()
    buy_price = float(row[1])
    sell_price = float(price)
    profit = (sell_price - buy_price) * float(row[2])
    print(profit, sell_price, day)
    c.execute(
        '''
        INSERT INTO Sell (lid, profit, sell_price, date) VALUES (%s,%s,%s,%s)
        ''', (int(id), profit, sell_price, day.strftime("%Y-%m-%d %H:%M:%S"))
    )
    conn.commit()
    c.execute(
        "SELECT Sell.date, Buy.date FROM Sell JOIN Buy ON Sell.lid = Buy.lid WHERE Sell.lid = %s", (int(id),)
    )
    row = c.fetchone()
    buy_date_str = row[1]
    sell_date_str = row[0]
    buy_date = buy_date_str
    sell_date = sell_date_str

    print(buy_date, sell_date)
    duration = (sell_date - buy_date).days
    print(duration)
    c.execute(
        "UPDATE Sell SET duration = %s WHERE lid = %s", (duration, int(id))
    )
    conn.commit()
    conn.close()
    return "done"

@app.route('/history',methods=['GET','POST'])
def history():
    key = request.args.get('key')
    if key!=sk:
        return []
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(
        '''
        SELECT Buy.name, Buy.date, Buy.price, Buy.amt, Sell.date, Sell.profit, Sell.duration, Sell.sell_price, Sell.sid
        FROM Buy
        LEFT JOIN Sell ON Buy.lid = Sell.lid
        WHERE Sell.hidden IS NULL OR Sell.hidden = 0
        ORDER BY Buy.name ASC
        '''
    )
    rows = cursor.fetchall()
    conn.close()
    return jsonify(rows)

@app.route('/hide', methods=['GET', 'POST'])
def hide():
    query = request.args.get('q')
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(
        '''
        UPDATE Sell SET hidden = 1 WHERE sid = ?''', (int(query),)
    )
    conn.commit()
    conn.close()
    return "done"

@app.route('/alias', methods=['GET', 'POST'])
def alias():
    query = request.args.get('q')
    alias = request.args.get('a')
    conn = connect_db()
    c = conn.cursor()
    c.execute(
        '''
        UPDATE Monitor SET alias = %s WHERE name = %s''', (alias, query)
    )
    conn.commit()
    conn.close()


if __name__ == '__main__':
    app.run(debug=True, port=7000)
