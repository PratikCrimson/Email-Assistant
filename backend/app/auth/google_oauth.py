import os
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

CLIENT_SECRET_FILE = os.path.join(
    os.path.dirname(__file__),
    "../core/client_secret.json"
)

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

REDIRECT_URI = "http://localhost:8000/auth/google/callback"

def get_google_oauth_flow():
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRET_FILE,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )
    return flow 

def get_user_email(credentials):
    service = build("gmail" , "v1" , credentials=credentials)
    results = service.users().getProfile(userId="me").execute()
    return results["emailAddress"] 
