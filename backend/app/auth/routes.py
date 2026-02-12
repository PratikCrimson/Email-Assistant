import threading    
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse, JSONResponse
from google.auth import credentials
from google_auth_oauthlib import flow
from app.auth.google_oauth import get_google_oauth_flow, get_user_email
from app.email.gmail_client import  fetch_latest_emails, fetch_email_detail , get_email_service
from app.email.parser import extract_email_feilds
from app.indexing.background import run_background_indexing

router = APIRouter()

TOKEN_STORAGE = {}

@router.get("/emails/test")
def fetch_emails_test():
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
    messages = fetch_latest_emails(service)

    emails =[]
    for msg in messages:
        detail = fetch_email_detail(service, msg["id"])
        parsed = extract_email_feilds(detail)
        emails.append(parsed)
    
    return {"count" : len(emails), "emails" : emails}

@router.post("/ ")
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
        args = (credentials,10),
        daemon=True,
    )

    thread.start()

    return {"status" : "started" , "message" : "Background indexing started"}
    

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

