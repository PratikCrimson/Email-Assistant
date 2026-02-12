import sqlite3
from pathlib import Path

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

def init_db():
    conn = get_conn
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS emails
            id INTEGER
    """
    )