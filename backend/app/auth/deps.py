from fastapi import Depends, HTTPException, status
from app.indexing.state import TOKEN_STORAGE


class User:
    def __init__(self, email: str):
        self.email = email

def get_current_user():
    if not TOKEN_STORAGE:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not logged in"
        )

    email = next(iter(TOKEN_STORAGE.keys()))
    return User(email=email)
