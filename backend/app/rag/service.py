from app.db.postgress import SessionLocal
from app.db.models import Email
from app.ai.llm import call_llm
from sqlalchemy import text

def rag_answer(user_email:str , query:str):
    db = SessionLocal()
    
    sql = text("""
        SELECT subject, sender, cleaned_body
        FROM emails
        WHERE user_email = :user_email
        ORDER BY embedding <-> CAST(:query_embedding AS vector)
        LIMIT 5
    """)
     
    from app.ai.embeddings import embed_text
    query_embedding = embed_text(query)
     
    results = db.execute(sql, {
        "user_email": user_email,
        "query_embedding": query_embedding
    }).fetchall()
     
    if not results:
         return "No relevant emails found."
     
    context = "/n/n".join(
        f"Subject: {r.subject}\nFrom: {r.sender}\nBody: {r.cleaned_body[:1500]}"
        for r in results
    )
    
    return call_llm(context, query)