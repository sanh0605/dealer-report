import os
from sqlalchemy import create_engine, text
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
    # Safely add columns to existing tables since create_all doesn't handle migrations
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE field_visit_plans ADD COLUMN purpose TEXT"))
            conn.commit()
        except Exception:
            pass # Column likely exists
            
        try:
            conn.execute(text("ALTER TABLE visit_logs ADD COLUMN purpose TEXT"))
            conn.commit()
        except Exception:
            pass # Column likely exists

def get_db() -> Session:
    return SessionLocal()
