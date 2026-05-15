import pandas as pd
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Base, SaleRecord
from services.upload_service import upsert_dataframe

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_sale_records_aggregation(db_session):
    # Data with duplicate (order_id, item_id, date_transfer)
    data = [
        {
            "order_id": "ORD1",
            "item_id": "ITEM1",
            "date_transfer": "2026-05-01",
            "sales_revenue": 1000,
            "sales_volume": 1,
            "cost_of_goods": 800,
            "total_price_standard": 1000
        },
        {
            "order_id": "ORD1",
            "item_id": "ITEM1",
            "date_transfer": "2026-05-01",
            "sales_revenue": -1000,
            "sales_volume": -1,
            "cost_of_goods": -800,
            "total_price_standard": -1000
        },
        {
            "order_id": "ORD1",
            "item_id": "ITEM1",
            "date_transfer": "2026-05-01",
            "sales_revenue": 500,
            "sales_volume": 1,
            "cost_of_goods": 400,
            "total_price_standard": 500
        }
    ]
    df = pd.DataFrame(data)
    
    # Upsert
    upsert_dataframe(db_session, df, "sale_records")
    
    # Check DB
    records = db_session.query(SaleRecord).all()
    assert len(records) == 1
    assert records[0].sales_revenue == 500
    assert records[0].sales_volume == 1

def test_sale_records_different_dates(db_session):
    # Data with different dates - should remain separate rows with updated PK
    data = [
        {
            "order_id": "ORD1",
            "item_id": "ITEM1",
            "date_transfer": "2026-05-01",
            "sales_revenue": 1000,
            "sales_volume": 1
        },
        {
            "order_id": "ORD1",
            "item_id": "ITEM1",
            "date_transfer": "2026-05-02",
            "sales_revenue": -1000,
            "sales_volume": -1
        }
    ]
    df = pd.DataFrame(data)
    
    # Upsert
    upsert_dataframe(db_session, df, "sale_records")
    
    # Check DB
    records = db_session.query(SaleRecord).all()
    assert len(records) == 2
    
    # Sum in DB
    total_rev = sum(r.sales_revenue for r in records)
    assert total_rev == 0
