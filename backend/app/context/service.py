import os
from datetime import datetime, timezone

from sqlalchemy import desc

from app.ai.llm import summarize_conversation
from app.core.logging import trace_event
from app.db.models import Conversation, ConversationMessage


def _env_int(name: str, default: int, minimum: int, maximum: int) -> int:
    raw = os.getenv(name, str(default))
    try:
        value = int(raw)
    except Exception:
        value = default
    return max(minimum, min(value, maximum))


CONTEXT_RECENT_MESSAGES = _env_int("CONTEXT_RECENT_MESSAGES", 8, 2, 30)
CONTEXT_MESSAGE_MAX_CHARS = _env_int("CONTEXT_MESSAGE_MAX_CHARS", 8000, 500, 50000)
CONTEXT_SUMMARY_MIN_MESSAGES = _env_int("CONTEXT_SUMMARY_MIN_MESSAGES", 12, 4, 200)
CONTEXT_SUMMARY_KEEP_RECENT = _env_int("CONTEXT_SUMMARY_KEEP_RECENT", 6, 2, 50)
CONTEXT_SUMMARY_EVERY_N_MESSAGES = _env_int("CONTEXT_SUMMARY_EVERY_N_MESSAGES", 4, 1, 25)
CONTEXT_SUMMARY_MAX_CHARS = _env_int("CONTEXT_SUMMARY_MAX_CHARS", 4000, 500, 15000)


def _trim_text(value: str | None, *, max_chars: int = CONTEXT_MESSAGE_MAX_CHARS) -> str:
    if not value:
        return ""
    text = value.strip()
    if len(text) <= max_chars:
        return text
    return text[:max_chars]


def _to_utc_iso(value):
    if not value:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    else:
        value = value.astimezone(timezone.utc)
    return value.isoformat().replace("+00:00", "Z")


def _clean_email_ids(values) -> list[str]:
    if not isinstance(values, list):
        return []
    cleaned: list[str] = []
    seen = set()
    for item in values:
        if not isinstance(item, str):
            continue
        candidate = item.strip()
        if not candidate or candidate in seen:
            continue
        seen.add(candidate)
        cleaned.append(candidate)
        if len(cleaned) >= 25:
            break
    return cleaned


def create_conversation(db, user_email: str, title: str | None = None) -> Conversation:
    row = Conversation(
        user_email=user_email,
        title=_trim_text(title, max_chars=255) if title else None,
        summary="",
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    trace_event(
        "db.conversation_created",
        conversation_id=row.id,
        user_email=user_email,
        title=row.title,
    )
    return row


def get_conversation(db, user_email: str, conversation_id: str) -> Conversation | None:
    if not conversation_id:
        return None
    return (
        db.query(Conversation)
        .filter(
            Conversation.id == conversation_id,
            Conversation.user_email == user_email,
        )
        .first()
    )


def ensure_conversation(db, user_email: str, conversation_id: str | None = None) -> Conversation:
    if conversation_id:
        row = get_conversation(db, user_email, conversation_id)
        if not row:
            raise ValueError("Conversation not found for this user")
        return row
    return create_conversation(db, user_email=user_email)


def save_message(
    db,
    conversation: Conversation,
    user_email: str,
    role: str,
    content: str,
    message_meta: dict | None = None,
) -> ConversationMessage:
    trimmed_content = _trim_text(content)
    if role == "user" and not (conversation.title or "").strip():
        conversation.title = _trim_text(trimmed_content, max_chars=120)

    row = ConversationMessage(
        conversation_id=conversation.id,
        user_email=user_email,
        role=role,
        content=trimmed_content,
        message_meta=message_meta or {},
    )
    db.add(row)
    conversation.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(row)
    trace_event(
        "db.message_saved",
        message_id=row.id,
        conversation_id=conversation.id,
        user_email=user_email,
        role=role,
        content=row.content,
        message_meta=row.message_meta,
    )
    return row


def get_recent_messages_for_prompt(
    db,
    conversation_id: str,
    user_email: str,
    limit: int = CONTEXT_RECENT_MESSAGES,
) -> list[ConversationMessage]:
    rows = (
        db.query(ConversationMessage)
        .filter(
            ConversationMessage.conversation_id == conversation_id,
            ConversationMessage.user_email == user_email,
        )
        .order_by(desc(ConversationMessage.created_at), desc(ConversationMessage.id))
        .limit(limit)
        .all()
    )
    rows.reverse()
    return rows


def get_last_assistant_email_refs(db, conversation_id: str, user_email: str) -> list[str]:
    row = (
        db.query(ConversationMessage)
        .filter(
            ConversationMessage.conversation_id == conversation_id,
            ConversationMessage.user_email == user_email,
            ConversationMessage.role == "assistant",
        )
        .order_by(desc(ConversationMessage.created_at), desc(ConversationMessage.id))
        .first()
    )
    if not row or not isinstance(row.message_meta, dict):
        return []
    meta = row.message_meta
    retrieved_ids = _clean_email_ids(meta.get("retrieved_email_ids"))
    focus_id = meta.get("focus_email_id")

    if not isinstance(focus_id, str):
        return retrieved_ids

    focus_id = focus_id.strip()
    if not focus_id:
        return retrieved_ids

    if focus_id in retrieved_ids:
        return [focus_id] + [item for item in retrieved_ids if item != focus_id]
    return [focus_id] + retrieved_ids


def get_conversation_messages(
    db,
    conversation_id: str,
    user_email: str,
    limit: int = 200,
) -> list[ConversationMessage]:
    safe_limit = max(1, min(limit, 500))
    return (
        db.query(ConversationMessage)
        .filter(
            ConversationMessage.conversation_id == conversation_id,
            ConversationMessage.user_email == user_email,
        )
        .order_by(ConversationMessage.created_at.asc(), ConversationMessage.id.asc())
        .limit(safe_limit)
        .all()
    )


def list_conversations(db, user_email: str, limit: int = 100) -> list[Conversation]:
    safe_limit = max(1, min(limit, 500))
    return (
        db.query(Conversation)
        .filter(Conversation.user_email == user_email)
        .order_by(desc(Conversation.updated_at), desc(Conversation.created_at))
        .limit(safe_limit)
        .all()
    )


def delete_conversation(db, user_email: str, conversation_id: str) -> bool:
    row = get_conversation(db=db, user_email=user_email, conversation_id=conversation_id)
    if not row:
        return False

    (
        db.query(ConversationMessage)
        .filter(
            ConversationMessage.conversation_id == conversation_id,
            ConversationMessage.user_email == user_email,
        )
        .delete(synchronize_session=False)
    )
    db.delete(row)
    db.commit()
    trace_event(
        "db.conversation_deleted",
        conversation_id=conversation_id,
        user_email=user_email,
    )
    return True


def serialize_message(row: ConversationMessage) -> dict:
    return {
        "id": row.id,
        "role": row.role,
        "content": row.content,
        "created_at": _to_utc_iso(row.created_at),
    }


def serialize_conversation(row: Conversation) -> dict:
    fallback_title = f"Chat {row.created_at.strftime('%Y-%m-%d')}" if row.created_at else "New chat"
    return {
        "conversation_id": row.id,
        "title": (row.title or "").strip() or fallback_title,
        "summary": row.summary or "",
        "created_at": _to_utc_iso(row.created_at),
        "updated_at": _to_utc_iso(row.updated_at),
    }


def _render_for_summary(messages: list[ConversationMessage]) -> str:
    lines: list[str] = []
    for msg in messages:
        role = "User" if msg.role == "user" else "Assistant"
        text = (msg.content or "").replace("\n", " ").strip()
        if not text:
            continue
        if len(text) > 500:
            text = text[:500]
        lines.append(f"{role}: {text}")
    return "\n".join(lines)


def maybe_refresh_summary(db, conversation: Conversation, user_email: str) -> None:
    rows = (
        db.query(ConversationMessage)
        .filter(
            ConversationMessage.conversation_id == conversation.id,
            ConversationMessage.user_email == user_email,
        )
        .order_by(ConversationMessage.created_at.asc(), ConversationMessage.id.asc())
        .all()
    )
    count = len(rows)
    if count < CONTEXT_SUMMARY_MIN_MESSAGES:
        return
    if count % CONTEXT_SUMMARY_EVERY_N_MESSAGES != 0:
        return
    if count <= CONTEXT_SUMMARY_KEEP_RECENT:
        return

    older_rows = rows[:-CONTEXT_SUMMARY_KEEP_RECENT]
    transcript = _render_for_summary(older_rows)
    if not transcript:
        return

    try:
        new_summary = summarize_conversation(
            existing_summary=conversation.summary or "",
            transcript=transcript,
        )
    except Exception as e:
        print(f"WARN failed to refresh conversation summary: {e}")
        db.rollback()
        return

    if not new_summary:
        return

    conversation.summary = _trim_text(new_summary, max_chars=CONTEXT_SUMMARY_MAX_CHARS)
    conversation.updated_at = datetime.utcnow()
    db.commit()
    trace_event(
        "db.conversation_summary_updated",
        conversation_id=conversation.id,
        user_email=user_email,
        summary=conversation.summary,
    )
