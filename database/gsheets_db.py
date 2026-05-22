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
        # Use the underlying gspread spreadsheet object
        # st-gsheets-connection stores it in _spreadsheet
        if hasattr(conn, "_spreadsheet"):
            return [ws.title for ws in conn._spreadsheet.worksheets()]
        # Fallback to internal client if _spreadsheet is not yet initialized
        spreadsheet = conn.client.open_by_key(conn._spreadsheet_id)
        return [ws.title for ws in spreadsheet.worksheets()]
    except Exception as e:
        # st.warning(f"Metadata error: {e}")
        return []

def read_sheet(worksheet_name: str, ttl: int = 600) -> pd.DataFrame:
    """Read a worksheet and return as a DataFrame"""
    conn = get_connection()
    ws_name = WORKSHEETS.get(worksheet_name, worksheet_name)
    
    try:
        df = conn.read(worksheet=ws_name, ttl=ttl)
        # Drop completely empty rows
        df = df.dropna(how="all")
        return df
    except Exception:
        return pd.DataFrame()

def update_sheet(worksheet_name: str, df: pd.DataFrame):
    """Overwrite a worksheet with a new DataFrame"""
    conn = get_connection()
    ws_name = WORKSHEETS.get(worksheet_name, worksheet_name)
    
    try:
        existing_ws = get_existing_worksheets(conn)
            
        if ws_name in existing_ws:
            conn.update(worksheet=ws_name, data=df)
        else:
            conn.create(worksheet=ws_name, data=df)
            
        st.cache_data.clear()
    except Exception as e:
        st.error(f"Error updating worksheet '{ws_name}': {e}")

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
    conn = get_connection()
    
    schema = {
        "users": ["id", "username", "password_hash", "role", "display_name", "created_at"],
        "audit_logs": ["timestamp", "username", "action_type", "details"],
        "visit_logs": ["id", "date", "staff_name", "dealer_id", "visit_result", "purpose"],
        "lost_sales": ["id", "date", "staff_name", "dealer_id", "item_id", "lost_volume", "lost_revenue"]
    }
    
    existing_ws = get_existing_worksheets(conn)

    # We check for 'users' sheet specifically to decide if we should run init
    if WORKSHEETS["users"] not in existing_ws:
        st.info("Initializing Google Sheets database structure...")
        for ws_key, headers in schema.items():
            ws_name = WORKSHEETS[ws_key]
            if ws_name not in existing_ws:
                df_init = pd.DataFrame(columns=headers)
                try:
                    conn.create(worksheet=ws_name, data=df_init)
                    st.write(f"✅ Created worksheet: {ws_name}")
                except Exception as e:
                    # If create fails, maybe it already exists and metadata check failed
                    st.error(f"Failed to create {ws_name}: {e}")
        st.success("Database structure initialization complete.")
        st.cache_data.clear()
