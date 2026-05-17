"""
Test configuration module structure and required constants.
"""

import os
import pytest


def test_config_module_exists():
    """Test that config.py module exists and can be imported."""
    import config
    assert config is not None


def test_roles_defined():
    """Test that ROLES constant is defined with required values."""
    import config
    assert hasattr(config, 'ROLES')
    assert isinstance(config.ROLES, list)
    assert "Admin" in config.ROLES
    assert "Manager" in config.ROLES
    assert "Sales Staff" in config.ROLES


def test_brand_group_map_defined():
    """Test that BRAND_GROUP_MAP constant is defined."""
    import config
    assert hasattr(config, 'BRAND_GROUP_MAP')
    assert isinstance(config.BRAND_GROUP_MAP, dict)


def test_sub_region_to_region_defined():
    """Test that SUB_REGION_TO_REGION constant is defined."""
    import config
    assert hasattr(config, 'SUB_REGION_TO_REGION')
    assert isinstance(config.SUB_REGION_TO_REGION, dict)


def test_required_columns_defined():
    """Test that REQUIRED_COLUMNS constant is defined with all required tables."""
    import config
    assert hasattr(config, 'REQUIRED_COLUMNS')
    assert isinstance(config.REQUIRED_COLUMNS, dict)

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
        assert table in config.REQUIRED_COLUMNS
        assert isinstance(config.REQUIRED_COLUMNS[table], list)
        assert len(config.REQUIRED_COLUMNS[table]) > 0


def test_package_directories_exist():
    """Test that all package directories exist with __init__.py files."""
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    packages = ['database', 'services', 'components', 'tests']
    for package in packages:
        package_path = os.path.join(base_path, package)
        assert os.path.isdir(package_path), f"Directory {package_path} does not exist"

        init_file = os.path.join(package_path, '__init__.py')
        assert os.path.isfile(init_file), f"File {init_file} does not exist"


def test_subdirectories_exist():
    """Test that required subdirectories exist."""
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    directories = ['pages', 'tests/e2e']
    for directory in directories:
        dir_path = os.path.join(base_path, directory)
        assert os.path.isdir(dir_path), f"Directory {dir_path} does not exist"
