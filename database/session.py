import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv
from database.models import Base

load_dotenv()

_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./dealer_report.db")

engine = create_engine(
    _DATABASE_URL,
    connect_args={"check_same_thread": False},  # required for SQLite + Streamlit
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

def init_db() -> None:
    Base.metadata.create_all(bind=engine)

def get_db() -> Session:
    return SessionLocal()
