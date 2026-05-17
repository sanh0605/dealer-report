import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Base, User
from database.seed import seed_users
from services.identity import login, require_role

@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    seed_users(session)
    yield session
    session.close()

def test_login_valid_credentials(db):
    user = login(db, "admin", "admin123")
    assert user is not None
    assert user.role == "Admin"

def test_login_wrong_password(db):
    user = login(db, "admin", "wrongpass")
    assert user is None

def test_login_unknown_user(db):
    user = login(db, "ghost", "anything")
    assert user is None

def test_require_role_passes(db):
    user = login(db, "manager", "manager123")
    require_role(user, ["Admin", "Manager"])  # should not raise

def test_require_role_blocks(db):
    user = login(db, "employee", "employee123")
    with pytest.raises(PermissionError):
        require_role(user, ["Admin", "Manager"])
