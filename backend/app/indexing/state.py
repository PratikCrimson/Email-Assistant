TOKEN_STORAGE = {}

INDEX_STATE = {
    "running" : False,
    "total" : 0,
    "processed" : 0,
    "started_at" : None,
    "finished_at" : None,
    "last_synced_at" : None,
}

def get_last_synced_at():
    return INDEX_STATE["last_synced_at"]

def update_last_synced_at(ts_iso : str):
    INDEX_STATE["last_synced_at"] = ts_iso

