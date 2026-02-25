from googleapiclient.discovery import build
from datetime import datetime

def get_email_service(credentials):
    return build("gmail", "v1", credentials=credentials)


def fetch_latest_emails(service, max_results=10, after_ts: str | None = None):
    """
    Fetch latest Gmail messages.
    If after_ts (ISO datetime string) is provided, only fetch emails after that time.
    """
    q = None

    if after_ts:
        try:
            # Convert ISO datetime string to Unix timestamp (seconds)
            dt = datetime.fromisoformat(after_ts.replace("Z", ""))
            unix_ts = int(dt.timestamp())
            q = f"after:{unix_ts}"
        except Exception as e:
            print("⚠️ Failed to parse after_ts, falling back to full fetch:", e)
            q = None

    kwargs = {
        "userId": "me",
        "maxResults": max_results,
    }

    if q:
        kwargs["q"] = q

    results = service.users().messages().list(**kwargs).execute()
    return results.get("messages", [])


def fetch_email_detail(service, msg_id):
    message = service.users().messages().get(
        userId="me",
        id=msg_id,
        format="full"
    ).execute()
    return message