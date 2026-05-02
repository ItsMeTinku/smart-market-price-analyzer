import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
from modules.db_config import get_connection
import os


def generate_price_chart(product_filter=None):
    conn = get_connection()
    cursor = conn.cursor()

    if product_filter:
        cursor.execute("""
            SELECT price_date, AVG(price)
            FROM daily_prices
            WHERE product_id=?
            GROUP BY price_date
            ORDER BY price_date
        """, (product_filter,))
    else:
        cursor.execute("""
            SELECT price_date, AVG(price)
            FROM daily_prices
            GROUP BY price_date
            ORDER BY price_date
        """)

    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return

    dates = [row[0] for row in rows]
    prices = [row[1] for row in rows]

    plt.figure(figsize=(8,4))
    plt.plot(dates, prices, marker='o', linewidth=3)
    plt.title("Smart Price Trend Analysis")
    plt.xlabel("Date")
    plt.ylabel("Average Price")
    plt.grid(True)

    os.makedirs("static/charts", exist_ok=True)
    plt.tight_layout()
    plt.savefig("static/charts/price_chart.png")
    plt.close()


def predict_tomorrow_price(product_filter=None):
    conn = get_connection()
    cursor = conn.cursor()

    if product_filter:
        cursor.execute("SELECT AVG(price) as avg_price FROM daily_prices WHERE product_id=?", (product_filter,))
    else:
        cursor.execute("SELECT AVG(price) as avg_price FROM daily_prices")

    avg_data = cursor.fetchone()
    conn.close()

    if avg_data["avg_price"] is None:
        return 0

    predicted = avg_data["avg_price"] * 1.05
    return round(predicted, 2)


def calculate_profit_estimation(product_filter=None):
    conn = get_connection()
    cursor = conn.cursor()

    if product_filter:
        cursor.execute("SELECT MIN(price) as min_price, MAX(price) as max_price FROM daily_prices WHERE product_id=?", (product_filter,))
    else:
        cursor.execute("SELECT MIN(price) as min_price, MAX(price) as max_price FROM daily_prices")

    data = cursor.fetchone()
    conn.close()

    if data["min_price"] is None or data["max_price"] is None:
        return 0

    profit = (data["max_price"] - data["min_price"]) * 100
    return round(profit, 2)