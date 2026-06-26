import sqlite3
from datetime import date, datetime
from typing import Optional, List, Dict, Any


class Database:
    def __init__(self, db_path: str = "dacha_bot.db"):
        self.db_path = db_path
        self._init_db()

    def _get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dachas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                price INTEGER NOT NULL,
                location TEXT,
                photo_id TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bookings (
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
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (dacha_id) REFERENCES dachas(id)
            )
        """)

        conn.commit()
        conn.close()

    # ============================================================
    # DACHA METHODS
    # ============================================================
    def add_dacha(self, name: str, description: str, price: int,
                  location: str, photo_id: Optional[str] = None) -> int:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO dachas (name, description, price, location, photo_id) VALUES (?, ?, ?, ?, ?)",
            (name, description, price, location, photo_id)
        )
        dacha_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return dacha_id

    def get_all_dachas(self) -> List[Dict]:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM dachas WHERE is_active = 1 ORDER BY id")
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_dacha(self, dacha_id: int) -> Optional[Dict]:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM dachas WHERE id = ?", (dacha_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def delete_dacha(self, dacha_id: int):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("UPDATE dachas SET is_active = 0 WHERE id = ?", (dacha_id,))
        conn.commit()
        conn.close()

    def update_dacha(self, dacha_id: int, **kwargs):
        conn = self._get_conn()
        cursor = conn.cursor()
        fields = ", ".join(f"{k} = ?" for k in kwargs)
        values = list(kwargs.values()) + [dacha_id]
        cursor.execute(f"UPDATE dachas SET {fields} WHERE id = ?", values)
        conn.commit()
        conn.close()

    # ============================================================
    # BOOKING METHODS
    # ============================================================
    def create_booking(self, user_id: int, dacha_id: int, start_date: date,
                       end_date: date, name: str, phone: str, total_price: int,
                       advance: int, receipt_photo_id: str, status: str = "pending") -> int:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO bookings 
               (user_id, dacha_id, start_date, end_date, name, phone, 
                total_price, advance, receipt_photo_id, status) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (user_id, dacha_id, str(start_date), str(end_date),
             name, phone, total_price, advance, receipt_photo_id, status)
        )
        booking_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return booking_id

    def get_booking(self, booking_id: int) -> Optional[Dict]:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT b.*, d.name as dacha_name 
            FROM bookings b 
            JOIN dachas d ON b.dacha_id = d.id 
            WHERE b.id = ?
        """, (booking_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def get_user_bookings(self, user_id: int) -> List[Dict]:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT b.*, d.name as dacha_name 
            FROM bookings b 
            JOIN dachas d ON b.dacha_id = d.id 
            WHERE b.user_id = ?
            ORDER BY b.created_at DESC
        """, (user_id,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_all_bookings(self) -> List[Dict]:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT b.*, d.name as dacha_name 
            FROM bookings b 
            JOIN dachas d ON b.dacha_id = d.id 
            ORDER BY b.created_at DESC
            LIMIT 50
        """)
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def update_booking_status(self, booking_id: int, status: str):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("UPDATE bookings SET status = ? WHERE id = ?", (status, booking_id))
        conn.commit()
        conn.close()

    def is_date_booked(self, dacha_id: int, check_date: date) -> bool:
        """Check if a specific date is booked for a dacha"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) as cnt FROM bookings 
            WHERE dacha_id = ? 
            AND status IN ('pending', 'confirmed')
            AND start_date <= ? 
            AND end_date > ?
        """, (dacha_id, str(check_date), str(check_date)))
        row = cursor.fetchone()
        conn.close()
        return row['cnt'] > 0

    def get_booked_dates(self, dacha_id: int, year: int, month: int) -> List[int]:
        """Get list of booked day numbers for a given month"""
        import calendar as cal
        _, days_in_month = cal.monthrange(year, month)

        booked = []
        for day in range(1, days_in_month + 1):
            check_date = date(year, month, day)
            if self.is_date_booked(dacha_id, check_date):
                booked.append(day)
        return booked

    # ============================================================
    # STATS
    # ============================================================
    def get_stats(self) -> Dict:
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) as cnt FROM dachas WHERE is_active = 1")
        dachas = cursor.fetchone()['cnt']

        cursor.execute("SELECT COUNT(*) as cnt FROM bookings")
        total = cursor.fetchone()['cnt']

        cursor.execute("SELECT COUNT(*) as cnt FROM bookings WHERE status = 'confirmed'")
        confirmed = cursor.fetchone()['cnt']

        cursor.execute("SELECT COUNT(*) as cnt FROM bookings WHERE status = 'pending'")
        pending = cursor.fetchone()['cnt']

        cursor.execute("SELECT COUNT(*) as cnt FROM bookings WHERE status = 'rejected'")
        rejected = cursor.fetchone()['cnt']

        cursor.execute("SELECT COALESCE(SUM(advance), 0) as total FROM bookings WHERE status = 'confirmed'")
        revenue = cursor.fetchone()['total']

        conn.close()
        return {
            'dachas': dachas,
            'total_bookings': total,
            'confirmed': confirmed,
            'pending': pending,
            'rejected': rejected,
            'total_revenue': revenue
        }
