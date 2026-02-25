import threading
from datetime import datetime
from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse, JSONResponse
from app.auth.google_oauth import get_google_oauth_flow, get_user_email
from app.email.gmail_client import fetch_latest_emails, fetch_email_detail, get_email_service
from app.email.parser import extract_email_feilds
from app.indexing.background import run_background_indexing
from app.indexing.state import INDEX_STATE
from app.ai.embeddings import embed_text
from app.db.postgress import SessionLocal
from sqlalchemy import text
from app.auth.deps import get_current_user
from app.rag.service import rag_answer

router = APIRouter()


@router.get("/emails/test")
def fetch_emails_test_and_trigger_bg():
    from app.db.models import UserToken
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request

    db = SessionLocal()
    token_row = db.query(UserToken).first()
    db.close()

    if not token_row:
        return {"error": "no users logged in yet"}

    credentials = Credentials(
        token=token_row.access_token,
        refresh_token=token_row.refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=None,
        client_secret=None,
        scopes=["https://www.googleapis.com/auth/gmail.readonly"],
    )

    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
        db = SessionLocal()
        token_row = db.query(UserToken).filter(UserToken.user_email == token_row.user_email).first()
        token_row.access_token = credentials.token
        token_row.expiry = credentials.expiry
        db.commit()
        db.close()

    service = get_email_service(credentials)

    messages = fetch_latest_emails(service, max_results=10)
    emails = []

    for msg in messages:
        detail = fetch_email_detail(service, msg["id"])
        parsed = extract_email_feilds(detail)
        emails.append(parsed)

    if not INDEX_STATE["running"]:
        threading.Thread(
            target=run_background_indexing,
            args=(credentials, token_row.user_email, 50),
            daemon=True
        ).start()

    return {"preview": emails, "background_indexing": "started"}


@router.post("/index/start")
def start_background_indexing():
    from app.db.models import UserToken
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request

    db = SessionLocal()
    token_row = db.query(UserToken).first()
    db.close()

    if not token_row:
        return {"error": "no users logged in yet"}

    credentials = Credentials(
        token=token_row.access_token,
        refresh_token=token_row.refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=None,
        client_secret=None,
        scopes=["https://www.googleapis.com/auth/gmail.readonly"],
    )

    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
        db = SessionLocal()
        token_row = db.query(UserToken).filter(UserToken.user_email == token_row.user_email).first()
        token_row.access_token = credentials.token
        token_row.expiry = credentials.expiry
        db.commit()
        db.close()

    threading.Thread(
        target=run_background_indexing,
        args=(credentials, token_row.user_email, 50),
        daemon=True,
    ).start()

    return {"status": "started", "message": "Background indexing started"}


@router.get("/search")
def semantic_search(
    q: str,
    category: str | None = None,
    limit: int = 5,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    from_sender: str | None = None,
    user=Depends(get_current_user),
):
    db = SessionLocal()
    try:
        query_embedding = embed_text(q)

        sql = text("""
        SELECT email_id, subject, sender, date, category, cleaned_body,
               embedding <-> CAST(:query_embedding AS vector) AS distance
        FROM emails
        WHERE user_email = :user_email
          AND (:category IS NULL OR category = :category)
          AND (:start_date IS NULL OR date >= :start_date)
          AND (:end_date IS NULL OR date <= :end_date)
          AND (:from_sender IS NULL OR sender ILIKE :from_sender)
        ORDER BY embedding <-> CAST(:query_embedding AS vector)
        LIMIT :limit
        """)

        from_sender_filter = f"%{from_sender}%" if from_sender else None

        results = db.execute(
            sql,
            {
                "query_embedding": query_embedding,
                "category": category,
                "limit": limit,
                "user_email": user.email,
                "start_date": start_date,
                "end_date": end_date,
                "from_sender": from_sender_filter,
            }
        ).fetchall()

        return {
            "query": q,
            "category": category,
            "results": [
                {
                    "email_id": r.email_id,
                    "subject": r.subject,
                    "sender": r.sender,
                    "date": r.date,
                    "category": r.category,
                    "preview": (r.cleaned_body or "")[:300],
                    "distance": float(r.distance),
                }
                for r in results
            ],
        }
    finally:
        db.close()


@router.post("/ask")
def ask_rag(payload: dict, user=Depends(get_current_user)):
    """
    Payload shape:
    {
        "query": "...",                      # required
        "start_date": "2024-01-01T00:00:00", # optional ISO-8601
        "end_date": "2024-12-31T23:59:59",   # optional ISO-8601
        "from_sender": "foo@bar.com",        # optional
        "category": "hr"                     # optional
    }
    """

    def _parse_iso_datetime(value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value)
        except Exception:
            return None

    start_date = _parse_iso_datetime(payload.get("start_date"))
    end_date = _parse_iso_datetime(payload.get("end_date"))

    answer = rag_answer(
        user_email=user.email,
        query=payload["query"],
        start_date=start_date,
        end_date=end_date,
        from_sender=payload.get("from_sender"),
        category=payload.get("category"),
    )
    return {"answer": answer}


@router.get("/login")
def login():
    flow = get_google_oauth_flow()
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    return RedirectResponse(auth_url)


@router.get("/google/callback")
def google_callback(request: Request):
    flow = get_google_oauth_flow()
    flow.fetch_token(authorization_response=str(request.url))

    credentials = flow.credentials
    email = get_user_email(credentials)

    from app.db.models import UserToken

    db = SessionLocal()
    try:
        token_row = db.query(UserToken).filter(UserToken.user_email == email).first()
        if token_row:
            token_row.access_token = credentials.token
            token_row.refresh_token = credentials.refresh_token
            token_row.expiry = credentials.expiry
        else:
            db.add(UserToken(
                user_email=email,
                access_token=credentials.token,
                refresh_token=credentials.refresh_token,
                expiry=credentials.expiry,
            ))
        db.commit()
    finally:
        db.close()

    return JSONResponse({"message": "Logged in successfully", "email": email})


@router.get("/index/status")
def get_index_status():
    return INDEX_STATE