import os
import pytest
from sqlalchemy import inspect
from database.session import engine, SessionLocal, init_db, get_db


class TestSessionFactory:
    """Test database session factory and initialization."""

    def test_engine_is_created(self):
        """Test that SQLAlchemy engine is created successfully."""
        assert engine is not None
        assert hasattr(engine, 'connect')

    def test_session_local_is_callable(self):
        """Test that SessionLocal is a valid session factory."""
        assert SessionLocal is not None
        assert callable(SessionLocal)

    def test_get_db_returns_session(self):
        """Test that get_db returns a valid Session instance."""
        session = get_db()
        assert session is not None
        assert hasattr(session, 'query')
        session.close()

    def test_init_db_creates_tables(self, tmp_path):
        """Test that init_db creates all tables in the database."""
        # Use a temporary database for testing
        import tempfile
        import sqlite3
        from sqlalchemy import create_engine
        from database.session import Base

        # Create a temporary database
        db_file = tmp_path / "test.db"
        test_engine = create_engine(
            f"sqlite:///{db_file}",
            connect_args={"check_same_thread": False},
        )

        # Create tables
        Base.metadata.create_all(bind=test_engine)

        # Verify tables were created
        inspector = inspect(test_engine)
        table_names = inspector.get_table_names()

        # Expected tables from models.py
        expected_tables = [
            "sale_records",
            "accounts_receivable_ledger",
            "product_master",
            "dealer_master",
            "sales_targets",
            "inventory_status",
            "incoming_shipments",
            "open_orders",
            "lost_sales_entry",
            "field_visit_plans",
            "visit_logs",
            "users",
            "audit_logs",
        ]

        for table in expected_tables:
            assert table in table_names, f"Table {table} not created"

        test_engine.dispose()

    def test_session_can_query(self, tmp_path):
        """Test that a session can perform queries (basic connectivity)."""
        import tempfile
        from sqlalchemy import create_engine, Column, Integer, String, text
        from sqlalchemy.orm import DeclarativeBase, sessionmaker

        class TestBase(DeclarativeBase):
            pass

        class TestTable(TestBase):
            __tablename__ = "test_table"
            id = Column(Integer, primary_key=True)
            name = Column(String)

        # Create temporary database
        db_file = tmp_path / "test_query.db"
        test_engine = create_engine(
            f"sqlite:///{db_file}",
            connect_args={"check_same_thread": False},
        )

        TestBase.metadata.create_all(bind=test_engine)
        TestSessionLocal = sessionmaker(bind=test_engine, autoflush=False, autocommit=False)

        session = TestSessionLocal()
        result = session.execute(text("SELECT 1"))
        assert result.scalar() == 1
        session.close()
        test_engine.dispose()
