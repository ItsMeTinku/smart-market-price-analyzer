from modules.db_config import get_connection


def add_product(product_name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO products(product_name) VALUES(?)", (product_name,))
    conn.commit()
    conn.close()


def add_market(market_name, location, distance):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO markets(market_name,location,distance) VALUES(?,?,?)",
                   (market_name, location, distance))
    conn.commit()
    conn.close()


def add_daily_price(product_id, market_id, price, price_date):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO daily_prices(product_id,market_id,price,price_date) VALUES(?,?,?,?)",
                   (product_id, market_id, price, price_date))
    conn.commit()
    conn.close()


def get_products():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products")
    data = cursor.fetchall()
    conn.close()
    return data


def get_markets():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM markets")
    data = cursor.fetchall()
    conn.close()
    return data
def delete_product(product_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM products WHERE id=?", (product_id,))
    conn.commit()
    conn.close()


def delete_market(market_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM markets WHERE id=?", (market_id,))
    conn.commit()
    conn.close()


def get_all_price_records():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT daily_prices.id, products.product_name, markets.market_name, daily_prices.price, daily_prices.price_date
    FROM daily_prices
    JOIN products ON daily_prices.product_id = products.id
    JOIN markets ON daily_prices.market_id = markets.id
    ORDER BY daily_prices.id DESC
    """)
    data = cursor.fetchall()
    conn.close()
    return data


def delete_price(price_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM daily_prices WHERE id=?", (price_id,))
    conn.commit()
    conn.close()