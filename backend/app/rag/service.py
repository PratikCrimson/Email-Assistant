from datetime import datetime
import re
from urllib.parse import urlparse
from sqlalchemy import text

from app.db.postgress import SessionLocal
from app.ai.llm import call_llm
from app.ai.embeddings import embed_text


def _format_date(value) -> str:
    if not value:
        return "Unknown"
    return value.strftime("%Y-%m-%d %H:%M:%S")


def _compact_url(url: str) -> str:
    candidate = url if url.startswith("http") else f"https://{url}"
    try:
        parsed = urlparse(candidate)
        host = parsed.netloc or "link"
        if host.startswith("www."):
            host = host[4:]
        return f"[{host} link]"
    except Exception:
        return "[link]"


def _compact_body(text: str) -> str:
    body = text or ""
    body = re.sub(r"(https?://\S+|www\.\S+)", lambda m: _compact_url(m.group(0)), body)
    body = re.sub(r"\s+", " ", body).strip()
    return body[:700]


def _format_row(row) -> str:
    body = _compact_body(row.cleaned_body or "")
    return (
        f"Subject: {row.subject}\n"
        f"From: {row.sender}\n"
        f"Date: {_format_date(row.date)}\n"
        f"Snippet: {body}"
    )


def rag_answer(
    user_email: str,
    query: str,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    from_sender: str | None = None,
    category: str | None = None,
):
    db = SessionLocal()
    from_sender_filter = f"%{from_sender}%" if from_sender else None

    try:
        semantic_sql = text("""
            SELECT email_id, subject, sender, date, cleaned_body
            FROM emails
            WHERE user_email = :user_email
              AND (:category IS NULL OR category = :category)
              AND (:start_date IS NULL OR date >= :start_date)
              AND (:end_date IS NULL OR date <= :end_date)
              AND (:from_sender IS NULL OR sender ILIKE :from_sender)
            ORDER BY embedding <=> CAST(:query_embedding AS vector)
            LIMIT 5
        """)

        query_embedding = embed_text(query)
        semantic_results = db.execute(
            semantic_sql,
            {
                "user_email": user_email,
                "query_embedding": query_embedding,
                "start_date": start_date,
                "end_date": end_date,
                "from_sender": from_sender_filter,
                "category": category,
            },
        ).fetchall()
    finally:
        db.close()

    if not semantic_results:
        return "No relevant emails found."

    context = "Semantically relevant emails:\n\n" + "\n\n".join(_format_row(r) for r in semantic_results)

    try:
        return call_llm(context, query)
    except Exception as e:
        print(f"❌ LLM call failed: {e}")
        fallback_lines = [
            "I found relevant emails, but I could not generate a full answer right now.",
            "Top matches:",
        ]
        for row in semantic_results[:3]:
            fallback_lines.append(
                f'- {row.subject or "(No subject)"} | {row.sender or "Unknown sender"} | {_format_date(row.date)}'
            )
        return "\n".join(fallback_lines)
