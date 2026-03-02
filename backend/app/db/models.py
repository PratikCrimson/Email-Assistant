from sqlalchemy import Column, Integer, Text, TIMESTAMP, UniqueConstraint, DateTime, String, Boolean
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


class UserSyncState(Base):
    __tablename__ = "user_sync_states"

    id = Column(Integer, primary_key=True, index=True)
    user_email = Column(String, unique=True, index=True, nullable=False)
    running = Column(Boolean, nullable=False, default=False)
    total = Column(Integer, nullable=False, default=0)
    processed = Column(Integer, nullable=False, default=0)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    last_synced_at = Column(DateTime, nullable=True)
    sync_after_ts = Column(DateTime, nullable=True)
    next_page_token = Column(Text, nullable=True)
    has_more = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
