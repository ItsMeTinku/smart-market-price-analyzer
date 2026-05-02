from modules.db_config import get_connection


def save_preferred_product(user_id, product_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET preferred_product=? WHERE id=?", (product_id, user_id))
    conn.commit()
    conn.close()


def get_user_preference(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT preferred_product FROM users WHERE id=?", (user_id,))
    data = cursor.fetchone()
    conn.close()

    if data:
        return data['preferred_product']
    return None