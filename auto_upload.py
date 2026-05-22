import os
import pandas as pd
from database.session import get_db
from services.upload_service import upsert_dataframe

def seed_sample_data():
    db = get_db()
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
                
                # Normalize columns like the UI does
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
                
                count = upsert_dataframe(db, df, table_name)
                print(f"Successfully loaded {count} rows into {table_name}.")
            else:
                print(f"File not found: {filepath}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_sample_data()
