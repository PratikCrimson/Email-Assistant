from fastapi import Depends, HTTPException, status
from app.indexing.state import TOKEN_STORAGE
from app.db.postgress import SessionLocal
from app.db.models import UserToken


class User:
    def __init__(self, email: str):
        self.email = email

def get_current_user():
    db = SessionLocal()
    try:
        token_row = db.query(UserToken).first()
        if not token_row:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not logged in"
            )
        return User(email=token_row.user_email)
    finally:
        db.close()
