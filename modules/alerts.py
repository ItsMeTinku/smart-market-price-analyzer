from modules.db_config import get_connection


def generate_alerts(product_filter=None):
    conn = get_connection()
    cursor = conn.cursor()

    if product_filter:
        cursor.execute("SELECT MAX(price) as max_price, MIN(price) as min_price FROM daily_prices WHERE product_id=?", (product_filter,))
    else:
        cursor.execute("SELECT MAX(price) as max_price, MIN(price) as min_price FROM daily_prices")

    data = cursor.fetchone()
    conn.close()

    if data["max_price"] is None:
        return "No market price data inserted yet."

    difference = data["max_price"] - data["min_price"]

    if difference >= 10:
        return "High Market Opportunity: Large price difference detected between markets."
    elif data["max_price"] > 25:
        return "Price Alert: Product prices are rising in selected markets."
    else:
        return "Market Stable: No unusual price fluctuation detected."