import io
import pandas as pd
from datetime import datetime
from config import REQUIRED_COLUMNS
from database.gsheets_db import read_sheet, update_sheet

# --- PK Definition (replacing SQLAlchemy model info) ---
_TABLE_PKS = {
    "sale_records": ["order_id", "item_id"],
    "product_master": ["item_id"],
    "dealer_master": ["dealer_id"],
    "accounts_receivable_ledger": ["dealer_id", "order_id"],
    "sales_targets": ["month_year", "sub_region"],
    "inventory_status": ["item_id", "warehouse"],
    "incoming_shipments": ["shipment_id", "item_id"],
    "open_orders": ["order_id", "item_id"],
    "field_visit_plans": ["month_year", "staff_name", "dealer_id"],
    "visit_logs": ["id"],
    "users": ["id"],
    "lost_sales": ["id"]
}

# Known ID columns that must stay as strings
_ID_COLUMNS = ["dealer_id", "item_id", "order_id", "id", "product_id", "shipment_id"]

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
        "màu_sắc": "color",
        "kích_cỡ": "size",
        "màu": "color",
        "kích_thước": "size",
        "mã_sku": "item_id",
        "mã_hàng": "item_id",
        "tên_hàng": "item_name",
        "thương_hiệu": "brand",
        "dòng_xe": "model",
        "nhóm_sản_phẩm": "category",
        "mã_sản_phẩm": "product_id",
        "doanh_thu": "sales_revenue",
        "giá_vốn": "cost_of_goods",
        "số_lượng": "sales_volume",
        "mã_đơn_hàng": "order_id",
        "ngày_đơn_hàng": "order_date",
        "ngày_chuyển": "date_transfer",
        "mã_đối_tác": "dealer_id",
        "nhân_viên": "salesperson",
        "admin": "sale_admin",
        "kênh": "channel_name",
        "đơn_giá": "unit_price_standard",
        "thành_tiền": "total_price_standard",
        "internal_reference": "item_id",
        "brand/display_name": "brand",
        "model/display_name": "model",
        "product_template/display_name": "product",
        "display_name": "item_name",
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
    def __init__(self, table_name: str):
        self.table_name = table_name
        self.pk_cols = _TABLE_PKS.get(table_name, [])

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Override to add custom business logic before upsert"""
        for col in _ID_COLUMNS:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip().str.replace(r'\.0$', '', regex=True).str.strip()
                # If the string is 'nan', make it empty or actual NaN
                df[col] = df[col].replace('nan', '')
        return df

    def process(self, df: pd.DataFrame) -> pd.DataFrame:
        df = self.transform(df)
        # Drop rows missing PK
        if self.pk_cols:
            existing_pks = [c for c in self.pk_cols if c in df.columns]
            if existing_pks:
                df = df.dropna(subset=existing_pks)
        return df

    def upsert(self, df: pd.DataFrame) -> int:
        new_data = self.process(df)
        if new_data.empty:
            return 0
            
        # Read existing data from Google Sheets
        existing_df = read_sheet(self.table_name, ttl=0)
        
        if existing_df.empty:
            final_df = new_data
        else:
            # Concatenate
            final_df = pd.concat([existing_df, new_data], ignore_index=True)
            
            # Deduplicate based on PKs, keeping the last (newest) entry
            if self.pk_cols:
                final_df = final_df.drop_duplicates(subset=self.pk_cols, keep='last')
        
        # Write back to Google Sheets
        update_sheet(self.table_name, final_df)
        return len(new_data)

class SalesIngestor(BaseIngestor):
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        df = super().transform(df)
        numeric_cols = ["sales_volume", "sales_revenue", "cost_of_goods", "total_price_standard", "unit_price_standard"]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
        
        if "sales_volume" in df.columns:
            df["sales_volume"] = df["sales_volume"].astype(float).astype(int)
        
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
        df = super().transform(df)
        def get_product_group(row):
            cat = str(row.get("category", "")).strip().lower()
            brand = str(row.get("brand", "")).strip().lower()
            subcat = str(row.get("subcategory", "")).strip().lower()
            if cat == "gears":
                if brand == "maxxis": return "maxxis"
                return "gears"
            if cat == "bikes":
                if any(x in subcat for x in ["e-bikes", "e-scooters"]): return "others"
                if any(x in brand for x in ["jeep", "hitasa"]): return "oem bikes"
                if any(x in brand for x in ["giant", "liv", "momentum"]): return "giant bikes"
                if "java" in brand: return "java bikes"
                return "oem bikes"
            return "others"
        
        df = df.copy()
        df["product_group"] = df.apply(get_product_group, axis=1)
        return df

class DealerIngestor(BaseIngestor):
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        df = super().transform(df)
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
    "sale_records": SalesIngestor,
    "product_master": ProductIngestor,
    "dealer_master": DealerIngestor,
    "accounts_receivable_ledger": BaseIngestor,
    "sales_targets": BaseIngestor,
    "inventory_status": BaseIngestor,
    "incoming_shipments": BaseIngestor,
    "open_orders": BaseIngestor,
    "field_visit_plans": BaseIngestor,
    "visit_logs": BaseIngestor,
}

def upsert_dataframe(dummy_db, df: pd.DataFrame, table_name: str) -> int:
    # dummy_db is ignored
    if table_name not in _INGESTOR_MAP:
        ingestor = BaseIngestor(table_name)
    else:
        ingestor_class = _INGESTOR_MAP[table_name]
        ingestor = ingestor_class(table_name)
    
    return ingestor.upsert(df)
