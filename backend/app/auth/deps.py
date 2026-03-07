from fastapi import HTTPException, Request, status
from app.db.postgress import SessionLocal
from app.db.models import UserToken
from app.core.security import SESSION_COOKIE_NAME, verify_session_token


class User:
    def __init__(self, email: str):
        self.email = email

def get_current_user(request: Request):
    session_token = request.cookies.get(SESSION_COOKIE_NAME)
    if not session_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing session",
        )

    session_email = verify_session_token(session_token)
    if not session_email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session",
        )

    db = SessionLocal()
    try:
        token_row = db.query(UserToken).filter(UserToken.user_email == session_email).first()
        if not token_row:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not logged in"
            )
        return User(email=token_row.user_email)
    finally:
        db.close()      