"""
Data Upload page for Admin users
Allows uploading CSV/Excel files for various data tables
"""
import streamlit as st
from auth.service import require_role
from database.session import get_db
from services.upload_service import load_file, validate_columns, upsert_dataframe

st.set_page_config(page_title="Upload Data", layout="wide")

if "user" not in st.session_state:
    st.error("Please sign in from the Home page.")
    st.stop()

user = st.session_state["user"]

try:
    require_role(type("U", (), user)(), ["Admin"])
except PermissionError:
    st.error("Admin access required to upload data.")
    st.stop()

TABLES = [
    "sale_records", "accounts_receivable_ledger", "product_master",
    "dealer_master", "sales_targets", "inventory_status",
    "incoming_shipments", "open_orders", "field_visit_plans",
]

st.title("Data Upload")
st.caption("Upload CSV or Excel files for each data table. Existing records are updated, new records are inserted.")

table_name = st.selectbox("Select table to upload", TABLES)

uploaded = st.file_uploader(f"Upload file for **{table_name}**", type=["csv", "xlsx", "xls"])

if uploaded:
    df = load_file(uploaded.read(), uploaded.name)
    st.subheader("Preview (first 5 rows)")
    st.dataframe(df.head(5))
    missing = validate_columns(df, table_name)
    if missing:
        st.error(f"Missing required columns: {', '.join(missing)}")
    else:
        st.success(f"All required columns present. {len(df)} rows ready to upload.")
        if st.button("Confirm Upload"):
            db = get_db()
            try:
                count = upsert_dataframe(db, df, table_name)
                st.success(f"Uploaded {count} rows to **{table_name}**.")
            except Exception as e:
                st.error(f"Upload failed: {e}")
            finally:
                db.close()
