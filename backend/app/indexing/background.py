import time
from datetime import datetime
from app.email.gmail_client import get_email_service, fetch_latest_emails, fetch_email_detail
from app.email.parser import extract_email_feilds
from app.email.cleaner import clean_email_text
from app.indexing.state import get_last_synced_at, update_last_synced_at, INDEX_STATE
from app.email.categorizer import categorize_email
from app.db.postgress import SessionLocal
from app.db.models import Email
from app.ai.embeddings import embed_text
from app.email.date_parser import parse_email_date


def run_background_indexing(credentials, user_email: str, max_results=50):
    try:
        INDEX_STATE["running"] = True
        INDEX_STATE["started_at"] = datetime.utcnow().isoformat()
        INDEX_STATE["finished_at"] = None
        INDEX_STATE["processed"] = 0

        service = get_email_service(credentials)

        # 🔁 Incremental sync: fetch only after last sync (if your client supports it)
        last_synced_at = get_last_synced_at()
        messages = fetch_latest_emails(service, max_results=max_results, after_ts=last_synced_at)

        INDEX_STATE["total"] = len(messages)
        print(f"🔄 Starting background indexing: {INDEX_STATE['total']} new emails")

        db = SessionLocal()

        for i, msg in enumerate(messages, start=1):
            # ⏭ Skip duplicates
            exists = db.query(Email).filter_by(
                user_email=user_email,
                email_id=msg["id"]
            ).first()

            if exists:
                print(f"⏭ Skipping already indexed: {msg['id']}")
                INDEX_STATE["processed"] = i
                continue

            detail = fetch_email_detail(service, msg["id"])
            parsed = extract_email_feilds(detail)

            raw_body = parsed.get("body", "")
            clean_body = clean_email_text(raw_body)

            category = categorize_email(f"{parsed.get('subject')} {clean_body}")
            print(f"🏷 Category: {category} | Subject: {parsed.get('subject')}")

            embedding = embed_text(clean_body)
            parsed_date = parse_email_date(parsed.get("date"))

            email_row = Email(
                user_email=user_email,
                email_id=msg["id"],
                thread_id=msg.get("threadId"),
                subject=parsed.get("subject"),
                sender=parsed.get("sender"),
                date=parsed_date,
                cleaned_body=clean_body,
                category=category,
                embedding=embedding,
            )

            try:
                db.add(email_row)
                db.commit()
                print(f"✅ Indexed: {parsed.get('subject')}")
            except Exception as e:
                db.rollback()
                print(f"❌ Error saving email {msg['id']}: {e}")

            INDEX_STATE["processed"] = i
            time.sleep(0.05)

        # 🧾 Mark last synced timestamp after successful run
        update_last_synced_at(datetime.utcnow().isoformat())

    except Exception as e:
        print("❌ Background indexing crashed:", e)

    finally:
        INDEX_STATE["running"] = False
        INDEX_STATE["finished_at"] = datetime.utcnow().isoformat()
        print("🏁 Background indexing finished")