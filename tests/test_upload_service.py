import pytest
import pandas as pd
import io
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from config import REQUIRED_COLUMNS, PRODUCT_GROUP_MAP, SUB_REGION_TO_REGION
from database.models import (
    SaleRecord, AccountsReceivableLedger, ProductMaster, DealerMaster,
    SalesTarget, InventoryStatus, IncomingShipment, OpenOrder,
    FieldVisitPlan,
)

_TABLE_MODEL_MAP = {
    "sale_records": SaleRecord,
    "accounts_receivable_ledger": AccountsReceivableLedger,
    "product_master": ProductMaster,
    "dealer_master": DealerMaster,
    "sales_targets": SalesTarget,
    "inventory_status": InventoryStatus,
    "incoming_shipments": IncomingShipment,
    "open_orders": OpenOrder,
    "field_visit_plans": FieldVisitPlan,
}


@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:")
    from database.models import Base
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def sample_csv():
    return b"order_id,order_date,dealer_id,item_id,sales_volume\nORD001,2026-01-15,DL001,IT001,100"


@pytest.fixture
def sample_excel():
    df = pd.DataFrame({
        "order_id": ["ORD001"],
        "order_date": ["2026-01-15"],
        "dealer_id": ["DL001"],
        "item_id": ["IT001"],
        "sales_volume": [100]
    })
    buf = io.BytesIO()
    df.to_excel(buf, index=False)
    buf.seek(0)
    return buf.read()


def test_load_file_csv(sample_csv):
    from services.upload_service import load_file

    df = load_file(sample_csv, "test.csv")
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 1
    assert df.iloc[0]["order_id"] == "ORD001"


def test_load_file_excel(sample_excel):
    from services.upload_service import load_file

    df = load_file(sample_excel, "test.xlsx")
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 1
    assert df.iloc[0]["order_id"] == "ORD001"


def test_validate_columns_missing():
    from services.upload_service import validate_columns

    df = pd.DataFrame({
        "order_id": ["ORD001"],
        "order_date": ["2026-01-15"]
    })

    missing = validate_columns(df, "sale_records")
    expected = ["date_transfer", "dealer_id", "item_id", "salesperson",
                "sale_admin", "channel_name", "sales_volume",
                "unit_price_standard", "total_price_standard",
                "sales_revenue", "cost_of_goods"]
    assert missing == expected


def test_validate_columns_all_present():
    from services.upload_service import validate_columns

    required = REQUIRED_COLUMNS["sale_records"]
    df = pd.DataFrame({col: ["test"] for col in required})

    missing = validate_columns(df, "sale_records")
    assert missing == []


def test_upsert_dataframe_insert(test_db):
    from services.upload_service import upsert_dataframe

    df = pd.DataFrame({
        "order_id": ["ORD001", "ORD002"],
        "order_date": ["2026-01-15", "2026-01-16"],
        "date_transfer": ["2026-01-15", "2026-01-16"],
        "dealer_id": ["DL001", "DL002"],
        "item_id": ["IT001", "IT002"],
        "salesperson": ["John", "Jane"],
        "sale_admin": ["Admin1", "Admin2"],
        "channel_name": ["Direct", "Indirect"],
        "sales_volume": [100, 200],
        "unit_price_standard": [10.0, 20.0],
        "total_price_standard": [1000.0, 4000.0],
        "sales_revenue": [1000.0, 4000.0],
        "cost_of_goods": [500.0, 2000.0],
    })

    count = upsert_dataframe(test_db, df, "sale_records")
    assert count == 2

    records = test_db.query(SaleRecord).all()
    assert len(records) == 2
    assert records[0].order_id == "ORD001"
    assert records[1].order_id == "ORD002"


def test_upsert_dataframe_update(test_db):
    from services.upload_service import upsert_dataframe

    df1 = pd.DataFrame({
        "order_id": ["ORD001"],
        "order_date": ["2026-01-15"],
        "date_transfer": ["2026-01-15"],
        "dealer_id": ["DL001"],
        "item_id": ["IT001"],
        "salesperson": ["John"],
        "sale_admin": ["Admin1"],
        "channel_name": ["Direct"],
        "sales_volume": [100],
        "unit_price_standard": [10.0],
        "total_price_standard": [1000.0],
        "sales_revenue": [1000.0],
        "cost_of_goods": [500.0],
    })

    upsert_dataframe(test_db, df1, "sale_records")

    df2 = pd.DataFrame({
        "order_id": ["ORD001"],
        "order_date": ["2026-01-15"],
        "date_transfer": ["2026-01-15"],
        "dealer_id": ["DL001"],
        "item_id": ["IT001"],
        "salesperson": ["John"],
        "sale_admin": ["Admin1"],
        "channel_name": ["Direct"],
        "sales_volume": [150],
        "unit_price_standard": [10.0],
        "total_price_standard": [1500.0],
        "sales_revenue": [1500.0],
        "cost_of_goods": [750.0],
    })

    count = upsert_dataframe(test_db, df2, "sale_records")
    assert count == 1

    records = test_db.query(SaleRecord).all()
    assert len(records) == 1
    assert records[0].sales_volume == 150
    assert records[0].total_price_standard == 1500.0
