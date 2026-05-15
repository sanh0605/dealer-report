import io
import pandas as pd
from datetime import datetime, date
from sqlalchemy.orm import Session
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.types import Date, DateTime
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


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    clean_cols = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
    aliases = {
        "refund_amout": "refund_amount",
        "deduction_amout": "deduction_amount",
        "paid_amout": "paid_amount",
        "bussiness_name": "business_name",
        "subregion": "sub_region",
        "item": "item_name",
        "open_quantity": "open_qty",
        "sale_person": "salesperson",
        "quantity": "sales_volume",
    }
    df.columns = [aliases.get(c, c) for c in clean_cols]
    return df

def load_file(file_bytes: bytes, filename: str) -> pd.DataFrame:
    buf = io.BytesIO(file_bytes)
    if filename.endswith(".csv"):
        df = pd.read_csv(buf, dtype=str)
    else:
        df = pd.read_excel(buf, dtype=str)
    return normalize_columns(df)


def validate_columns(df: pd.DataFrame, table_name: str) -> list[str]:
    required = REQUIRED_COLUMNS.get(table_name, [])
    return [c for c in required if c not in df.columns]


def _convert_date_columns(df: pd.DataFrame, model) -> pd.DataFrame:
    df = df.copy()
    for col in df.columns:
        if col not in model.__mapper__.columns:
            continue
        col_type = model.__mapper__.columns[col].type
        if isinstance(col_type, (Date, DateTime)):
            df[col] = pd.to_datetime(df[col], dayfirst=True, errors="coerce")
            if isinstance(col_type, Date):
                df[col] = df[col].dt.date
    return df


def _apply_auto_assignments(df: pd.DataFrame, table_name: str) -> pd.DataFrame:
    df = df.copy()
    if table_name == "product_master":
        def get_brand_group(row):
            cat = str(row.get("category", "")).strip().lower()
            brand = str(row.get("brand", "")).strip().lower()
            subcat = str(row.get("subcategory", "")).strip().lower()
            
            if cat == "gears":
                return "gears"
            
            if cat == "bikes":
                # Priority 1: E-Bikes/Scooters are always Others
                if any(x in subcat for x in ["e-bikes", "e-scooters"]):
                    return "others"
                # Priority 2: Jeep/Hitasa are always Others
                if any(x in brand for x in ["jeep", "hitasa"]):
                    return "others"
                # Priority 3: Giant Group
                if any(x in brand for x in ["giant", "liv", "momentum"]):
                    return "giant bikes"
                # Priority 4: Java
                if "java" in brand:
                    return "java bikes"
                # Priority 5: OEM
                return "oem bikes"
            
            return "others"
        
        df["brand_group"] = df.apply(get_brand_group, axis=1)
        
    if table_name == "dealer_master" and "sub_region" in df.columns:
        def get_region(sub_reg):
            sr = str(sub_reg).upper()
            if "MN" in sr: return "Miền Nam"
            if "MB" in sr: return "Miền Bắc"
            if "MT" in sr: return "Miền Trung"
            return "Unknown"
        
        df["region"] = df["sub_region"].apply(get_region)
        
    return df


def upsert_dataframe(db: Session, df: pd.DataFrame, table_name: str) -> int:
    model = _TABLE_MODEL_MAP[table_name]
    df = _apply_auto_assignments(df, table_name)
    df = _convert_date_columns(df, model)
    mapper = model.__mapper__
    cols = {c.key for c in mapper.columns}
    df = df[[c for c in df.columns if c in cols]]
    
    pk_cols = [c.key for c in mapper.primary_key]
    existing_pk_cols = [c for c in pk_cols if c in df.columns]
    if existing_pk_cols:
        df = df.dropna(subset=existing_pk_cols)
    
    df = df.where(pd.notna(df), None)
    records = df.to_dict(orient="records")
    if not records:
        return 0
        
    chunk_size = 50
    
    for i in range(0, len(records), chunk_size):
        chunk = records[i:i + chunk_size]
        stmt = sqlite_insert(model.__table__).values(chunk)
        update_cols = {c: stmt.excluded[c] for c in df.columns if c not in pk_cols}
        if update_cols:
            stmt = stmt.on_conflict_do_update(index_elements=pk_cols, set_=update_cols)
        else:
            stmt = stmt.on_conflict_do_nothing(index_elements=pk_cols)
        db.execute(stmt)
        
    db.commit()
    return len(records)
