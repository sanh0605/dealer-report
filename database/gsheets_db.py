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

def get_existing_worksheets(conn):
    """Robustly get existing worksheet names"""
    try:
        # st-gsheets-connection makes it hard to get worksheet list 
        # without potentially failing on different connection modes.
        # We try the most direct gspread method.
        if hasattr(conn, "client"):
            spreadsheet = conn.client.open_by_key(conn._spreadsheet_id)
            return [ws.title for ws in spreadsheet.worksheets()]
    except:
        pass
    return []

# Known ID columns that must stay as strings
_ID_COLUMNS = ["dealer_id", "item_id", "order_id", "id", "product_id", "shipment_id"]

def read_sheet(worksheet_name: str, ttl: int = 600) -> pd.DataFrame:
    """Read a worksheet and return as a DataFrame"""
    conn = get_connection()
    ws_name = WORKSHEETS.get(worksheet_name, worksheet_name)
    
    try:
        df = conn.read(worksheet=ws_name, ttl=ttl)
        # Drop completely empty rows
        df = df.dropna(how="all")
        
        # Enforce string types for ID columns
        if not df.empty:
            for col in _ID_COLUMNS:
                if col in df.columns:
                    df[col] = df[col].astype(str).str.strip().str.replace(r'\.0$', '', regex=True).str.strip()
                    df[col] = df[col].replace('nan', '')
                    
        return df
    except Exception:
        return pd.DataFrame()

def update_sheet(worksheet_name: str, df: pd.DataFrame):
    """Overwrite a worksheet with a new DataFrame"""
    conn = get_connection()
    ws_name = WORKSHEETS.get(worksheet_name, worksheet_name)
    
    try:
        conn.update(worksheet=ws_name, data=df)
        st.cache_data.clear()
    except Exception as e:
        # If update fails, maybe it doesn't exist? Try create.
        if "not found" in str(e).lower() or "already exists" not in str(e).lower():
            try:
                conn.create(worksheet=ws_name, data=df)
                st.cache_data.clear()
            except:
                st.error(f"Error updating/creating worksheet '{ws_name}': {e}")

def append_row(worksheet_name: str, row_dict: dict):
    """Append a single row to a worksheet"""
    df = read_sheet(worksheet_name, ttl=0)
    new_row = pd.DataFrame([row_dict])
    
    if df.empty:
        updated_df = new_row
    else:
        updated_df = pd.concat([df, new_row], ignore_index=True)
    
    update_sheet(worksheet_name, updated_df)

def init_sheets():
    """Initialize necessary worksheets with headers if they don't exist"""
    # This function is now silent to avoid cluttering the UI with 'already exists' messages
    conn = get_connection()
    
    schema = {
        "users": ["id", "username", "password_hash", "role", "display_name", "created_at"],
        "audit_logs": ["timestamp", "username", "action_type", "details"],
        "visit_logs": ["id", "date", "staff_name", "dealer_id", "visit_result", "purpose"],
        "lost_sales": ["id", "date", "staff_name", "dealer_id", "item_id", "lost_volume", "lost_revenue"]
    }
    
    # Try reading the users sheet. If it works, we assume DB is initialized.
    try:
        df = conn.read(worksheet=WORKSHEETS["users"], ttl=0)
        if not df.empty or len(df.columns) > 0:
            return # Already exists and has structure
    except:
        # If read fails, attempt to create the schema
        for ws_key, headers in schema.items():
            ws_name = WORKSHEETS[ws_key]
            df_init = pd.DataFrame(columns=headers)
            try:
                conn.create(worksheet=ws_name, data=df_init)
            except Exception as e:
                # Silently ignore 'already exists' errors
                if "already exists" not in str(e).lower():
                    st.error(f"Failed to initialize {ws_name}: {e}")
        st.cache_data.clear()
