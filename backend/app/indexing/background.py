import time
from app.email.gmail_client import get_email_service, fetch_latest_emails, fetch_email_detail
from app.email.parser import extract_email_feilds
from app.email.cleaner import clean_email_text
from app.db.sqlite import get_conn
from datetime import datetime
from app.indexing.state import get_last_synced_at
from app.indexing.state import update_last_synced_at
from app.indexing.state import INDEX_STATE 
from app.email.categorizer import categorize_email



def run_background_indexing(credentials, max_results=100):
    try:
        INDEX_STATE["running"] = True
        INDEX_STATE["started_at"] = datetime.utcnow().isoformat()
        INDEX_STATE["finished_at"] = None
        INDEX_STATE["processed"] = 0

        service = get_email_service(credentials)
        messages = fetch_latest_emails(service, max_results=max_results)

        INDEX_STATE["total"] = len(messages)
        print(f"🔄 Starting background indexing: {INDEX_STATE['total']} emails")

        for i, msg in enumerate(messages, start=1):
            detail = fetch_email_detail(service, msg["id"])
            parsed = extract_email_feilds(detail)

            raw_body = parsed.get("body", "")
            clean_body = clean_email_text(raw_body)

            category = categorize_email(f"{parsed.get('subject')} {clean_body}")
            print(f"🏷 Category: {category} | Subject: {parsed.get('subject')}")


            save_email(parsed, clean_body, msg["id"], msg.get("threadId"), category)

            INDEX_STATE["processed"] = i

            print(f"✅ {i}/{INDEX_STATE['total']} | {parsed.get('subject')}")

            time.sleep(0.1)

    except Exception as e:
        print("❌ Background indexing crashed:", e)

    finally:
        INDEX_STATE["running"] = False
        INDEX_STATE["finished_at"] = datetime.utcnow().isoformat()
        print("🏁 Background indexing finished")

def save_email(parsed , clean_body , email_id , thread_id, category):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        INSERT OR IGNORE INTO emails (email_id, thread_id, subject, sender, date, cleaned_body,category, indexed_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (email_id, thread_id, parsed.get("subject"), parsed.get("sender"), parsed.get("date"), clean_body, category, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()