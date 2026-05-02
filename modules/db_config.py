import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fullname TEXT,
        email TEXT UNIQUE,
        password TEXT,
        role TEXT DEFAULT 'user',
        preferred_product INTEGER DEFAULT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_name TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS markets(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        market_name TEXT,
        location TEXT,
        distance REAL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS daily_prices(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER,
        market_id INTEGER,
        price REAL,
        price_date TEXT
    )
    """)

    conn.commit()
    conn.close()