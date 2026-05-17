import bcrypt
from datetime import datetime
from sqlalchemy.orm import Session
from database.models import User, AuditLog

# --- Authentication & Authorization ---

def login(db: Session, username: str, password: str) -> User | None:
    user = db.query(User).filter_by(username=username).first()
    if user is None:
        return None
    if not bcrypt.checkpw(password.encode(), user.password_hash.encode()):
        return None
    return user

def require_role(user: User | None, allowed_roles: list[str]) -> None:
    if user is None or user.role not in allowed_roles:
        raise PermissionError(f"Access denied. Required: {allowed_roles}")

# --- Auditing ---

def log_audit_action(db: Session, username: str, action_type: str, details: str) -> None:
    log = AuditLog(
        timestamp=datetime.now(),
        username=username,
        action_type=action_type,
        details=details
    )
    db.add(log)
    db.commit()

# --- User Management ---

def create_user(db: Session, username: str, password: str, role: str, display_name: str, action_by: str) -> User:
    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    new_user = User(
        username=username,
        password_hash=password_hash,
        role=role,
        display_name=display_name,
        created_at=datetime.now()
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    log_audit_action(db, action_by, "Create", f"Created user {username} with role {role}")
    return new_user

def update_user(db: Session, user_id: str, role: str, display_name: str, action_by: str) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError("User not found")
    
    user.role = role
    user.display_name = display_name
    db.commit()
    db.refresh(user)
    
    log_audit_action(db, action_by, "Modify", f"Updated user {user.username} to role {role}, name {display_name}")
    return user

def delete_user(db: Session, user_id: str, action_by: str) -> bool:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return False
        
    username = user.username
    db.delete(user)
    db.commit()
    
    log_audit_action(db, action_by, "Delete", f"Deleted user {username}")
    return True

def change_password(db: Session, user_id: str, new_password: str, action_by: str) -> bool:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return False
        
    user.password_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
    db.commit()
    
    log_audit_action(db, action_by, "Modify", f"Changed password for user {user.username}")
    return True

def get_audit_logs(db: Session, limit: int = 100) -> list[AuditLog]:
    return db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit).all()
