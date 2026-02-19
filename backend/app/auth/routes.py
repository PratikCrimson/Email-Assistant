import threading    
from fastapi import APIRouter, Request , Depends
from fastapi.responses import RedirectResponse, JSONResponse
from google.auth import credentials
from google_auth_oauthlib import flow
from app.auth.google_oauth import get_google_oauth_flow, get_user_email
from app.email.gmail_client import  fetch_latest_emails, fetch_email_detail , get_email_service
from app.email.parser import extract_email_feilds
from app.indexing.background import run_background_indexing
from app.indexing.state import INDEX_STATE
from app.email.date_parser import parse_email_date
from app.ai.embeddings import embed_text
from app.db.postgress import SessionLocal
from app.db.models import Email
from sqlalchemy import text
from app.auth.deps import get_current_user
from app.rag.service import rag_answer


router = APIRouter()


from app.indexing.state import TOKEN_STORAGE

@router.get("/emails/test")
def fetch_emailS_test_and_trigger_bg():
    if not TOKEN_STORAGE:
        return {"error" : "no users is logged in yet"}
    
    email , token_data = next(iter(TOKEN_STORAGE.items()))

    from google.oauth2.credentials import Credentials

    credentials = Credentials(
        token=token_data["access_token"],
        refresh_token=token_data["refresh_token"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=None,
        client_secret=None,
        scopes=["https://www.googleapis.com/auth/gmail.readonly"],
    )

    service = get_email_service(credentials)

    messages = fetch_latest_emails(service , max_results =10)
    emails = []

    for msg in messages:
        detail = fetch_email_detail(service , msg["id"])
        parsed = extract_email_feilds(detail)
        emails.append(parsed)

    if not INDEX_STATE["running"]:
        INDEX_STATE["running"] = True

        threading.Thread(
            target=run_background_indexing,
            args=(credentials, email, 50),
            daemon=True
        ).start()
    return {"preview" : emails, "background_indexing" : "started"}

@router.post("/index/start")
def start_background_indexing():
    if not TOKEN_STORAGE:
        return {"error" : "no users is logged in yet"}
    
    email, token_data = next(iter(TOKEN_STORAGE.items()))

    from google.oauth2.credentials import Credentials 

    credentials = Credentials(
        token=token_data["access_token"],
        refresh_token=token_data["refresh_token"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=None,
        client_secret=None,
        scopes=["https://www.googleapis.com/auth/gmail.readonly"],
    )

    thread = threading.Thread(
        target=run_background_indexing,
        args = (credentials, email, 50),
        daemon=True,
    )

    thread.start()

    return {"status" : "started" , "message" : "Background indexing started"}

@router.get("/search")
def semantic_search(q:str , category:str | None = None , limit:int = 5):
    db = SessionLocal()

    try:
        query_embedding = embed_text(q)

        sql = text("""
        SELECT email_id, subject, sender, date, category, cleaned_body, embedding <-> CAST(:query_embedding AS vector) AS distance
            FROM emails
            WHERE user_email = :user_email
            AND (:category IS NULL OR category = :category)
            ORDER BY embedding <-> CAST(:query_embedding AS vector)
            LIMIT :limit
        """)
        
        results = db.execute(
            sql,
            {
                "query_embedding": query_embedding,
                "category": category,
                "limit": limit,
                "user_email": user.email,
            }
        ).fetchall()

        return {
            "query" : q,
            "category" : category,
            "results" : [
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
def ask_rag(payload: dict , user = Depends(get_current_user)):
    query = payload["query"]
    answer = rag_answer(user_email = user.email, query = query)
    return {"answer": answer}
    


# @router.get("/emails/list")
# def list_indexed_emails(limit: int = 20):
#     conn = get_conn()
#     cur = conn.cursor()
#     rows = cur.execute("""
#         SELECT email_id, subject, sender, date, substr(cleaned_body, 1, 200) AS preview
#         FROM emails
#         ORDER BY indexed_at DESC
#         LIMIT ?
#     """, (limit,)).fetchall()

#     conn.close()
#     return {"count": len(rows), "emails": [dict(r) for r in rows]}


@router.get("/login")
def login():
    flow = get_google_oauth_flow()
    auth_url ,_ = flow.authorization_url(
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

    TOKEN_STORAGE[email] = {
        "access_token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "expiry" : credentials.expiry.isoformat() if credentials.expiry else None,
    }

    print("✅ Logged in user email:", email)
    print("🔐 Access Token:", credentials.token[:20], "...")

    return JSONResponse({
        "message": "Logged in successfully",
        "email": email
    })

@router.get("/index/status")
def get_index_status():
    return INDEX_STATE