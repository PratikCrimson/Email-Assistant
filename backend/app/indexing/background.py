import os
import time
from datetime import datetime
from app.email.gmail_client import get_email_service, fetch_latest_emails_page, fetch_email_detail
from app.email.parser import extract_email_feilds
from app.email.cleaner import clean_email_text
from app.indexing.state import get_or_create_user_sync_state
from app.email.categorizer import categorize_email
from app.db.postgress import SessionLocal
from app.db.models import Email
from app.ai.embeddings import embed_text
from app.email.date_parser import parse_email_date


def _get_batch_size() -> int:
    value = os.getenv("INDEX_BATCH_SIZE", "50")
    try:
        parsed = int(value)
    except ValueError:
        parsed = 50
    return max(1, min(parsed, 500))


def _get_max_pages() -> int | None:
    value = os.getenv("INDEX_MAX_PAGES", "0")
    try:
        parsed = int(value)
    except ValueError:
        parsed = 0
    if parsed <= 0:
        return None
    return parsed


def run_background_indexing(credentials, user_email: str):
    db = SessionLocal()
    started_indexing = False
    try:
        state = get_or_create_user_sync_state(db, user_email)
        if state.running:
            print(f"⏭ Indexing already running for {user_email}")
            return

        state.running = True
        state.started_at = datetime.utcnow()
        state.finished_at = None
        state.processed = 0
        state.total = 0
        db.commit()
        started_indexing = True

        service = get_email_service(credentials)
        batch_size = _get_batch_size()
        max_pages = _get_max_pages()

        # Resume a pending paginated window first; if none exists, start from last_synced_at.
        sync_after_ts_dt = state.sync_after_ts if state.next_page_token else state.last_synced_at
        after_ts = sync_after_ts_dt.isoformat() if sync_after_ts_dt else None
        page_token = state.next_page_token

        if not state.next_page_token:
            state.sync_after_ts = state.last_synced_at
            state.next_page_token = None
            state.has_more = False
            db.commit()

        messages: list[dict] = []
        pages_fetched = 0
        pending_next_page_token = None

        while True:
            page_messages, next_page_token = fetch_latest_emails_page(
                service=service,
                max_results=batch_size,
                after_ts=after_ts,
                page_token=page_token,
            )
            pages_fetched += 1
            messages.extend(page_messages)

            if not next_page_token:
                pending_next_page_token = None
                break

            if max_pages is not None and pages_fetched >= max_pages:
                pending_next_page_token = next_page_token
                break

            page_token = next_page_token

        # De-duplicate ids while preserving order.
        unique_messages = []
        seen_ids = set()
        for msg in messages:
            msg_id = msg.get("id")
            if not msg_id or msg_id in seen_ids:
                continue
            seen_ids.add(msg_id)
            unique_messages.append(msg)

        state.total = len(unique_messages)
        db.commit()
        print(
            f"🔄 Starting background indexing for {user_email}: "
            f"{state.total} emails across {pages_fetched} page(s)"
        )

        for i, msg in enumerate(unique_messages, start=1):
            # ⏭ Skip duplicates
            exists = db.query(Email).filter_by(
                user_email=user_email,
                email_id=msg["id"]
            ).first()

            if exists:
                print(f"⏭ Skipping already indexed: {msg['id']}")
                state.processed = i
                db.commit()
                continue

            detail = fetch_email_detail(service, msg["id"])
            parsed = extract_email_feilds(detail)

            subject = parsed.get("subject")
            sender = parsed.get("sender")
            date_str = parsed.get("date")

            raw_body = parsed.get("body", "")
            clean_body = clean_email_text(raw_body)

            category = categorize_email(f"{subject or ''} {clean_body}")
            print(f"🏷 Category: {category} | Subject: {subject}")

            # Build richer text for embeddings so that subject, sender, date and
            # category also influence similarity.
            embedding_text = (
                f"Subject: {subject or ''}\n"
                f"From: {sender or ''}\n"
                f"Date: {date_str or ''}\n"
                f"Category: {category or ''}\n"
                f"Body: {clean_body}"
            )
            embedding = embed_text(embedding_text)
            parsed_date = parse_email_date(date_str)

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

            state = get_or_create_user_sync_state(db, user_email)
            state.processed = i
            db.commit()
            time.sleep(0.05)

        # Persist pagination cursor so capped runs continue where they stopped.
        state = get_or_create_user_sync_state(db, user_email)
        if pending_next_page_token:
            state.next_page_token = pending_next_page_token
            state.has_more = True
            print(
                f"ℹ️ More pages pending for {user_email}. "
                "Run indexing again to continue from the saved cursor."
            )
        else:
            state.last_synced_at = datetime.utcnow()
            state.sync_after_ts = None
            state.next_page_token = None
            state.has_more = False
        db.commit()

    except Exception as e:
        db.rollback()
        # Reset cursor on crash so next run can restart cleanly from last_synced_at.
        try:
            state = get_or_create_user_sync_state(db, user_email)
            state.sync_after_ts = None
            state.next_page_token = None
            state.has_more = False
            db.commit()
        except Exception:
            db.rollback()
        print("❌ Background indexing crashed:", e)

    finally:
        try:
            if started_indexing:
                state = get_or_create_user_sync_state(db, user_email)
                state.running = False
                state.finished_at = datetime.utcnow()
                db.commit()
        finally:
            db.close()
        if started_indexing:
            print(f"🏁 Background indexing finished for {user_email}")
