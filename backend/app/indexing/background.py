import time
from app.email.gmail_client import get_email_service, fetch_latest_emails, fetch_email_detail
from app.email.parser import extract_email_feilds
from app.email.cleaner import clean_email_text
from app.db.sqlite import get_conn
from datetime import datetime
from app.indexing.state import get_last_synced_at
from app.indexing.state import update_last_synced_at



def run_background_indexing(credentials , max_results=10):
    service = get_email_service(credentials)
    
    last_synced_at_iso = get_last_synced_at()
    print(f"🔄 Last synced at: {last_synced_at_iso}")

    after_ts = None
    if last_synced_at_iso:
        after_ts = int(datetime.fromisoformat(last_synced_at_iso).timestamp())

    messages = fetch_latest_emails(service, max_results = max_results , after_ts = after_ts)
    print(f"🔄 Found {len(messages)} emails after {after_ts}")

    newest_seen_iso = None
    
    

    for i, msg in enumerate(messages, start=1):
       
            detail = fetch_email_detail(service, msg["id"])
            parsed = extract_email_feilds(detail)

            raw_body = parsed.get("body" ,  "")
            clean_body = clean_email_text(raw_body)

            internal_ts = int(detail["internalDate"]) / 1000
            email_iso = datetime.utcfromtimestamp(internal_ts).isoformat()

            save_email(parsed, clean_body, msg["id"] , msg.get("threadId"))

            if not newest_seen_iso or email_iso > newest_seen_iso:
                newest_seen_iso = email_iso

            print(f"✅ {i}/{len(messages)} | {parsed.get('subject')} | {email_iso}")

            if newest_seen_iso:
                update_last_synced_at(newest_seen_iso)
            else:
                print("❌ No new emails found")
        
            print("Incremental sync completed")

def save_email(parsed , clean_body , email_id , thread_id):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        INSERT OR IGNORE INTO emails (email_id, thread_id, subject, sender, date, cleaned_body, indexed_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (email_id, thread_id, parsed.get("subject"), parsed.get("sender"), parsed.get("date"), clean_body, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()