import sqlite3
from datetime import datetime, timedelta

DB_NAME = "bot.db"


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        vip_until TEXT
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS movies (
        code TEXT PRIMARY KEY,
        title TEXT,
        file_id TEXT,
        file_type TEXT
    )""")
    conn.commit()
    conn.close()


def add_user_if_not_exists(user_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO users (user_id, vip_until) VALUES (?, NULL)", (user_id,))
    conn.commit()
    conn.close()


def get_vip_until(user_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT vip_until FROM users WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    conn.close()
    if row and row[0]:
        return datetime.fromisoformat(row[0])
    return None


def is_vip(user_id):
    until = get_vip_until(user_id)
    return bool(until and until > datetime.now())


def set_vip(user_id, days):
    until = get_vip_until(user_id)
    now = datetime.now()
    start = until if (until and until > now) else now
    new_until = start + timedelta(days=days)

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO users (user_id, vip_until) VALUES (?, NULL)", (user_id,))
    cur.execute("UPDATE users SET vip_until=? WHERE user_id=?", (new_until.isoformat(), user_id))
    conn.commit()
    conn.close()
    return new_until


def get_movie_by_code(code):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT title, file_id, file_type FROM movies WHERE code=?", (code,))
    row = cur.fetchone()
    conn.close()
    return row


def search_movies(query):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT code, title FROM movies WHERE title LIKE ?", (f"%{query}%",))
    rows = cur.fetchall()
    conn.close()
    return rows


def add_movie(code, title, file_id, file_type):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        "INSERT OR REPLACE INTO movies (code, title, file_id, file_type) VALUES (?, ?, ?, ?)",
        (code, title, file_id, file_type),
    )
    conn.commit()
    conn.close()
