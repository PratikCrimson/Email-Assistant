from fastapi import FastAPI
from app.auth.routes import router as auth_router  

app = FastAPI(title="Email assistant")

app.include_router(auth_router , prefix="/auth")

@app.get("/health")
def health_check():
    return{'status' : "ok"}

