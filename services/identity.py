import bcrypt
import pandas as pd
import uuid
from datetime import datetime
from database.gsheets_db import read_sheet, update_sheet, append_row

# --- Helper to make a Series behave a bit like an object ---
class UserProxy:
    def __init__(self, data):
        self._data = data
    @property
    def id(self): return self._data.get('id')
    @property
    def username(self): return self._data.get('username')
    @property
    def password_hash(self): return self._data.get('password_hash')
    @property
    def role(self): return self._data.get('role')
    @property
    def display_name(self): return self._data.get('display_name')

# --- Authentication & Authorization ---

def login(dummy_db, username: str, password: str) -> UserProxy | None:
    # dummy_db is ignored as we use GSheets directly
    df = read_sheet("users", ttl=0)
    if df.empty:
        return None
        
    user_row = df[df['username'] == username]
    if user_row.empty:
        return None
    
    user_data = user_row.iloc[0].to_dict()
    if not bcrypt.checkpw(password.encode(), str(user_data['password_hash']).encode()):
        return None
        
    return UserProxy(user_data)

def require_role(user: UserProxy | dict | None, allowed_roles: list[str]) -> None:
    if user is None:
        raise PermissionError("Access denied. Authentication required.")
    
    role = user.role if isinstance(user, UserProxy) else user.get('role')
    if role not in allowed_roles:
        raise PermissionError(f"Access denied. Required: {allowed_roles}")

# --- Auditing ---

def log_audit_action(dummy_db, username: str, action_type: str, details: str) -> None:
    append_row("audit_logs", {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "username": username,
        "action_type": action_type,
        "details": details
    })

# --- User Management ---

def create_user(dummy_db, username: str, password: str, role: str, display_name: str, action_by: str) -> UserProxy:
    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    new_user_data = {
        "id": str(uuid.uuid4()),
        "username": username,
        "password_hash": password_hash,
        "role": role,
        "display_name": display_name,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    append_row("users", new_user_data)
    log_audit_action(None, action_by, "Create", f"Created user {username} with role {role}")
    return UserProxy(new_user_data)

def update_user(dummy_db, user_id: str, role: str, display_name: str, action_by: str) -> UserProxy:
    df = read_sheet("users", ttl=0)
    if df.empty:
        raise ValueError("User not found")
        
    idx = df[df['id'] == user_id].index
    if idx.empty:
        # Fallback to username if id is missing/not uuid (legacy)
        idx = df[df['username'] == user_id].index
        if idx.empty:
            raise ValueError("User not found")
    
    df.loc[idx, 'role'] = role
    df.loc[idx, 'display_name'] = display_name
    update_sheet("users", df)
    
    user_data = df.loc[idx[0]].to_dict()
    log_audit_action(None, action_by, "Modify", f"Updated user {user_data['username']} to role {role}, name {display_name}")
    return UserProxy(user_data)

def delete_user(dummy_db, user_id: str, action_by: str) -> bool:
    df = read_sheet("users", ttl=0)
    if df.empty:
        return False
        
    idx = df[df['id'] == user_id].index
    if idx.empty:
        idx = df[df['username'] == user_id].index
        if idx.empty:
            return False
            
    username = df.loc[idx[0], 'username']
    df = df.drop(idx)
    update_sheet("users", df)
    
    log_audit_action(None, action_by, "Delete", f"Deleted user {username}")
    return True

def change_password(dummy_db, user_id: str, new_password: str, action_by: str) -> bool:
    df = read_sheet("users", ttl=0)
    if df.empty:
        return False
        
    idx = df[df['id'] == user_id].index
    if idx.empty:
        idx = df[df['username'] == user_id].index
        if idx.empty:
            return False
            
    password_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
    df.loc[idx, 'password_hash'] = password_hash
    update_sheet("users", df)
    
    username = df.loc[idx[0], 'username']
    log_audit_action(None, action_by, "Modify", f"Changed password for user {username}")
    return True

def get_audit_logs(dummy_db, limit: int = 100) -> list:
    df = read_sheet("audit_logs", ttl=0)
    if df.empty:
        return []
    
    # Sort by timestamp desc and take limit
    if 'timestamp' in df.columns:
        df = df.sort_values('timestamp', ascending=False)
    
    # Return as list of objects for compatibility with view
    class AuditProxy:
        def __init__(self, d):
            self.timestamp = pd.to_datetime(d.get('timestamp'))
            self.username = d.get('username')
            self.action_type = d.get('action_type')
            self.details = d.get('details')
            
    return [AuditProxy(row) for _, row in df.head(limit).iterrows()]
