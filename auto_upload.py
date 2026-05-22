import os
import pandas as pd
import streamlit as st
from services.upload_service import normalize_columns, upsert_dataframe
from services.identity import create_user
from database.gsheets_db import init_sheets, read_sheet

def seed_sample_data():
    print("Starting data seeding to Google Sheets...")
    
    # Initialize sheets first
    init_sheets()
    
    data_dir = "sample_data"
    
    # Map filenames to table names
    file_to_table = {
        "dealer_master.xlsx": "dealer_master",
        "product_master.xlsx": "product_master",
        "sale_records.xlsx": "sale_records",
        "accounts_receivable_ledger.xlsx": "accounts_receivable_ledger",
        "open_orders.xlsx": "open_orders",
        "inventory_status.xlsx": "inventory_status"
    }

    try:
        for filename, table_name in file_to_table.items():
            filepath = os.path.join(data_dir, filename)
            if os.path.exists(filepath):
                print(f"Loading {filename} into {table_name}...")
                df = pd.read_excel(filepath, dtype=str)
                df = normalize_columns(df)
                
                # No dummy_db needed for GSheets
                count = upsert_dataframe(None, df, table_name)
                print(f"Successfully loaded {count} rows into {table_name}.")
            else:
                print(f"File not found: {filepath}")
                
        # Create default admin user if no users exist
        users_df = read_sheet("users", ttl=0)
        if users_df.empty:
            print("Creating default admin user...")
            create_user(None, "admin", "admin1234", "Admin", "System Admin", "System")
            print("Default admin user created: admin / admin1234")
            
    except Exception as e:
        print(f"Error during seeding: {e}")

if __name__ == "__main__":
    # Note: To run this locally, you need Streamlit secrets set up 
    # and you might need to mock streamlit for some parts or run within a streamlit context.
    # Since upsert_dataframe uses st.connection, this script should ideally be run
    # via a dedicated setup page in the app or with extreme care locally.
    seed_sample_data()
