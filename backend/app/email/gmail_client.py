from googleapiclient.discovery import build
from datetime import datetime

def get_email_service(credentials):
    return build("gmail", "v1", credentials=credentials)


def _build_after_query(after_ts: str | None = None) -> str | None:
    if not after_ts:
        return None

    try:
        # Convert ISO datetime string to Unix timestamp (seconds)
        dt = datetime.fromisoformat(after_ts.replace("Z", ""))
        unix_ts = int(dt.timestamp())
        return f"after:{unix_ts}"
    except Exception as e:
        print("⚠️ Failed to parse after_ts, falling back to full fetch:", e)
        return None


def fetch_latest_emails_page(
    service,
    max_results=50,
    after_ts: str | None = None,
    page_token: str | None = None,
):
    """
    Fetch one page of Gmail messages.
    Returns (messages, next_page_token).
    """
    q = _build_after_query(after_ts)

    kwargs = {
        "userId": "me",
        "maxResults": max_results,
    }

    if q:
        kwargs["q"] = q

    if page_token:
        kwargs["pageToken"] = page_token

    results = service.users().messages().list(**kwargs).execute()
    return results.get("messages", []), results.get("nextPageToken")


def fetch_latest_emails(service, max_results=10, after_ts: str | None = None):
    """
    Backward-compatible helper: fetch only first page.
    """
    messages, _ = fetch_latest_emails_page(
        service=service,
        max_results=max_results,
        after_ts=after_ts,
        page_token=None,
    )
    return messages


def fetch_email_detail(service, msg_id):
    message = service.users().messages().get(
        userId="me",
        id=msg_id,
        format="full"
    ).execute()
    return message
