import sqlite3
import json
from datetime import datetime
from config import DB_PATH


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price INTEGER NOT NULL,
            description TEXT DEFAULT '',
            category TEXT DEFAULT 'Boshqa',
            photo_url TEXT DEFAULT '',
            in_stock INTEGER DEFAULT 1
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            telegram_id INTEGER PRIMARY KEY,
            full_name TEXT,
            username TEXT,
            phone TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            items_json TEXT NOT NULL,
            total INTEGER NOT NULL,
            status TEXT DEFAULT 'yangi',
            created_at TEXT,
            admin_message_ids TEXT DEFAULT '[]'
        )
    """)
    conn.commit()
    conn.close()


def seed_sample_products():
    """Agar katalog bo'sh bo'lsa, bir nechta namunaviy mahsulot qo'shadi."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) AS c FROM products")
    if cur.fetchone()["c"] == 0:
        samples = [
            ("Non", 4000, "Issiq, yangi pishirilgan non", "Non mahsulotlari", ""),
            ("Sut 1L", 12000, "Tabiiy sigir suti", "Sut mahsulotlari", ""),
            ("Tuxum (10 dona)", 18000, "Fermer tuxumi", "Sut mahsulotlari", ""),
            ("Olma 1kg", 9000, "Qizil olma", "Meva-sabzavot", ""),
        ]
        cur.executemany(
            "INSERT INTO products (name, price, description, category, photo_url) VALUES (?,?,?,?,?)",
            samples,
        )
        conn.commit()
    conn.close()


# ---------- Products ----------

def add_product(name, price, description="", category="Boshqa", photo_url=""):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO products (name, price, description, category, photo_url) VALUES (?,?,?,?,?)",
        (name, price, description, category, photo_url),
    )
    conn.commit()
    pid = cur.lastrowid
    conn.close()
    return pid


def get_products(in_stock_only=True):
    conn = get_conn()
    cur = conn.cursor()
    if in_stock_only:
        cur.execute("SELECT * FROM products WHERE in_stock=1 ORDER BY category, id")
    else:
        cur.execute("SELECT * FROM products ORDER BY category, id")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def get_product(product_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM products WHERE id=?", (product_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def set_product_stock(product_id, in_stock: bool):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE products SET in_stock=? WHERE id=?", (1 if in_stock else 0, product_id))
    conn.commit()
    conn.close()


def delete_product(product_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM products WHERE id=?", (product_id,))
    conn.commit()
    conn.close()


# ---------- Users ----------

def upsert_user(telegram_id, full_name, username, phone=None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT telegram_id FROM users WHERE telegram_id=?", (telegram_id,))
    exists = cur.fetchone()
    if exists:
        if phone:
            cur.execute("UPDATE users SET full_name=?, username=?, phone=? WHERE telegram_id=?",
                        (full_name, username, phone, telegram_id))
        else:
            cur.execute("UPDATE users SET full_name=?, username=? WHERE telegram_id=?",
                        (full_name, username, telegram_id))
    else:
        cur.execute("INSERT INTO users (telegram_id, full_name, username, phone) VALUES (?,?,?,?)",
                    (telegram_id, full_name, username, phone))
    conn.commit()
    conn.close()


def get_user(telegram_id):
    """Bitta foydalanuvchini telegram_id bo'yicha qaytaradi (topilmasa None)."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE telegram_id=?", (telegram_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def get_all_user_ids():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT telegram_id FROM users")
    ids = [r["telegram_id"] for r in cur.fetchall()]
    conn.close()
    return ids


# ---------- Orders ----------

def create_order(user_id, items: list, total: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO orders (user_id, items_json, total, status, created_at) VALUES (?,?,?,?,?)",
        (user_id, json.dumps(items, ensure_ascii=False), total, "yangi", datetime.now().isoformat()),
    )
    conn.commit()
    oid = cur.lastrowid
    conn.close()
    return oid


def get_order(order_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM orders WHERE id=?", (order_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    order = dict(row)
    order["items"] = json.loads(order["items_json"])
    return order


def update_order_status(order_id, status):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE orders SET status=? WHERE id=?", (status, order_id))
    conn.commit()
    conn.close()


def get_user_orders(user_id, limit=10):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM orders WHERE user_id=? ORDER BY id DESC LIMIT ?",
        (user_id, limit),
    )
    rows = [dict(r) for r in cur.fetchall()]
    for r in rows:
        r["items"] = json.loads(r["items_json"])
    conn.close()
    return rows


def get_all_orders(limit=30):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM orders ORDER BY id DESC LIMIT ?", (limit,))
    rows = [dict(r) for r in cur.fetchall()]
    for r in rows:
        r["items"] = json.loads(r["items_json"])
    conn.close()
    return rows
  
