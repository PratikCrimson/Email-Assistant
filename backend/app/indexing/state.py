
INDEX_STATE = {
    "running" : False,
    "total" : 0,
    "processed" : 0,
    "started_at" : None,
    "finished_at" : None,
}

from app.db.sqlite import get_conn

def get_last_synced_at():
    conn = get_conn()
    cur = conn.cursor()
    row = cur.execute(
    "SELECT last_synced_at FROM sync_state WHERE id = 1"
   ).fetchone()
    conn.close()
    return row["last_synced_at"] if row and row["last_synced_at"] else None

def update_last_synced_at(ts_iso : str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE sync_state SET last_synced_at = ? WHERE id = 1", (ts_iso,))
    conn.commit()
    conn.close()
