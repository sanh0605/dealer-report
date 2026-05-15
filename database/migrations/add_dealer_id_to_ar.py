"""
Migration: Add dealer_id column to accounts_receivable_ledger table

This migration adds the dealer_id column to allow direct queries
for AR outstanding by dealer without joining with sale_records.
"""
import sqlite3
import os

def migrate_database(db_path: str) -> None:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            ALTER TABLE accounts_receivable_ledger
            ADD COLUMN dealer_id TEXT
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS ix_accounts_receivable_ledger_dealer_id
            ON accounts_receivable_ledger(dealer_id)
        """)
        conn.commit()
        print("Migration successful: Added dealer_id column to accounts_receivable_ledger")
    except sqlite3.Error as e:
        conn.rollback()
        print(f"Migration failed: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    db_path = os.getenv("DATABASE_URL", "sqlite:///./dealer_report.db").replace("sqlite:///", "")
    migrate_database(db_path)
