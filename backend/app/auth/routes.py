import os
import threading
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from app.auth.google_oauth import get_google_oauth_flow, get_user_email
from app.email.gmail_client import fetch_latest_emails, fetch_email_detail, get_email_service
from app.email.parser import extract_email_feilds
from app.indexing.background import run_background_indexing
from app.indexing.state import get_user_index_status, is_user_indexing_running
from app.ai.embeddings import embed_text
from app.db.postgress import SessionLocal
from sqlalchemy import text
from app.auth.deps import get_current_user
from app.rag.service import rag_answer_with_context
from app.context.service import (
    create_conversation,
    delete_conversation,
    ensure_conversation,
    get_conversation,
    get_conversation_messages,
    get_last_assistant_email_refs,
    get_recent_messages_for_prompt,
    list_conversations,
    maybe_refresh_summary,
    serialize_conversation,
    save_message,
    serialize_message,
)
from app.core.security import (
    SESSION_COOKIE_NAME,
    SESSION_TTL_SECONDS,
    create_session_token,
)
from app.core.logging import trace_event

router = APIRouter()
VALID_CATEGORIES = {"job", "finance", "hr", "promotions", "security", "other"}


def _normalize_category(value: str | None) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        return None
    normalized = value.strip().lower()
    if not normalized or normalized == "all":
        return None
    if normalized in VALID_CATEGORIES:
        return normalized
    return None


def _parse_iso_datetime(value: str | None, *, end_of_day: bool = False) -> datetime | None:
    if value is None:
        return None
    if not isinstance(value, str):
        return None
    raw = value.strip()
    if not raw:
        return None
    try:
        dt = datetime.fromisoformat(raw)
    except Exception:
        return None

    # For date-only inputs (YYYY-MM-DD), make end_date inclusive.
    if len(raw) == 10 and end_of_day:
        dt = dt.replace(hour=23, minute=59, second=59, microsecond=999999)
    return dt


@router.get("/emails/test")
def fetch_emails_test_and_trigger_bg(user=Depends(get_current_user)):
    credentials = _load_user_credentials(user.email)
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not logged in",
        )

    service = get_email_service(credentials)
    messages = fetch_latest_emails(service, max_results=10)
    emails = []

    for msg in messages:
        detail = fetch_email_detail(service, msg["id"])
        parsed = extract_email_feilds(detail)
        parsed["email_id"] = msg["id"]
        emails.append(parsed)

    if not is_user_indexing_running(user.email):
        threading.Thread(
            target=run_background_indexing,
            args=(credentials, user.email),
            daemon=True
        ).start()

    return {"preview": emails, "background_indexing": "started"}


def _load_user_credentials(user_email: str):
    from app.db.models import UserToken
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request as GoogleRequest

    oauth_flow = get_google_oauth_flow()
    client_id = oauth_flow.client_config.get("client_id")
    client_secret = oauth_flow.client_config.get("client_secret")

    db = SessionLocal()
    try:
        token_row = db.query(UserToken).filter(UserToken.user_email == user_email).first()
        if not token_row:
            return None

        credentials = Credentials(
            token=token_row.access_token,
            refresh_token=token_row.refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_id,
            client_secret=client_secret,
            scopes=["https://www.googleapis.com/auth/gmail.readonly"],
        )

        if credentials.expired and credentials.refresh_token:
            credentials.refresh(GoogleRequest())
            token_row.access_token = credentials.token
            token_row.expiry = credentials.expiry
            if credentials.refresh_token:
                token_row.refresh_token = credentials.refresh_token
            db.commit()

        return credentials
    finally:
        db.close()


@router.post("/index/start")
def start_background_indexing(user=Depends(get_current_user)):
    credentials = _load_user_credentials(user.email)
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not logged in",
        )

    if is_user_indexing_running(user.email):
        return {"status": "running", "message": "Background indexing already in progress"}

    threading.Thread(
        target=run_background_indexing,
        args=(credentials, user.email),
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
        category = _normalize_category(category)
        from_sender = from_sender.strip() if from_sender else None
        query_embedding = embed_text(q)

        sql = text("""
        SELECT email_id, subject, sender, date, category, cleaned_body,
        embedding <=> CAST(:query_embedding AS vector) AS distance
        FROM emails
        WHERE user_email = :user_email
          AND (:category IS NULL OR category = :category)
          AND (:start_date IS NULL OR date >= :start_date)
          AND (:end_date IS NULL OR date <= :end_date)
          AND (:from_sender IS NULL OR sender ILIKE :from_sender)
        ORDER BY embedding <=> CAST(:query_embedding AS vector)
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
        "conversation_id": "uuid-string",    # optional (for follow-ups)
        "start_date": "2024-01-01T00:00:00", # optional ISO-8601
        "end_date": "2024-12-31T23:59:59",   # optional ISO-8601
        "from_sender": "foo@bar.com",        # optional
        "category": "hr"                     # optional
    }
    """

    if not isinstance(payload, dict):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid payload",
        )
    trace_event(
        "http.ask.in",
        route="/auth/ask",
        user_email=user.email,
        payload=payload,
    )
    query = payload.get("query")
    if not isinstance(query, str) or not query.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="query is required",
        )

    start_date = _parse_iso_datetime(payload.get("start_date"), end_of_day=False)
    end_date = _parse_iso_datetime(payload.get("end_date"), end_of_day=True)
    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="start_date cannot be after end_date",
        )
    category = _normalize_category(payload.get("category"))
    from_sender = payload.get("from_sender")
    from_sender = from_sender.strip() if isinstance(from_sender, str) else None
    conversation_id = payload.get("conversation_id")
    if conversation_id is not None and not isinstance(conversation_id, str):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="conversation_id must be a string",
        )
    conversation_id = conversation_id.strip() if isinstance(conversation_id, str) else None
    if conversation_id == "":
        conversation_id = None

    filter_meta = {
        "category": category,
        "from_sender": from_sender,
        "start_date": start_date.isoformat() if start_date else None,
        "end_date": end_date.isoformat() if end_date else None,
    }
    db = SessionLocal()
    conversation = None
    response_conversation_id = None
    try:
        try:
            conversation = ensure_conversation(
                db=db,
                user_email=user.email,
                conversation_id=conversation_id,
            )
            response_conversation_id = conversation.id
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            )

        recent_messages = get_recent_messages_for_prompt(
            db=db,
            conversation_id=conversation.id,
            user_email=user.email,
        )
        prior_email_ids = get_last_assistant_email_refs(
            db=db,
            conversation_id=conversation.id,
            user_email=user.email,
        )
        save_message(
            db=db,
            conversation=conversation,
            user_email=user.email,
            role="user",
            content=query.strip(),
            message_meta={"filters": filter_meta},
        )

        rag_result = rag_answer_with_context(
            user_email=user.email,
            query=query.strip(),
            start_date=start_date,
            end_date=end_date,
            from_sender=from_sender,
            category=category,
            conversation_summary=conversation.summary or "",
            recent_messages=recent_messages,
            prior_email_ids=prior_email_ids,
        )
        answer = rag_result.get("answer", "").strip() or "I couldn't find this in your emails."
        save_message(
            db=db,
            conversation=conversation,
            user_email=user.email,
            role="assistant",
            content=answer,
            message_meta={
                "filters": filter_meta,
                "retrieved_email_ids": rag_result.get("retrieved_email_ids", []),
                "rewritten_query": rag_result.get("rewritten_query", query.strip()),
                "focus_email_id": rag_result.get("focus_email_id"),
            },
        )
        maybe_refresh_summary(db=db, conversation=conversation, user_email=user.email)
    except HTTPException:
        db.rollback()
        trace_event(
            "http.ask.error",
            route="/auth/ask",
            user_email=user.email,
            conversation_id=response_conversation_id,
            error="http_exception",
        )
        raise
    except Exception as e:
        db.rollback()
        print(f"❌ ask_rag failed for {user.email}: {e}")
        trace_event(
            "http.ask.error",
            route="/auth/ask",
            user_email=user.email,
            conversation_id=response_conversation_id,
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ask pipeline failed: {e}",
        )
    finally:
        db.close()

    response_payload = {
        "answer": answer,
        "conversation_id": response_conversation_id,
    }
    trace_event(
        "http.ask.out",
        route="/auth/ask",
        user_email=user.email,
        response=response_payload,
    )
    return response_payload


@router.post("/conversations")
def create_new_conversation(payload: dict | None = None, user=Depends(get_current_user)):
    title = None
    if isinstance(payload, dict):
        candidate = payload.get("title")
        if isinstance(candidate, str):
            title = candidate.strip() or None

    db = SessionLocal()
    try:
        conversation = create_conversation(db=db, user_email=user.email, title=title)
        return {
            "conversation_id": conversation.id,
            "title": conversation.title,
            "created_at": conversation.created_at,
        }
    finally:
        db.close()


@router.get("/conversations")
def get_conversations(limit: int = 100, user=Depends(get_current_user)):
    db = SessionLocal()
    try:
        rows = list_conversations(db=db, user_email=user.email, limit=limit)
        return {
            "conversations": [serialize_conversation(row) for row in rows],
        }
    finally:
        db.close()


@router.get("/conversations/{conversation_id}/messages")
def get_conversation_history(
    conversation_id: str,
    limit: int = 200,
    user=Depends(get_current_user),
):
    db = SessionLocal()
    try:
        conversation = get_conversation(db=db, user_email=user.email, conversation_id=conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )
        rows = get_conversation_messages(
            db=db,
            conversation_id=conversation.id,
            user_email=user.email,
            limit=limit,
        )
        return {
            "conversation_id": conversation.id,
            "summary": conversation.summary or "",
            "messages": [serialize_message(row) for row in rows],
        }
    finally:
        db.close()


@router.delete("/conversations/{conversation_id}")
def delete_conversation_route(conversation_id: str, user=Depends(get_current_user)):
    db = SessionLocal()
    try:
        deleted = delete_conversation(db=db, user_email=user.email, conversation_id=conversation_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )
        return {"deleted": True, "conversation_id": conversation_id}
    finally:
        db.close()


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

    session_token = create_session_token(email)
    frontend_base = os.getenv("FRONTEND_URL", "http://localhost:5173").rstrip("/")
    response = RedirectResponse(url=f"{frontend_base}/dashboard/emails")
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session_token,
        httponly=True,
        max_age=SESSION_TTL_SECONDS,
        samesite="lax",
        secure=os.getenv("COOKIE_SECURE", "false").lower() == "true",
        path="/",
    )
    return response


@router.get("/index/status")
def get_index_status(user=Depends(get_current_user)):
    return get_user_index_status(user.email)
