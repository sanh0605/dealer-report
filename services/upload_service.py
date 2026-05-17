import io
import pandas as pd
from datetime import datetime, date
from sqlalchemy.orm import Session
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.types import Date, DateTime
from config import REQUIRED_COLUMNS
from database.models import (
    SaleRecord, AccountsReceivableLedger, ProductMaster, DealerMaster,
    SalesTarget, InventoryStatus, IncomingShipment, OpenOrder,
    FieldVisitPlan, VisitLog
)

# --- File Utilities ---

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

# --- Ingestion Framework ---

class BaseIngestor:
    def __init__(self, db: Session, model):
        self.db = db
        self.model = model
        self.mapper = model.__mapper__
        self.cols = {c.key for c in self.mapper.columns}
        self.pk_cols = [c.key for c in self.mapper.primary_key]

    def _convert_dates(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        for col in df.columns:
            if col not in self.cols:
                continue
            col_type = self.mapper.columns[col].type
            if isinstance(col_type, (Date, DateTime)):
                df[col] = pd.to_datetime(df[col], dayfirst=True, errors="coerce")
                if isinstance(col_type, Date):
                    df[col] = df[col].dt.date
        return df

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Override to add custom business logic before upsert"""
        return df

    def process(self, df: pd.DataFrame) -> pd.DataFrame:
        df = self.transform(df)
        df = self._convert_dates(df)
        # Filter to model columns
        df = df[[c for c in df.columns if c in self.cols]]
        # Drop rows missing PK
        existing_pk_cols = [c for c in self.pk_cols if c in df.columns]
        if existing_pk_cols:
            df = df.dropna(subset=existing_pk_cols)
        return df

    def upsert(self, df: pd.DataFrame) -> int:
        df = self.process(df)
        df = df.where(pd.notna(df), None)
        records = df.to_dict(orient="records")
        if not records:
            return 0
            
        chunk_size = 50
        for i in range(0, len(records), chunk_size):
            chunk = records[i:i + chunk_size]
            stmt = sqlite_insert(self.model.__table__).values(chunk)
            update_cols = {c: stmt.excluded[c] for c in df.columns if c not in self.pk_cols}
            if update_cols:
                stmt = stmt.on_conflict_do_update(index_elements=self.pk_cols, set_=update_cols)
            else:
                stmt = stmt.on_conflict_do_nothing(index_elements=self.pk_cols)
            self.db.execute(stmt)
            
        self.db.commit()
        return len(records)

class SalesIngestor(BaseIngestor):
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        numeric_cols = ["sales_volume", "sales_revenue", "cost_of_goods", "total_price_standard"]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
        
        # Aggregation logic for sale_records
        agg_dict = {}
        for c in df.columns:
            if c in self.pk_cols:
                continue
            if c in numeric_cols:
                agg_dict[c] = "sum"
            elif c == "order_date":
                agg_dict[c] = "max"
            else:
                agg_dict[c] = "first"
        
        return df.groupby(self.pk_cols).agg(agg_dict).reset_index()

class ProductIngestor(BaseIngestor):
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        def get_brand_group(row):
            cat = str(row.get("category", "")).strip().lower()
            brand = str(row.get("brand", "")).strip().lower()
            subcat = str(row.get("subcategory", "")).strip().lower()
            if cat == "gears": return "gears"
            if cat == "bikes":
                if any(x in subcat for x in ["e-bikes", "e-scooters"]): return "others"
                if any(x in brand for x in ["jeep", "hitasa"]): return "others"
                if any(x in brand for x in ["giant", "liv", "momentum"]): return "giant bikes"
                if "java" in brand: return "java bikes"
                return "oem bikes"
            return "others"
        
        df = df.copy()
        df["brand_group"] = df.apply(get_brand_group, axis=1)
        return df

class DealerIngestor(BaseIngestor):
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        def get_region(sub_reg):
            sr = str(sub_reg).upper()
            if "MN" in sr: return "Miền Nam"
            if "MB" in sr: return "Miền Bắc"
            if "MT" in sr: return "Miền Trung"
            return "Unknown"
        
        if "sub_region" in df.columns:
            df = df.copy()
            df["region"] = df["sub_region"].apply(get_region)
        return df

# --- Ingestion Registry ---

_INGESTOR_MAP = {
    "sale_records": (SaleRecord, SalesIngestor),
    "product_master": (ProductMaster, ProductIngestor),
    "dealer_master": (DealerMaster, DealerIngestor),
    "accounts_receivable_ledger": (AccountsReceivableLedger, BaseIngestor),
    "sales_targets": (SalesTarget, BaseIngestor),
    "inventory_status": (InventoryStatus, BaseIngestor),
    "incoming_shipments": (IncomingShipment, BaseIngestor),
    "open_orders": (OpenOrder, BaseIngestor),
    "field_visit_plans": (FieldVisitPlan, BaseIngestor),
    "visit_logs": (VisitLog, BaseIngestor),
}

def upsert_dataframe(db: Session, df: pd.DataFrame, table_name: str) -> int:
    if table_name not in _INGESTOR_MAP:
        raise ValueError(f"No ingestor registered for table: {table_name}")
    
    model_class, ingestor_class = _INGESTOR_MAP[table_name]
    ingestor = ingestor_class(db, model_class)
    return ingestor.upsert(df)
