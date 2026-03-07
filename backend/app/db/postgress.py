import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.models import Base
from dotenv import load_dotenv
load_dotenv()

database_url = os.getenv("DATABASE_URL")
sql_echo = os.getenv("SQL_ECHO", "false").strip().lower() == "true"

engine = create_engine(database_url, echo=sql_echo, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_pg():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
