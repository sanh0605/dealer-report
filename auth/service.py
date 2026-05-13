import bcrypt
from sqlalchemy.orm import Session
from database.models import User

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
