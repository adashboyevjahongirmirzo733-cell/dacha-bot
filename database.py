import sqlite3
from datetime import date
from typing import Optional, List, Dict


class Database:
    def __init__(self, db_path="dacha.db"):
        self.db_path = db_path
        self._init()

    def _conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init(self):
        conn = self._conn()
        c = conn.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS dachas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price INTEGER NOT NULL,
            location TEXT,
            photo_id TEXT,
            active INTEGER DEFAULT 1
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            dacha_id INTEGER NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            total_price INTEGER NOT NULL,
            advance INTEGER NOT NULL,
            receipt_photo_id TEXT,
            status TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )""")
        conn.commit()
        conn.close()

    def add_dacha(self, name, description, price, location, photo_id=None):
        conn = self._conn()
        c = conn.cursor()
        c.execute("INSERT INTO dachas (name,description,price,location,photo_id) VALUES (?,?,?,?,?)",
                  (name, description, price, location, photo_id))
        id = c.lastrowid
        conn.commit()
        conn.close()
        return id

    def get_dachas(self):
        conn = self._conn()
        rows = conn.execute("SELECT * FROM dachas WHERE active=1 ORDER BY id").fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_dacha(self, id):
        conn = self._conn()
        row = conn.execute("SELECT * FROM dachas WHERE id=?", (id,)).fetchone()
        conn.close()
        return dict(row) if row else None

    def delete_dacha(self, id):
        conn = self._conn()
        conn.execute("UPDATE dachas SET active=0 WHERE id=?", (id,))
        conn.commit()
        conn.close()

    def is_booked(self, dacha_id, check_date):
        conn = self._conn()
        row = conn.execute("""SELECT COUNT(*) as n FROM bookings
            WHERE dacha_id=? AND status IN ('pending','confirmed')
            AND start_date<=? AND end_date>?""",
            (dacha_id, str(check_date), str(check_date))).fetchone()
        conn.close()
        return row['n'] > 0

    def booked_days(self, dacha_id, year, month):
        import calendar
        _, days = calendar.monthrange(year, month)
        result = []
        for d in range(1, days+1):
            if self.is_booked(dacha_id, date(year, month, d)):
                result.append(d)
        return result

    def create_booking(self, user_id, dacha_id, start_date, end_date,
                       name, phone, total_price, advance, receipt_photo_id):
        conn = self._conn()
        c = conn.cursor()
        c.execute("""INSERT INTO bookings
            (user_id,dacha_id,start_date,end_date,name,phone,total_price,advance,receipt_photo_id)
            VALUES (?,?,?,?,?,?,?,?,?)""",
            (user_id, dacha_id, str(start_date), str(end_date),
             name, phone, total_price, advance, receipt_photo_id))
        id = c.lastrowid
        conn.commit()
        conn.close()
        return id

    def get_booking(self, id):
        conn = self._conn()
        row = conn.execute("""SELECT b.*, d.name as dacha_name FROM bookings b
            JOIN dachas d ON b.dacha_id=d.id WHERE b.id=?""", (id,)).fetchone()
        conn.close()
        return dict(row) if row else None

    def get_user_bookings(self, user_id):
        conn = self._conn()
        rows = conn.execute("""SELECT b.*, d.name as dacha_name FROM bookings b
            JOIN dachas d ON b.dacha_id=d.id WHERE b.user_id=?
            ORDER BY b.created_at DESC""", (user_id,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_all_bookings(self):
        conn = self._conn()
        rows = conn.execute("""SELECT b.*, d.name as dacha_name FROM bookings b
            JOIN dachas d ON b.dacha_id=d.id
            ORDER BY b.created_at DESC LIMIT 50""").fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def update_status(self, id, status):
        conn = self._conn()
        conn.execute("UPDATE bookings SET status=? WHERE id=?", (status, id))
        conn.commit()
        conn.close()

    def stats(self):
        conn = self._conn()
        c = conn.cursor()
        dachas = c.execute("SELECT COUNT(*) as n FROM dachas WHERE active=1").fetchone()['n']
        total = c.execute("SELECT COUNT(*) as n FROM bookings").fetchone()['n']
        confirmed = c.execute("SELECT COUNT(*) as n FROM bookings WHERE status='confirmed'").fetchone()['n']
        pending = c.execute("SELECT COUNT(*) as n FROM bookings WHERE status='pending'").fetchone()['n']
        rejected = c.execute("SELECT COUNT(*) as n FROM bookings WHERE status='rejected'").fetchone()['n']
        revenue = c.execute("SELECT COALESCE(SUM(advance),0) as n FROM bookings WHERE status='confirmed'").fetchone()['n']
        conn.close()
        return dict(dachas=dachas, total=total, confirmed=confirmed,
                    pending=pending, rejected=rejected, revenue=revenue)
