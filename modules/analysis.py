from modules.db_config import get_connection


def get_all_prices(product_filter=None):
    conn = get_connection()
    cursor = conn.cursor()

    if product_filter:
        cursor.execute("""
        SELECT daily_prices.id,
               products.product_name,
               markets.market_name,
               markets.distance,
               daily_prices.price,
               daily_prices.price_date
        FROM daily_prices
        JOIN products ON daily_prices.product_id = products.id
        JOIN markets ON daily_prices.market_id = markets.id
        WHERE products.id=?
        ORDER BY daily_prices.price_date DESC
        """, (product_filter,))
    else:
        cursor.execute("""
        SELECT daily_prices.id,
               products.product_name,
               markets.market_name,
               markets.distance,
               daily_prices.price,
               daily_prices.price_date
        FROM daily_prices
        JOIN products ON daily_prices.product_id = products.id
        JOIN markets ON daily_prices.market_id = markets.id
        ORDER BY daily_prices.price_date DESC
        """)

    data = cursor.fetchall()
    conn.close()
    return data


def get_best_buy_sell(product_filter=None):
    conn = get_connection()
    cursor = conn.cursor()

    if product_filter:
        cursor.execute("""
        SELECT products.product_name, markets.market_name, markets.distance, daily_prices.price
        FROM daily_prices
        JOIN products ON daily_prices.product_id = products.id
        JOIN markets ON daily_prices.market_id = markets.id
        WHERE products.id=?
        ORDER BY daily_prices.price ASC, markets.distance ASC
        LIMIT 1
        """, (product_filter,))
        best_buy = cursor.fetchone()

        cursor.execute("""
        SELECT products.product_name, markets.market_name, markets.distance, daily_prices.price
        FROM daily_prices
        JOIN products ON daily_prices.product_id = products.id
        JOIN markets ON daily_prices.market_id = markets.id
        WHERE products.id=?
        ORDER BY daily_prices.price DESC
        LIMIT 1
        """, (product_filter,))
        best_sell = cursor.fetchone()
    else:
        cursor.execute("""
        SELECT products.product_name, markets.market_name, markets.distance, daily_prices.price
        FROM daily_prices
        JOIN products ON daily_prices.product_id = products.id
        JOIN markets ON daily_prices.market_id = markets.id
        ORDER BY daily_prices.price ASC, markets.distance ASC
        LIMIT 1
        """)
        best_buy = cursor.fetchone()

        cursor.execute("""
        SELECT products.product_name, markets.market_name, markets.distance, daily_prices.price
        FROM daily_prices
        JOIN products ON daily_prices.product_id = products.id
        JOIN markets ON daily_prices.market_id = markets.id
        ORDER BY daily_prices.price DESC
        LIMIT 1
        """)
        best_sell = cursor.fetchone()

    conn.close()
    return best_buy, best_sell


def calculate_percentage_change(product_filter=None):
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

    avg_price = avg_data["avg_price"]
    yesterday_price = avg_price - 2

    if yesterday_price <= 0:
        return 0

    percent = round(((avg_price - yesterday_price) / yesterday_price) * 100, 2)
    return percent