import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Base, User, AuditLog
from database.seed import seed_users
from services.user_service import create_user, update_user, delete_user, change_password, get_audit_logs
import bcrypt

@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    seed_users(session)
    yield session
    session.close()

def test_create_user(db):
    user = create_user(db, "newuser", "newpass123", "Manager", "New User", "admin")
    assert user.username == "newuser"
    assert user.role == "Manager"
    
    # Check audit log
    logs = get_audit_logs(db, limit=1)
    assert len(logs) == 1
    assert logs[0].action_type == "Create"
    assert logs[0].username == "admin"
    assert "newuser" in logs[0].details

def test_update_user(db):
    employee = db.query(User).filter_by(username="employee").first()
    updated = update_user(db, employee.id, "Manager", "Updated Name", "admin")
    assert updated.role == "Manager"
    assert updated.display_name == "Updated Name"
    
    # Check audit log
    logs = get_audit_logs(db, limit=1)
    assert logs[0].action_type == "Modify"
    assert "Updated Name" in logs[0].details

def test_delete_user(db):
    employee = db.query(User).filter_by(username="employee").first()
    success = delete_user(db, employee.id, "admin")
    assert success is True
    
    # Ensure deleted
    deleted = db.query(User).filter_by(username="employee").first()
    assert deleted is None
    
    # Check audit log
    logs = get_audit_logs(db, limit=1)
    assert logs[0].action_type == "Delete"
    assert "employee" in logs[0].details

def test_change_password(db):
    employee = db.query(User).filter_by(username="employee").first()
    success = change_password(db, employee.id, "newemployee123", "employee")
    assert success is True
    
    # Verify password changed
    db.refresh(employee)
    assert bcrypt.checkpw(b"newemployee123", employee.password_hash.encode())
    
    # Check audit log
    logs = get_audit_logs(db, limit=1)
    assert logs[0].action_type == "Modify"
    assert "password" in logs[0].details.lower()
