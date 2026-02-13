from fastapi import FastAPI
from app.auth.routes import router as auth_router  
from app.db.sqlite import init_db
from app.db.sqlite import ensure_category_column
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Email assistant")

app.include_router(auth_router , prefix="/auth")

@app.on_event("startup")
def startup():
    init_db()
    ensure_category_column()

@app.get("/health")
def health_check():
    return{'status' : "ok"}

