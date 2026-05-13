import bcrypt
from sqlalchemy.orm import Session
from database.models import User
from database.session import init_db, get_db

_SEED_USERS = [
    {"username": "admin",    "password": "admin123",    "role": "Admin",       "display_name": "Administrator"},
    {"username": "manager", "password": "manager123",  "role": "Manager",     "display_name": "Sales Manager"},
    {"username": "employee", "password": "employee123",  "role": "Sales Staff", "display_name": "Sales Staff"},
]

def _hash(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def seed_users(db: Session) -> None:
    if db.query(User).count() > 0:
        return
    for u in _SEED_USERS:
        db.add(User(
            username=u["username"],
            password_hash=_hash(u["password"]),
            role=u["role"],
            display_name=u["display_name"],
        ))
    db.commit()

if __name__ == "__main__":
    init_db()
    db = get_db()
    try:
        seed_users(db)
        print("Database initialized. Default users created.")
        print("  admin / admin123     (Admin)")
        print("  manager / manager123 (Manager)")
        print("  employee / employee123 (Sales Staff)")
        print("IMPORTANT: Change all passwords after first login.")
    finally:
        db.close()
