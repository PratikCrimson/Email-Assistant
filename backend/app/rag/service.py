from datetime import datetime
from sqlalchemy import text

from app.db.postgress import SessionLocal
from app.ai.llm import call_llm
from app.ai.embeddings import embed_text


def rag_answer(
    user_email: str,
    query: str,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    from_sender: str | None = None,
    category: str | None = None,
):
    db = SessionLocal()

    sql = text("""
        SELECT subject, sender, cleaned_body
        FROM emails
        WHERE user_email = :user_email
          AND (:category IS NULL OR category = :category)
          AND (:start_date IS NULL OR date >= :start_date)
          AND (:end_date IS NULL OR date <= :end_date)
          AND (:from_sender IS NULL OR sender ILIKE :from_sender)
        ORDER BY embedding <-> CAST(:query_embedding AS vector)
        LIMIT 5
    """)

    query_embedding = embed_text(query)
    from_sender_filter = f"%{from_sender}%" if from_sender else None

    try:
        results = db.execute(
            sql,
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

    if not results:
        return "No relevant emails found."

    context = "\n\n".join(
        f"Subject: {r.subject}\nFrom: {r.sender}\nBody: {r.cleaned_body[:1500]}"
        for r in results
    )

    return call_llm(context, query)