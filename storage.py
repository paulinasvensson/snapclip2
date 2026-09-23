"""
Lightweight SQLite-backed storage for snapclip2 URL shortener.
"""
import sqlite3
import string
import random
import time
from contextlib import contextmanager

DB_PATH = "snapclip2.db"


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def get_conn():
    conn = _connect()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS links (
                code TEXT PRIMARY KEY,
                target TEXT NOT NULL,
                created_at REAL NOT NULL,
                is_custom INTEGER NOT NULL DEFAULT 0,
                clicks INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS click_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL,
                ts REAL NOT NULL,
                referrer TEXT
            )
            """
        )


def _random_code(length: int = 6) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(random.choice(alphabet) for _ in range(length))


def code_exists(code: str) -> bool:
    with get_conn() as conn:
        row = conn.execute("SELECT 1 FROM links WHERE code = ?", (code,)).fetchone()
        return row is not None


def create_link(target: str, custom_code: str = None) -> str:
    if custom_code:
        if code_exists(custom_code):
            raise ValueError("Code already taken")
        code = custom_code
        is_custom = 1
    else:
        code = _random_code()
        while code_exists(code):
            code = _random_code()
        is_custom = 0

    with get_conn() as conn:
        conn.execute(
            "INSERT INTO links (code, target, created_at, is_custom, clicks) VALUES (?, ?, ?, ?, 0)",
            (code, target, time.time(), is_custom),
        )
    return code


def get_link(code: str):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM links WHERE code = ?", (code,)).fetchone()
        return dict(row) if row else None


def register_click(code: str, referrer: str = None):
    with get_conn() as conn:
        conn.execute("UPDATE links SET clicks = clicks + 1 WHERE code = ?", (code,))
        conn.execute(
            "INSERT INTO click_events (code, ts, referrer) VALUES (?, ?, ?)",
            (code, time.time(), referrer),
        )


def get_click_history(code: str):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT ts, referrer FROM click_events WHERE code = ? ORDER BY ts DESC",
            (code,),
        ).fetchall()
        return [dict(r) for r in rows]
