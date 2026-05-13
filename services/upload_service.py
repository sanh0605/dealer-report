import io
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from config import REQUIRED_COLUMNS, BRAND_GROUP_MAP, SUB_REGION_TO_REGION
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


def load_file(file_bytes: bytes, filename: str) -> pd.DataFrame:
    buf = io.BytesIO(file_bytes)
    if filename.endswith(".csv"):
        return pd.read_csv(buf, dtype=str)
    return pd.read_excel(buf, dtype=str)


def validate_columns(df: pd.DataFrame, table_name: str) -> list[str]:
    required = REQUIRED_COLUMNS.get(table_name, [])
    return [c for c in required if c not in df.columns]


def _apply_auto_assignments(df: pd.DataFrame, table_name: str) -> pd.DataFrame:
    df = df.copy()
    if table_name == "product_master" and "brand" in df.columns:
        df["brand_group"] = df["brand"].map(BRAND_GROUP_MAP).fillna("Other")
    if table_name == "dealer_master" and "sub_region" in df.columns:
        df["region"] = df["sub_region"].map(SUB_REGION_TO_REGION).fillna("Unknown")
    return df


def upsert_dataframe(db: Session, df: pd.DataFrame, table_name: str) -> int:
    model = _TABLE_MODEL_MAP[table_name]
    df = _apply_auto_assignments(df, table_name)
    mapper = model.__mapper__
    cols = {c.key for c in mapper.columns}
    df = df[[c for c in df.columns if c in cols]]
    df = df.where(pd.notna(df), None)
    records = df.to_dict(orient="records")
    if not records:
        return 0
    stmt = sqlite_insert(model.__table__).values(records)
    pk_cols = [c.key for c in mapper.primary_key]
    update_cols = {c: stmt.excluded[c] for c in df.columns if c not in pk_cols}
    stmt = stmt.on_conflict_do_update(index_elements=pk_cols, set_=update_cols)
    db.execute(stmt)
    db.commit()
    return len(records)
