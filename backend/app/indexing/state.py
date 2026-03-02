from app.db.models import UserSyncState
from app.db.postgress import SessionLocal


def _serialize_sync_state(row: UserSyncState) -> dict:
    return {
        "running": bool(row.running),
        "total": int(row.total or 0),
        "processed": int(row.processed or 0),
        "started_at": row.started_at.isoformat() if row.started_at else None,
        "finished_at": row.finished_at.isoformat() if row.finished_at else None,
        "last_synced_at": row.last_synced_at.isoformat() if row.last_synced_at else None,
        "has_more": bool(row.has_more),
    }


def get_or_create_user_sync_state(db, user_email: str) -> UserSyncState:
    row = db.query(UserSyncState).filter(UserSyncState.user_email == user_email).first()
    if row:
        return row

    row = UserSyncState(
        user_email=user_email,
        running=False,
        total=0,
        processed=0,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def get_user_index_status(user_email: str) -> dict:
    db = SessionLocal()
    try:
        row = db.query(UserSyncState).filter(UserSyncState.user_email == user_email).first()
        if not row:
            return {
                "running": False,
                "total": 0,
                "processed": 0,
                "started_at": None,
                "finished_at": None,
                "last_synced_at": None,
                "has_more": False,
            }
        return _serialize_sync_state(row)
    finally:
        db.close()


def is_user_indexing_running(user_email: str) -> bool:
    status = get_user_index_status(user_email)
    return bool(status["running"])
