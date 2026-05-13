import pytest
from sqlalchemy import create_engine, inspect
from database.models import Base

@pytest.fixture
def engine():
    eng = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    return eng

def test_all_tables_created(engine):
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    expected = [
        "sale_records", "accounts_receivable_ledger", "product_master",
        "dealer_master", "sales_targets", "inventory_status",
        "incoming_shipments", "open_orders", "lost_sales_entry",
        "field_visit_plans", "visit_logs", "users", "audit_logs",
    ]
    for t in expected:
        assert t in tables, f"Missing table: {t}"

def test_sale_records_columns(engine):
    inspector = inspect(engine)
    cols = {c["name"] for c in inspector.get_columns("sale_records")}
    assert "order_id" in cols
    assert "sales_revenue" in cols
    assert "cost_of_goods" in cols
    assert "unit_price_standard" in cols
