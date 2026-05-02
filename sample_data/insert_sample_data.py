import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database.db")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# products
products = [
    ("Onion",),
    ("Potato",),
    ("Tomato",),
    ("Wheat",),
    ("Rice",)
]

# markets
markets = [
    ("Khanna Mandi", "Khanna", 5),
    ("Rajpura Grain Market", "Rajpura", 12),
    ("Sirhind Sabzi Mandi", "Sirhind", 8),
    ("Patiala Wholesale Market", "Patiala", 25)
]

# daily prices
prices = [
    (1,1,20,"2026-04-30"),
    (1,2,25,"2026-04-30"),
    (1,3,23,"2026-04-30"),
    (2,1,15,"2026-04-30"),
    (2,2,18,"2026-04-30"),
    (2,4,17,"2026-04-30"),
    (3,1,28,"2026-04-30"),
    (3,3,30,"2026-04-30"),
    (4,2,32,"2026-04-30"),
    (5,4,35,"2026-04-30")
]

try:
    cursor.executemany("INSERT INTO products(product_name) VALUES(?)", products)
except:
    pass

try:
    cursor.executemany("INSERT INTO markets(market_name,location,distance) VALUES(?,?,?)", markets)
except:
    pass

cursor.executemany("INSERT INTO daily_prices(product_id,market_id,price,price_date) VALUES(?,?,?,?)", prices)

conn.commit()
conn.close()

print("Sample Data Inserted Successfully")