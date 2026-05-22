import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- CONFIGURATION ---
# Worksheet names used in the app
WORKSHEETS = {
    "users": "users",
    "dealer_master": "dealer_master",
    "product_master": "product_master",
    "sale_records": "sale_records",
    "accounts_receivable_ledger": "accounts_receivable_ledger",
    "open_orders": "open_orders",
    "inventory_status": "inventory_status",
    "sales_targets": "sales_targets",
    "field_visit_plans": "field_visit_plans",
    "visit_logs": "visit_logs",
    "lost_sales": "lost_sales",
    "audit_logs": "audit_logs"
}

def get_connection():
    """Create and return a GSheetsConnection"""
    try:
        return st.connection("gsheets", type=GSheetsConnection)
    except Exception as e:
        st.error(f"Error connecting to Google Sheets: {e}")
        st.info("Check if .streamlit/secrets.toml is configured correctly.")
        st.stop()

def read_sheet(worksheet_name: str, ttl: int = 600) -> pd.DataFrame:
    """Read a worksheet and return as a DataFrame"""
    conn = get_connection()
    # Ensure worksheet_name is one of the keys in WORKSHEETS or a direct name
    ws_name = WORKSHEETS.get(worksheet_name, worksheet_name)
    
    try:
        df = conn.read(worksheet=ws_name, ttl=ttl)
        # Drop completely empty rows
        df = df.dropna(how="all")
        return df
    except Exception as e:
        # If worksheet doesn't exist, return empty DF with expected columns if known
        # or just an empty DF
        # st.warning(f"Could not read worksheet '{ws_name}': {e}")
        return pd.DataFrame()

def update_sheet(worksheet_name: str, df: pd.DataFrame):
    """Overwrite a worksheet with a new DataFrame"""
    conn = get_connection()
    ws_name = WORKSHEETS.get(worksheet_name, worksheet_name)
    
    try:
        conn.update(worksheet=ws_name, data=df)
        st.cache_data.clear() # Clear cache so next read gets fresh data
    except Exception as e:
        st.error(f"Error updating worksheet '{ws_name}': {e}")

def append_row(worksheet_name: str, row_dict: dict):
    """Append a single row to a worksheet"""
    # Google Sheets API via st-gsheets doesn't have a direct 'append' 
    # that is efficient, so we read, concat, and update.
    # For high-volume logs, this might be slow, but it's the standard way for this library.
    df = read_sheet(worksheet_name, ttl=0) # Read without cache
    new_row = pd.DataFrame([row_dict])
    
    if df.empty:
        updated_df = new_row
    else:
        updated_df = pd.concat([df, new_row], ignore_index=True)
    
    update_sheet(worksheet_name, updated_df)

def init_sheets():
    """Initialize necessary worksheets with headers if they don't exist"""
    # This is a bit heavy for every app start, but good for first run.
    # We'll check if 'users' exists; if not, we assume we need to init.
    conn = get_connection()
    
    # Required headers for core tables
    schema = {
        "users": ["id", "username", "password_hash", "role", "display_name", "created_at"],
        "audit_logs": ["timestamp", "username", "action_type", "details"],
        "visit_logs": ["id", "date", "staff_name", "dealer_id", "visit_result", "purpose"],
        "lost_sales": ["id", "date", "staff_name", "dealer_id", "item_id", "lost_volume", "lost_revenue"]
    }
    
    # Try reading 'users'. If it fails, create basic structure.
    try:
        df = conn.read(worksheet=WORKSHEETS["users"], ttl=0)
    except Exception:
        st.info("Initializing Google Sheets database structure...")
        for ws, headers in schema.items():
            df_init = pd.DataFrame(columns=headers)
            update_sheet(ws, df_init)
        st.success("Database structure initialized.")
