"""Test that project skeleton files and directories exist."""
import os
from pathlib import Path

def test_required_files_exist():
    """Test that all required files exist."""
    project_root = Path(__file__).parent.parent

    required_files = [
        "requirements.txt",
        ".env",
        "config.py",
    ]

    for file_name in required_files:
        file_path = project_root / file_name
        assert file_path.exists(), f"Required file {file_name} does not exist"

def test_required_directories_exist():
    """Test that all required directories exist."""
    project_root = Path(__file__).parent.parent

    required_dirs = [
        "database",
        "services",
        "components",
        "pages",
        "tests",
        "tests/e2e",
    ]
    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        assert dir_path.exists(), f"Required directory {dir_name} does not exist"
        assert dir_path.is_dir(), f"{dir_name} exists but is not a directory"

def test_init_files_exist():
    """Test that all __init__.py files exist in package directories."""
    project_root = Path(__file__).parent.parent

    init_file_dirs = [
        "database",
        "services",
        "components",
        "tests",
    ]
    for dir_name in init_file_dirs:
        init_path = project_root / dir_name / "__init__.py"
        assert init_path.exists(), f"__init__.py does not exist in {dir_name}"

def test_config_constants():
    """Test that config.py has required constants."""
    from config import ROLES, BRAND_GROUP_MAP, SUB_REGION_TO_REGION, REQUIRED_COLUMNS

    assert isinstance(ROLES, list), "ROLES should be a list"
    assert len(ROLES) == 3, "ROLES should have 3 elements"
    assert "Admin" in ROLES, "Admin role should be in ROLES"

    assert isinstance(BRAND_GROUP_MAP, dict), "BRAND_GROUP_MAP should be a dict"
    assert isinstance(SUB_REGION_TO_REGION, dict), "SUB_REGION_TO_REGION should be a dict"
    assert isinstance(REQUIRED_COLUMNS, dict), "REQUIRED_COLUMNS should be a dict"

    required_tables = [
        "sale_records",
        "accounts_receivable_ledger",
        "product_master",
        "dealer_master",
        "sales_targets",
        "inventory_status",
        "incoming_shipments",
        "open_orders",
        "field_visit_plans",
        "visit_logs",
    ]

    for table in required_tables:
        assert table in REQUIRED_COLUMNS, f"{table} should be in REQUIRED_COLUMNS"
        assert isinstance(REQUIRED_COLUMNS[table], list), f"{table} columns should be a list"
        assert len(REQUIRED_COLUMNS[table]) > 0, f"{table} should have at least one required column"

def test_env_file_content():
    """Test that .env file has required variables."""
    project_root = Path(__file__).parent.parent
    env_path = project_root / ".env"

    with open(env_path, 'r') as f:
        content = f.read()

    assert "DATABASE_URL=sqlite:///./dealer_report.db" in content, "DATABASE_URL should be in .env"
    assert "SECRET_KEY=" in content, "SECRET_KEY should be in .env"

def test_requirements_content():
    """Test that requirements.txt has required packages."""
    project_root = Path(__file__).parent.parent
    requirements_path = project_root / "requirements.txt"

    with open(requirements_path, 'r') as f:
        content = f.read()

    required_packages = [
        "streamlit>=1.35.0",
        "pandas>=2.2.0",
        "sqlalchemy>=2.0.0",
        "python-pptx>=1.0.0",
        "weasyprint>=62.0",
        "pytest>=8.0.0",
        "pytest-playwright>=0.5.0",
        "python-dotenv>=1.0.0",
        "plotly>=5.22.0",
        "openpyxl>=3.1.0",
        "bcrypt>=4.1.0",
        "validators>=0.22.0",
        "bleach>=6.0.0",
        "pytz>=2024.1",
    ]

    for package in required_packages:
        assert package in content, f"{package} should be in requirements.txt"
