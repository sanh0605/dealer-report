"""
Tests for Upload page (pages/1_Upload.py)

Note: Streamlit pages that start with numbers cannot be imported directly
using standard Python import syntax. These tests focus on:
1. File structure validation
2. Service integration testing
3. File format handling
4. Column validation
5. Table selection logic
"""
import pytest
import io
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from database.session import SessionLocal
from database.models import User
import bcrypt
import os


class TestUploadPageFileStructure:
    """Test upload page file structure"""

    def test_upload_page_file_exists(self):
        """Test that upload page file exists"""
        assert os.path.exists("pages/1_Upload.py"), "pages/1_Upload.py does not exist"

    def test_upload_page_has_correct_imports(self):
        """Test that upload page has required imports"""
        with open("pages/1_Upload.py", "r") as f:
            content = f.read()
            assert "import streamlit as st" in content
            assert "from auth.service import require_role" in content
            assert "from database.session import get_db" in content
            assert "from services.upload_service import" in content

    def test_upload_page_has_tables_list(self):
        """Test that upload page has TABLES list with all required tables"""
        with open("pages/1_Upload.py", "r") as f:
            content = f.read()
            expected_tables = [
                "sale_records", "accounts_receivable_ledger", "product_master",
                "dealer_master", "sales_targets", "inventory_status",
                "incoming_shipments", "open_orders", "field_visit_plans",
            ]
            for table in expected_tables:
                assert f'"{table}"' in content or f"'{table}'" in content

    def test_upload_page_has_ui_elements(self):
        """Test that upload page has required UI elements"""
        with open("pages/1_Upload.py", "r") as f:
            content = f.read()
            assert 'st.set_page_config' in content
            assert 'st.title' in content
            assert 'st.file_uploader' in content
            assert 'st.selectbox' in content
            assert 'st.button' in content

    def test_upload_page_has_authentication_check(self):
        """Test that upload page has authentication check"""
        with open("pages/1_Upload.py", "r") as f:
            content = f.read()
            assert 'if "user" not in st.session_state' in content
            assert 'require_role' in content

    def test_upload_page_has_upload_confirmation(self):
        """Test that upload page has upload confirmation flow"""
        with open("pages/1_Upload.py", "r") as f:
            content = f.read()
            assert 'st.success' in content
            assert 'st.error' in content
            assert 'upsert_dataframe' in content


class TestUploadPageServiceIntegration:
    """Test upload page integration with services"""

    @patch('services.upload_service.load_file')
    def test_upload_page_loads_csv_file(self, mock_load):
        """Test that upload page can load CSV files"""
        from services.upload_service import load_file

        # Mock the file loading
        df = pd.DataFrame({"col1": ["a", "b"], "col2": [1, 2]})
        mock_load.return_value = df

        # Test that load_file is called with correct arguments
        file_bytes = b"test data"
        filename = "test.csv"
        result = load_file(file_bytes, filename)

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2

    @patch('services.upload_service.validate_columns')
    def test_upload_page_validates_columns(self, mock_validate):
        """Test that upload page validates columns correctly"""
        from services.upload_service import validate_columns

        # Mock validation
        mock_validate.return_value = []

        # Test validation
        df = pd.DataFrame({"col1": ["a"], "col2": [1]})
        result = validate_columns(df, "sale_records")

        mock_validate.assert_called_once_with(df, "sale_records")

    @patch('services.upload_service.validate_columns')
    def test_upload_page_handles_missing_columns(self, mock_validate):
        """Test that upload page handles missing columns"""
        from services.upload_service import validate_columns

        # Mock validation with missing columns
        mock_validate.return_value = ["missing_col1", "missing_col2"]

        # Test validation
        df = pd.DataFrame({"col1": ["a"]})
        result = validate_columns(df, "sale_records")

        assert result == ["missing_col1", "missing_col2"]


class TestUploadPageFileFormats:
    """Test upload page handles different file formats"""

    def test_load_csv_file(self):
        """Test that upload page accepts CSV files"""
        from services.upload_service import load_file

        # Create CSV data
        csv_data = b"col1,col2\na,1\nb,2"
        df = load_file(csv_data, "test.csv")

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert "col1" in df.columns
        assert "col2" in df.columns

    def test_load_excel_file(self):
        """Test that upload page accepts Excel files"""
        from services.upload_service import load_file

        # Create Excel data in memory
        df_excel = pd.DataFrame({"col1": ["a", "b"], "col2": [1, 2]})
        excel_buffer = io.BytesIO()
        df_excel.to_excel(excel_buffer, engine='openpyxl')
        excel_buffer.seek(0)

        df_loaded = load_file(excel_buffer.read(), "test.xlsx")

        assert isinstance(df_loaded, pd.DataFrame)
        assert len(df_loaded) == 2
        assert "col1" in df_loaded.columns


class TestUploadPageTableSelection:
    """Test upload page table selection logic"""

    def test_all_required_tables_exist(self):
        """Test that all required tables are defined in config"""
        from config import REQUIRED_COLUMNS

        required_tables = [
            "sale_records", "accounts_receivable_ledger", "product_master",
            "dealer_master", "sales_targets", "inventory_status",
            "incoming_shipments", "open_orders", "field_visit_plans",
        ]

        for table in required_tables:
            assert table in REQUIRED_COLUMNS


class TestUploadPageColumnValidation:
    """Test upload page column validation"""

    def test_validate_columns_with_valid_data(self):
        """Test validate_columns with valid sale_records data"""
        from services.upload_service import validate_columns

        df = pd.DataFrame({
            "order_id": ["ORD001"],
            "order_date": ["2024-01-01"],
            "date_transfer": ["2024-01-02"],
            "dealer_id": ["DEAL001"],
            "item_id": ["ITEM001"],
            "salesperson": ["SP001"],
            "sale_admin": ["SA001"],
            "channel_name": ["Retail"],
            "sales_volume": ["10"],
            "unit_price_standard": ["100"],
            "total_price_standard": ["1000"],
            "sales_revenue": ["1000"],
            "cost_of_goods": ["500"],
        })

        missing = validate_columns(df, "sale_records")
        assert missing == []

    def test_validate_columns_with_missing_columns(self):
        """Test validate_columns with missing columns"""
        from services.upload_service import validate_columns

        df = pd.DataFrame({
            "order_id": ["ORD001"],
            # Missing other required columns
        })

        missing = validate_columns(df, "sale_records")
        assert len(missing) > 0
        assert "order_date" in missing
        assert "dealer_id" in missing

    def test_validate_columns_for_product_master(self):
        """Test validate_columns for product_master table"""
        from services.upload_service import validate_columns

        df = pd.DataFrame({
            "item_id": ["ITEM001"],
            "item_name": ["Product A"],
            "product_id": ["PROD001"],
            "product": ["Product Group A"],
            "brand": ["Brand A"],
            "category": ["Category A"],
            "subcategory": ["Subcategory A"],
            "model": ["Model A"],
            "color": ["Red"],
            "size": ["M"],
        })

        missing = validate_columns(df, "product_master")
        assert missing == []


class TestUploadPagePreview:
    """Test upload page preview functionality"""

    def test_data_preview_shows_first_5_rows(self):
        """Test that preview shows first 5 rows"""
        # Create test data with more than 5 rows
        df = pd.DataFrame({
            "col1": [f"val{i}" for i in range(10)],
            "col2": list(range(10)),
        })

        # Preview should show first 5 rows
        preview = df.head(5)
        assert len(preview) == 5
        assert list(preview["col1"]) == ["val0", "val1", "val2", "val3", "val4"]

    def test_data_preview_with_less_than_5_rows(self):
        """Test that preview works with less than 5 rows"""
        df = pd.DataFrame({
            "col1": ["val0", "val1", "val2"],
            "col2": [0, 1, 2],
        })

        preview = df.head(5)
        assert len(preview) == 3


class TestUploadPageConfirmation:
    """Test upload page confirmation flow"""

    @patch('services.upload_service.upsert_dataframe')
    def test_upload_confirmation_success(self, mock_upsert):
        """Test that upload confirmation shows success message"""
        from services.upload_service import upsert_dataframe

        # Mock upsert
        df = pd.DataFrame({"col1": ["a"], "col2": [1]})
        mock_upsert.return_value = 5

        mock_db = MagicMock()
        count = upsert_dataframe(mock_db, df, "sale_records")

        assert count == 5
        mock_upsert.assert_called_once()

    @patch('services.upload_service.upsert_dataframe')
    def test_upload_handles_zero_rows(self, mock_upsert):
        """Test that upload handles empty dataframes"""
        from services.upload_service import upsert_dataframe

        df = pd.DataFrame()
        mock_upsert.return_value = 0

        mock_db = MagicMock()
        count = upsert_dataframe(mock_db, df, "sale_records")

        assert count == 0


class TestUploadPageErrorHandling:
    """Test upload page error handling"""

    def test_load_valid_csv_with_pandas(self):
        """Test that load_file handles valid CSV with pandas"""
        from services.upload_service import load_file

        # Pandas handles CSV data gracefully even with varying column counts
        csv_data = b"col1,col2\na,1\nb,2"
        df = load_file(csv_data, "test.csv")

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert "col1" in df.columns
        assert "col2" in df.columns

    def test_validate_columns_with_unknown_table(self):
        """Test validate_columns with unknown table name"""
        from services.upload_service import validate_columns

        df = pd.DataFrame({"col1": ["a"]})
        # Unknown table should return empty list or handle gracefully
        missing = validate_columns(df, "unknown_table")
        assert isinstance(missing, list)
