from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse, JSONResponse
from google_auth_oauthlib import flow
from app.auth.google_oauth import get_google_oauth_flow, get_user_email

router = APIRouter()

TOKEN_STORAGE = {}

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

