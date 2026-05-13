import pytest
from database.session import init_db, get_db
from auth.service import login
from database.models import User


def test_init_db_callable():
    """Test that init_db is callable"""
    from app import init_db as app_init_db
    assert callable(app_init_db)


def test_login_callable():
    """Test that login function is imported correctly"""
    from app import login as app_login
    assert callable(app_login)


def test_render_login_callable():
    """Test that _render_login function exists"""
    from app import _render_login
    assert callable(_render_login)


def test_app_module_structure():
    """Test that app module has expected structure"""
    import app
    assert hasattr(app, 'init_db')
    assert hasattr(app, 'get_db')
    assert hasattr(app, 'login')
    assert hasattr(app, '_render_login')


def test_login_function_integration():
    """Test login function integration with database"""
    from database.session import SessionLocal
    import bcrypt

    db = SessionLocal()

    # Create a test user
    test_password = "test123"
    password_hash = bcrypt.hashpw(test_password.encode(), bcrypt.gensalt()).decode()

    test_user = User(
        username="testuser",
        password_hash=password_hash,
        role="Admin",
        display_name="Test User"
    )
    db.add(test_user)
    db.commit()

    # Test successful login
    user = login(db, "testuser", test_password)
    assert user is not None
    assert user.username == "testuser"
    assert user.role == "Admin"
    assert user.display_name == "Test User"

    # Test failed login with wrong password
    user = login(db, "testuser", "wrongpassword")
    assert user is None

    # Test failed login with non-existent user
    user = login(db, "nonexistent", test_password)
    assert user is None

    # Cleanup
    db.delete(test_user)
    db.commit()
    db.close()
