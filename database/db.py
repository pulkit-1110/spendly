import sqlite3
from datetime import date, timedelta
from pathlib import Path

from werkzeug.security import generate_password_hash


DB_PATH = Path(__file__).resolve().parent.parent / "spendly.db"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    schema_users = """
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            name          TEXT NOT NULL,
            email         TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at    TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """
    schema_expenses = """
        CREATE TABLE IF NOT EXISTS expenses (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            amount      REAL    NOT NULL,
            category    TEXT    NOT NULL,
            date        TEXT    NOT NULL,
            description TEXT,
            created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """
    conn = get_db()
    try:
        conn.execute(schema_users)
        conn.execute(schema_expenses)
        conn.commit()
    finally:
        conn.close()


def create_user(name, email, password):
    """Create a new user account. Returns user_id on success, None if email exists."""
    conn = get_db()
    try:
        # Check if email already exists
        existing = conn.execute(
            "SELECT id FROM users WHERE email = ?", (email,)
        ).fetchone()

        if existing:
            return None

        # Create new user
        password_hash = generate_password_hash(password)
        cur = conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (name, email, password_hash)
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get_user_by_email(email):
    conn = get_db()
    try:
        return conn.execute(
            "SELECT id, name, email, password_hash FROM users WHERE email = ?",
            (email,)
        ).fetchone()
    finally:
        conn.close()


def seed_db():
    conn = get_db()
    try:
        existing = conn.execute("SELECT COUNT(*) AS n FROM users").fetchone()
        if existing["n"] > 0:
            return

        cur = conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            ("Demo User", "demo@spendly.com", generate_password_hash("demo123")),
        )
        user_id = cur.lastrowid

        today = date.today()

        def in_month(offset_days):
            d = today + timedelta(days=offset_days)
            if d.month != today.month or d.year != today.year:
                d = today
            return d.isoformat()

        seed_rows = [
            (12.50, "Food",          -1,  "Lunch at cafe"),
            (45.00, "Food",          -5,  "Weekly groceries"),
            (22.75, "Transport",     -2,  "Gas refill"),
            (89.99, "Bills",         -10, "Internet bill"),
            (35.00, "Health",        -7,  "Pharmacy"),
            (18.00, "Entertainment", -3,  "Movie ticket"),
            (64.20, "Shopping",      -4,  "New running shoes"),
            (9.99,  "Other",         -6,  "Cloud storage subscription"),
        ]

        conn.executemany(
            """
            INSERT INTO expenses (user_id, amount, category, date, description)
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                (user_id, amount, category, in_month(offset), description)
                for (amount, category, offset, description) in seed_rows
            ],
        )
        conn.commit()
    finally:
        conn.close()
