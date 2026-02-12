import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "emails.db"

def get_conn():                 
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS emails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email_id TEXT UNIQUE,
            thread_id TEXT,
            subject TEXT,
            sender TEXT,
            date TEXT,
            cleaned_body TEXT,
            indexed_at TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sync_state (
            id INTEGER PRIMARY KEY ,
            last_synced_at TEXT,
            CHECK (id = 1)
        )
    """)
    cur.execute("INSERT OR IGNORE INTO sync_state (id, last_synced_at) VALUES (1, NULL)")
    conn.commit()
    conn.close()