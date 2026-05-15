"""
Migration: Add order_date column to accounts_receivable_ledger table

This migration adds the order_date column as requested by the user.
"""
import sqlite3
import os

def migrate_database(db_path: str) -> None:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            ALTER TABLE accounts_receivable_ledger
            ADD COLUMN order_date DATE
        """)
        conn.commit()
        print("Migration successful: Added order_date column to accounts_receivable_ledger")
    except sqlite3.Error as e:
        conn.rollback()
        print(f"Migration failed: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    db_path = os.getenv("DATABASE_URL", "sqlite:///./dealer_report.db").replace("sqlite:///", "")
    migrate_database(db_path)
