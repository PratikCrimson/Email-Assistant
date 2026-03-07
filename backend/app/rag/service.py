from datetime import datetime
import re
from urllib.parse import urlparse
from sqlalchemy import bindparam, text

from app.db.postgress import SessionLocal
from app.ai.llm import call_llm, rewrite_query_with_context
from app.ai.embeddings import embed_text
from app.core.logging import trace_event


FULL_BODY_MAX_CHARS = 12000


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


def _compact_body(text_value: str, *, max_chars: int = 700) -> str:
    body = text_value or ""
    body = re.sub(r"(https?://\S+|www\.\S+)", lambda m: _compact_url(m.group(0)), body)
    body = re.sub(r"\s+", " ", body).strip()
    return body[:max_chars]


def _format_row(row, *, body_chars: int = 700) -> str:
    body = _compact_body(row.cleaned_body or "", max_chars=body_chars)
    return (
        f"Email ID: {row.email_id}\n"
        f"Subject: {row.subject}\n"
        f"From: {row.sender}\n"
        f"Date: {_format_date(row.date)}\n"
        f"Snippet: {body}"
    )


def _format_full_body_row(row) -> str:
    raw = (row.cleaned_body or "").strip()
    if len(raw) > FULL_BODY_MAX_CHARS:
        raw = raw[:FULL_BODY_MAX_CHARS]
    return (
        f"Email ID: {row.email_id}\n"
        f"Subject: {row.subject}\n"
        f"From: {row.sender}\n"
        f"Date: {_format_date(row.date)}\n"
        f"Body:\n{raw}"
    )


def _requests_full_body(question: str) -> bool:
    q = (question or "").strip().lower()
    if not q:
        return False
    phrases = [
        "full body",
        "whole body",
        "full email",
        "entire email",
        "complete email",
        "full content",
        "entire content",
        "whole content",
        "complete content",
        "full message",
        "entire message",
        "whole message",
        "complete message",
    ]
    return any(phrase in q for phrase in phrases)


def _is_latest_query(question: str) -> bool:
    q = (question or "").strip().lower()
    if not q:
        return False
    tokens = ["latest", "newest", "most recent", "last email", "last mail", "recent mail", "recent email"]
    return any(token in q for token in tokens)


def _prioritize_rows_by_email_ids(rows, ordered_ids: list[str]):
    if not rows or not ordered_ids:
        return rows
    rows_by_id = {}
    for row in rows:
        email_id = getattr(row, "email_id", None)
        if isinstance(email_id, str) and email_id:
            rows_by_id[email_id] = row

    prioritized = []
    seen = set()
    for email_id in ordered_ids:
        row = rows_by_id.get(email_id)
        if row is None:
            continue
        prioritized.append(row)
        seen.add(email_id)
    for row in rows:
        email_id = getattr(row, "email_id", None)
        if email_id in seen:
            continue
        prioritized.append(row)
    return prioritized


def _pick_focus_row(query: str, prior_rows, semantic_results):
    ordered_rows = []
    seen = set()
    for row in list(prior_rows or []) + list(semantic_results or []):
        email_id = getattr(row, "email_id", None)
        if not email_id or email_id in seen:
            continue
        ordered_rows.append(row)
        seen.add(email_id)
    if not ordered_rows:
        return None
    if not _is_latest_query(query):
        return ordered_rows[0]
    dated_rows = [row for row in ordered_rows if getattr(row, "date", None) is not None]
    if not dated_rows:
        return ordered_rows[0]
    return max(dated_rows, key=lambda row: row.date)


def _render_recent_messages_text(recent_messages: list | None) -> str:
    if not recent_messages:
        return ""

    lines: list[str] = []
    for msg in recent_messages:
        role = None
        content = None
        if isinstance(msg, dict):
            role = msg.get("role")
            content = msg.get("content")
        else:
            role = getattr(msg, "role", None)
            content = getattr(msg, "content", None)

        if not isinstance(content, str):
            continue

        text_value = re.sub(r"\s+", " ", content).strip()
        if not text_value:
            continue
        if len(text_value) > 320:
            text_value = text_value[:320]

        speaker = "User" if role == "user" else "Assistant"
        lines.append(f"{speaker}: {text_value}")

    return "\n".join(lines)


def _extract_ids(rows) -> list[str]:
    ids: list[str] = []
    seen = set()
    for row in rows:
        candidate = getattr(row, "email_id", None)
        if not candidate or candidate in seen:
            continue
        ids.append(candidate)
        seen.add(candidate)
    return ids


def _semantic_search(
    db,
    *,
    user_email: str,
    query_text: str,
    start_date: datetime | None,
    end_date: datetime | None,
    from_sender_filter: str | None,
    category: str | None,
    limit: int,
):
    semantic_sql = text("""
        SELECT email_id, subject, sender, date, cleaned_body
        FROM emails
        WHERE user_email = :user_email
          AND (:category IS NULL OR category = :category)
          AND (:start_date IS NULL OR date >= :start_date)
          AND (:end_date IS NULL OR date <= :end_date)
          AND (:from_sender IS NULL OR sender ILIKE :from_sender)
        ORDER BY embedding <=> CAST(:query_embedding AS vector)
        LIMIT :limit
    """)
    query_embedding = embed_text(query_text)
    return db.execute(
        semantic_sql,
        {
            "user_email": user_email,
            "query_embedding": query_embedding,
            "start_date": start_date,
            "end_date": end_date,
            "from_sender": from_sender_filter,
            "category": category,
            "limit": limit,
        },
    ).fetchall()


def _merge_rows_by_id(primary_rows, secondary_rows, *, max_rows: int = 10):
    merged = []
    seen = set()
    for row in list(primary_rows or []) + list(secondary_rows or []):
        email_id = getattr(row, "email_id", None)
        if not email_id or email_id in seen:
            continue
        merged.append(row)
        seen.add(email_id)
        if len(merged) >= max_rows:
            break
    return merged


def rag_answer_with_context(
    user_email: str,
    query: str,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    from_sender: str | None = None,
    category: str | None = None,
    conversation_summary: str | None = None,
    recent_messages: list | None = None,
    prior_email_ids: list[str] | None = None,
) -> dict:
    trace_event(
        "rag.start",
        user_email=user_email,
        query=query,
        filters={
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
            "from_sender": from_sender,
            "category": category,
        },
        prior_email_ids=prior_email_ids or [],
    )

    db = SessionLocal()
    from_sender_filter = f"%{from_sender}%" if from_sender else None

    cleaned_prior_ids: list[str] = []
    if isinstance(prior_email_ids, list):
        for item in prior_email_ids:
            if isinstance(item, str) and item.strip():
                cleaned_prior_ids.append(item.strip())
            if len(cleaned_prior_ids) >= 15:
                break

    recent_messages_text = _render_recent_messages_text(recent_messages)
    effective_query = rewrite_query_with_context(
        question=query,
        conversation_summary=conversation_summary or "",
        recent_messages_text=recent_messages_text,
    )
    trace_event(
        "rag.rewrite",
        query=query,
        rewritten_query=effective_query,
        used_summary=bool(conversation_summary),
        recent_messages_count=len(recent_messages or []),
    )

    semantic_results = []
    prior_rows = []
    try:
        semantic_primary = _semantic_search(
            db,
            user_email=user_email,
            query_text=effective_query,
            start_date=start_date,
            end_date=end_date,
            from_sender_filter=from_sender_filter,
            category=category,
            limit=5,
        )
        semantic_secondary = []
        if effective_query.strip().lower() != query.strip().lower():
            semantic_secondary = _semantic_search(
                db,
                user_email=user_email,
                query_text=query.strip(),
                start_date=start_date,
                end_date=end_date,
                from_sender_filter=from_sender_filter,
                category=category,
                limit=5,
            )
        semantic_results = _merge_rows_by_id(semantic_primary, semantic_secondary, max_rows=10)

        if cleaned_prior_ids:
            prior_sql = text("""
                SELECT email_id, subject, sender, date, cleaned_body
                FROM emails
                WHERE user_email = :user_email
                  AND email_id IN :email_ids
                ORDER BY date DESC NULLS LAST
                LIMIT 10
            """).bindparams(bindparam("email_ids", expanding=True))

            prior_rows = db.execute(
                prior_sql,
                {
                    "user_email": user_email,
                    "email_ids": cleaned_prior_ids,
                },
            ).fetchall()
            prior_rows = _prioritize_rows_by_email_ids(prior_rows, cleaned_prior_ids)
    finally:
        db.close()

    trace_event(
        "rag.retrieve",
        semantic_count=len(semantic_results),
        semantic_email_ids=_extract_ids(semantic_results),
        prior_count=len(prior_rows),
        prior_email_ids=_extract_ids(prior_rows),
    )

    if not semantic_results and not prior_rows:
        trace_event("rag.no_results", query=query, rewritten_query=effective_query)
        return {
            "answer": "No relevant emails found.",
            "retrieved_email_ids": [],
            "rewritten_query": effective_query,
            "focus_email_id": None,
        }

    full_body_requested = _requests_full_body(query)
    focus_row = _pick_focus_row(query=query, prior_rows=prior_rows, semantic_results=semantic_results)
    focus_email_id = getattr(focus_row, "email_id", None) if focus_row else None

    context_blocks: list[str] = []
    if conversation_summary:
        context_blocks.append(f"Conversation summary:\n{conversation_summary.strip()}")
    if recent_messages_text:
        context_blocks.append(f"Recent conversation:\n{recent_messages_text}")
    if prior_rows:
        context_blocks.append(
            "Previously referenced emails from this conversation:\n\n"
            + "\n\n".join(_format_row(r) for r in prior_rows)
        )
    if semantic_results:
        context_blocks.append(
            "Semantically relevant emails for the current query:\n\n"
            + "\n\n".join(_format_row(r) for r in semantic_results)
        )
    if full_body_requested and focus_row is not None:
        context_blocks.append(
            "Focused email for referential follow-up (full content requested):\n\n"
            + _format_full_body_row(focus_row)
        )

    full_context = "\n\n".join(context_blocks)

    try:
        answer = call_llm(full_context, query)
    except Exception as e:
        print(f"❌ LLM call failed: {e}")
        trace_event("rag.llm_error", error=str(e), query=query, rewritten_query=effective_query)
        source_rows = semantic_results or prior_rows
        fallback_lines = [
            "I found relevant emails, but I could not generate a full answer right now.",
            "Top matches:",
        ]
        for row in source_rows[:3]:
            fallback_lines.append(
                f'- {row.subject or "(No subject)"} | {row.sender or "Unknown sender"} | {_format_date(row.date)}'
            )
        answer = "\n".join(fallback_lines)

    semantic_ids = _extract_ids(semantic_results)
    merged_ids = semantic_ids + [item for item in _extract_ids(prior_rows) if item not in semantic_ids]

    trace_event(
        "rag.answer",
        query=query,
        rewritten_query=effective_query,
        answer=answer,
        returned_email_ids=merged_ids[:15],
        focus_email_id=focus_email_id,
        full_body_requested=full_body_requested,
    )

    return {
        "answer": answer,
        "retrieved_email_ids": merged_ids[:15],
        "rewritten_query": effective_query,
        "focus_email_id": focus_email_id,
    }


def rag_answer(
    user_email: str,
    query: str,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    from_sender: str | None = None,
    category: str | None = None,
):
    result = rag_answer_with_context(
        user_email=user_email,
        query=query,
        start_date=start_date,
        end_date=end_date,
        from_sender=from_sender,
        category=category,
    )
    return result["answer"]
