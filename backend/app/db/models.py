from sqlalchemy import Column, Integer, Text, TIMESTAMP , UniqueConstraint
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector



Base = declarative_base()

class Email(Base):
    __tablename__ = "emails"

    __table_args__ = (
        UniqueConstraint("user_email" , "email_id" , name ="uq_user_email_msg"),
    )

    id = Column(Integer, primary_key=True)
    user_email = Column(Text , index=True)
    email_id = Column(Text, unique=True, index=True)
    thread_id = Column(Text)
    subject = Column(Text)
    sender = Column(Text)
    date = Column(TIMESTAMP)
    category = Column(Text)
    cleaned_body = Column(Text)
    embedding = Column(Vector(384))
    indexed_at = Column(TIMESTAMP, server_default=func.now())