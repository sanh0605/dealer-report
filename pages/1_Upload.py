"""
Data Upload page for Admin users
Allows uploading CSV/Excel files for various data tables
"""
import streamlit as st
import pandas as pd
import io
from auth.service import require_role
from database.session import get_db
from services.upload_service import load_file, validate_columns, upsert_dataframe
from components.ui_utils import show_centered_loader
from config import REQUIRED_COLUMNS

# Show loading animation
PageLoader = show_centered_loader()

st.set_page_config(page_title="Upload Data", layout="wide")

try:
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
        "visit_logs",
    ]

    st.title("Data Upload")
    st.caption("Upload CSV or Excel files for each data table. Existing records are updated, new records are inserted.")

    table_name = st.selectbox("Select table to upload", TABLES)

    # Download template section
    cols = REQUIRED_COLUMNS.get(table_name, [])
    if cols:
        template_df = pd.DataFrame(columns=cols)
        csv_buffer = io.StringIO()
        template_df.to_csv(csv_buffer, index=False)
        st.download_button(
            label=f"📥 Download template for {table_name}",
            data=csv_buffer.getvalue(),
            file_name=f"template_{table_name}.csv",
            mime="text/csv",
        )

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

finally:
    PageLoader.empty()
