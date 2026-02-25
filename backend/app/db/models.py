from sqlalchemy import Column, Integer, Text, TIMESTAMP, UniqueConstraint, DateTime, String
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector

Base = declarative_base()

class Email(Base):
    __tablename__ = "emails"

    __table_args__ = (
        UniqueConstraint("user_email", "email_id", name="uq_user_email_msg"),
    )

    id = Column(Integer, primary_key=True)
    user_email = Column(Text, index=True, nullable=False)
    email_id = Column(Text, index=True, nullable=False)  # ❌ removed unique=True
    thread_id = Column(Text)
    subject = Column(Text)
    sender = Column(Text)
    date = Column(TIMESTAMP)
    category = Column(Text)
    cleaned_body = Column(Text)
    embedding = Column(Vector(384))
    indexed_at = Column(TIMESTAMP, server_default=func.now())


class UserToken(Base):
    __tablename__ = "user_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_email = Column(String, unique=True, index=True, nullable=False)
    access_token = Column(String, nullable=False)
    refresh_token = Column(String, nullable=True)
    expiry = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())