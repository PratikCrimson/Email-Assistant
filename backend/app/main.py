from fastapi import FastAPI
from app.auth.routes import router as auth_router  
from app.db.postgress import Base
from app.db.postgress import engine
from dotenv import load_dotenv  
from app.ai.embeddings import get_model
import threading
from sqlalchemy import text
load_dotenv()

app = FastAPI(title="Email assistant")

app.include_router(auth_router , prefix="/auth")

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    with engine.begin() as conn:
        conn.execute(text("""
            ALTER TABLE user_sync_states
            ADD COLUMN IF NOT EXISTS sync_after_ts TIMESTAMP,
            ADD COLUMN IF NOT EXISTS next_page_token TEXT,
            ADD COLUMN IF NOT EXISTS has_more BOOLEAN NOT NULL DEFAULT FALSE
        """))

    def warmup_model():
        print("Starting to warm up the embedding model ...")
        get_model()
        print("Embedding model warmed up successfully")
    threading.Thread(target=warmup_model , daemon=True).start()

@app.get("/health")
def health_check():
    return{'status' : "ok"}
