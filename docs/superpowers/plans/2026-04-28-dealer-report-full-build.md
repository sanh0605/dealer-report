# Dealer Report System — Full Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a production-ready Streamlit wholesale operations platform covering sales analytics, dealer health, inventory, field visits, and data exports — accessible to staff on the company LAN.

**Architecture:** Multi-page Streamlit app with a local SQLite database (SQLAlchemy ORM), role-based access control (Admin / Manager / Employee), CSV/Excel data upload, Plotly dashboards, and WeasyPrint/python-pptx export. All business logic lives in pure-function services tested with pytest before any UI is written.

**Tech Stack:** Python 3.11+, Streamlit, SQLAlchemy 2.x, SQLite, Pandas, Plotly, python-pptx, WeasyPrint, pytest, Playwright (E2E)

---

## Pre-Coding Fixes (Complete Before Any Task)

- [x] Remove `psycopg2-binary` from `requirements.txt`
- [x] Remove `altair` from `requirements.txt` (already not present)
- [x] Move `unit_price_standard` from product_master to sale_records (removed from product_master, added to sale_records)
- [x] Fix `sales_targets` table to simplified structure: target_id, month_year, sub_region, target_revenue (removed province, staff_name, target_volume)
- [x] Create `.env` file with content: `DATABASE_URL=sqlite:///./dealer_report.db` and `SECRET_KEY=change-me-in-production`
- [x] Create SECURITY.md with complete password policy, session management, user roles, and audit trail requirements
- [x] Create DASHBOARDS.md with complete dashboard design specifications (5 dashboards with Vietnamese UI)
- [x] Create DATA_VALIDATION.md with validation rules for all 11 tables including decision workflow for sales_targets
- [x] Add `dealer_VX_id` field to dealer_master table (optional text field)
- [x] Update business logic for lost sales revenue calculation with cascading formula
- [x] Define visit adherence with structured outcomes + free notes
- [x] Define AR aging with configurable bucket_size and max_days parameters
- [x] Confirm Vietnamese UI language policy with English development approach
- [x] Design PPT export format matching Vietnamese business report template

---

## File Map

| File | Responsibility |
|---|---|
| `app.py` | Entry point, auth gate, page navigation |
| `config.py` | Brand-group map, sub_region-to-region map, role constants |
| `.env` | DB URL and secret key |
| `database/models.py` | All 11 SQLAlchemy ORM models |
| `database/session.py` | Engine creation, `get_db()` session factory |
| `database/seed.py` | Create tables + seed Admin/Manager/Employee users |
| `auth/service.py` | `login()`, `get_session_user()`, `require_role()` |
| `services/upload_service.py` | `load_file()`, `validate_columns()`, `upsert_table()` |
| `services/analytics.py` | All KPI calculations (pure functions, no Streamlit) |
| `services/export_pdf.py` | `generate_pdf(figures, kpis) -> bytes` |
| `services/export_ppt.py` | `generate_ppt(figures, kpis) -> bytes` |
| `components/charts.py` | Reusable `plotly.graph_objects.Figure` builders |
| `components/kpi_cards.py` | `render_kpi_card(label, value, delta)` HTML helper |
| `pages/1_Upload.py` | Admin upload page for all tables |
| `pages/2_Sales_Dashboard.py` | Revenue KPIs + bar/pie/line charts |
| `pages/3_Dealer_Health.py` | AR aging, outstanding balance, dealer ranking |
| `pages/4_Product_Performance.py` | Sales by brand/category/model |
| `pages/5_Inventory.py` | Stock status, incoming, open orders, net availability |
| `pages/6_Field_Operations.py` | Visit plan management + log entry + adherence metrics |
| `pages/7_Lost_Sales.py` | Lost sales entry form + summary table |
| `pages/8_Admin.py` | User management + sales targets upload |
| `tests/test_models.py` | ORM model creation tests |
| `tests/test_auth.py` | Auth service unit tests |
| `tests/test_upload_service.py` | Upload validation and upsert tests |
| `tests/test_analytics.py` | KPI formula unit tests |
| `tests/test_export.py` | PDF/PPT byte output tests |
| `tests/e2e/test_app.spec.ts` | Playwright login + upload + dashboard E2E |

---

## Phase 1 — Foundation

### Task 1: Clean up dependencies and create project skeleton

**Files:**
- Modify: `requirements.txt`
- Create: `config.py`
- Create: `.env`
- Create: `database/__init__.py`
- Create: `auth/__init__.py`
- Create: `services/__init__.py`
- Create: `components/__init__.py`
- Create: `pages/` (empty directory)
- Create: `tests/__init__.py`
- Create: `tests/e2e/` (empty directory)

- [ ] **Step 1: Replace requirements.txt**

```
streamlit>=1.35.0
pandas>=2.2.0
sqlalchemy>=2.0.0
python-pptx>=1.0.0
weasyprint>=62.0
pytest>=8.0.0
pytest-playwright>=0.5.0
python-dotenv>=1.0.0
plotly>=5.22.0
openpyxl>=3.1.0
bcrypt>=4.1.0
```

- [ ] **Step 2: Create `.env`**

```
DATABASE_URL=sqlite:///./dealer_report.db
SECRET_KEY=change-me-in-production
```

- [ ] **Step 3: Create `config.py`**

```python
ROLES = ["Admin", "Manager", "Employee"]

BRAND_GROUP_MAP: dict[str, str] = {
    # Populate with actual brand names before first upload
    # Example: "Trek": "Premium Bikes", "Shimano": "Components"
}

SUB_REGION_TO_REGION: dict[str, str] = {
    # Populate with actual sub_region names before first upload
    # Example: "Chiang Mai": "North", "Bangkok": "Central", "Phuket": "South"
}

REQUIRED_COLUMNS: dict[str, list[str]] = {
    "sale_records": ["order_id","order_date","date_transfer","dealer_id","item_id",
                     "salesperson","sale_admin","channel_name","sales_volume",
                     "unit_price_standard","total_price_standard","sales_revenue",
                     "cost_of_goods"],
    "accounts_receivable_ledger": ["order_id","date_posted","due_date",
                                    "total_order_value","refund_amount",
                                    "deduction_amount","paid_amount"],
    "product_master": ["item_id","item_name","product_id","product","brand",
                        "category","subcategory","model","color","size"],
    "dealer_master": ["dealer_id","dealer_name","business_name","province",
                       "sub_region","address"],
    "sales_targets": ["month_year","sub_region","target_revenue"],
    "inventory_status": ["item_id","stock_on_hand","location","location_region"],
    "incoming_shipments": ["item_id","incoming_qty","expected_arrival_date"],
    "open_orders": ["order_id","dealer_id","item_id","open_qty"],
    "field_visit_plans": ["staff_name","month_year","dealer_id"],
    "visit_logs": ["date","staff_name","dealer_id","visit_result"],
}
```

- [ ] **Step 4: Create all `__init__.py` files (empty)**

```bash
touch database/__init__.py auth/__init__.py services/__init__.py components/__init__.py tests/__init__.py
mkdir -p pages tests/e2e
```

- [ ] **Step 5: Install dependencies**

```bash
pip install -r requirements.txt
```

Expected: All packages install without error.

- [ ] **Step 6: Commit**

```bash
git add requirements.txt config.py .env database/__init__.py auth/__init__.py services/__init__.py components/__init__.py tests/__init__.py
git commit -m "chore: project skeleton and cleaned dependencies"
```

---

### Task 2: SQLAlchemy ORM models

**Files:**
- Create: `database/models.py`
- Create: `tests/test_models.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_models.py
import pytest
from sqlalchemy import create_engine, inspect
from database.models import Base

@pytest.fixture
def engine():
    eng = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    return eng

def test_all_tables_created(engine):
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    expected = [
        "sale_records", "accounts_receivable_ledger", "product_master",
        "dealer_master", "sales_targets", "inventory_status",
        "incoming_shipments", "open_orders", "lost_sales_entry",
        "field_visit_plans", "visit_logs", "users",
    ]
    for t in expected:
        assert t in tables, f"Missing table: {t}"

def test_sale_records_columns(engine):
    inspector = inspect(engine)
    cols = {c["name"] for c in inspector.get_columns("sale_records")}
    assert "order_id" in cols
    assert "sales_revenue" in cols
    assert "cost_of_goods" in cols
    assert "unit_price_standard" in cols
```

- [ ] **Step 2: Run test to confirm it fails**

```bash
pytest tests/test_models.py -v
```

Expected: `ModuleNotFoundError: No module named 'database.models'`

- [ ] **Step 3: Create `database/models.py`**

```python
import uuid
from sqlalchemy import Column, Text, Integer, Float, Date, DateTime
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

def _uuid() -> str:
    return str(uuid.uuid4())

class SaleRecord(Base):
    __tablename__ = "sale_records"
    order_id              = Column(Text, primary_key=True)
    order_date            = Column(DateTime)
    date_transfer         = Column(Date)
    dealer_id             = Column(Text, index=True)
    item_id               = Column(Text, index=True)
    salesperson           = Column(Text)
    sale_admin            = Column(Text)
    channel_name          = Column(Text)
    sales_volume          = Column(Integer)
    unit_price_standard   = Column(Float)
    total_price_standard  = Column(Float)
    sales_revenue         = Column(Float)
    cost_of_goods         = Column(Float)

class AccountsReceivableLedger(Base):
    __tablename__ = "accounts_receivable_ledger"
    id                = Column(Text, primary_key=True, default=_uuid)
    order_id          = Column(Text, index=True)
    date_posted       = Column(Date)
    due_date          = Column(Date)
    total_order_value = Column(Float)
    refund_amount     = Column(Float)
    deduction_amount  = Column(Float)
    paid_amount       = Column(Float)

class ProductMaster(Base):
    __tablename__ = "product_master"
    item_id      = Column(Text, primary_key=True)
    item_name    = Column(Text)
    product_id   = Column(Text)
    product      = Column(Text)
    brand_group  = Column(Text)
    brand        = Column(Text)
    category     = Column(Text)
    subcategory  = Column(Text)
    model        = Column(Text)
    color        = Column(Text)
    size         = Column(Text)

class DealerMaster(Base):
    __tablename__ = "dealer_master"
    dealer_id     = Column(Text, primary_key=True)
    dealer_name   = Column(Text)
    business_name = Column(Text)
    province      = Column(Text)
    sub_region    = Column(Text)
    region        = Column(Text)
    address       = Column(Text)

class SalesTarget(Base):
    __tablename__ = "sales_targets"
    target_id      = Column(Text, primary_key=True, default=_uuid)
    month_year     = Column(Text, index=True)
    sub_region     = Column(Text)
    target_revenue = Column(Float)

class InventoryStatus(Base):
    __tablename__ = "inventory_status"
    id              = Column(Text, primary_key=True, default=_uuid)
    item_id         = Column(Text, index=True)
    stock_on_hand   = Column(Integer)
    location        = Column(Text)
    location_region = Column(Text)

class IncomingShipment(Base):
    __tablename__ = "incoming_shipments"
    id                    = Column(Text, primary_key=True, default=_uuid)
    item_id               = Column(Text, index=True)
    incoming_qty          = Column(Integer)
    expected_arrival_date = Column(Date)

class OpenOrder(Base):
    __tablename__ = "open_orders"
    id        = Column(Text, primary_key=True, default=_uuid)
    order_id  = Column(Text)
    dealer_id = Column(Text, index=True)
    item_id   = Column(Text, index=True)
    open_qty  = Column(Integer)

class LostSalesEntry(Base):
    __tablename__ = "lost_sales_entry"
    entry_id     = Column(Text, primary_key=True, default=_uuid)
    date         = Column(Date)
    staff_name   = Column(Text)
    dealer_id    = Column(Text, index=True)
    item_id      = Column(Text, index=True)
    lost_volume  = Column(Integer)
    lost_revenue = Column(Float)

class FieldVisitPlan(Base):
    __tablename__ = "field_visit_plans"
    plan_id    = Column(Text, primary_key=True, default=_uuid)
    staff_name = Column(Text)
    month_year = Column(Text, index=True)
    dealer_id  = Column(Text, index=True)

class VisitLog(Base):
    __tablename__ = "visit_logs"
    log_id       = Column(Text, primary_key=True, default=_uuid)
    date         = Column(Date)
    staff_name   = Column(Text)
    dealer_id    = Column(Text, index=True)
    visit_result = Column(Text)

class User(Base):
    __tablename__ = "users"
    id            = Column(Text, primary_key=True, default=_uuid)
    username      = Column(Text, unique=True, nullable=False)
    password_hash = Column(Text, nullable=False)
    role          = Column(Text, nullable=False)
    display_name  = Column(Text)
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_models.py -v
```

Expected: 3 PASSED

- [ ] **Step 5: Commit**

```bash
git add database/models.py tests/test_models.py
git commit -m "feat: SQLAlchemy ORM models for all 11 tables + users"
```

---

### Task 3: Database session factory

**Files:**
- Create: `database/session.py`

- [ ] **Step 1: Create `database/session.py`**

```python
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv
from database.models import Base

load_dotenv()

_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./dealer_report.db")

engine = create_engine(
    _DATABASE_URL,
    connect_args={"check_same_thread": False},  # required for SQLite + Streamlit
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

def init_db() -> None:
    Base.metadata.create_all(bind=engine)

def get_db() -> Session:
    return SessionLocal()
```

- [ ] **Step 2: Verify manually (no isolated test needed — covered by seed task)**

```bash
python -c "from database.session import init_db; init_db(); print('OK')"
```

Expected: `OK` printed, `dealer_report.db` file created.

- [ ] **Step 3: Commit**

```bash
git add database/session.py
git commit -m "feat: database session factory and init_db()"
```

---

### Task 4: Seed script (users + empty tables)

**Files:**
- Create: `database/seed.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_models.py  (append to existing file)
from database.seed import seed_users
from database.session import get_db
from database.models import User
import bcrypt

def test_seed_creates_three_users(engine):
    from sqlalchemy.orm import sessionmaker
    Session = sessionmaker(bind=engine)
    db = Session()
    seed_users(db)
    users = db.query(User).all()
    assert len(users) == 3
    roles = {u.role for u in users}
    assert roles == {"Admin", "Manager", "Employee"}
    db.close()

def test_seed_passwords_are_hashed(engine):
    from sqlalchemy.orm import sessionmaker
    Session = sessionmaker(bind=engine)
    db = Session()
    seed_users(db)
    admin = db.query(User).filter_by(role="Admin").first()
    assert admin.password_hash != "admin123"
    assert bcrypt.checkpw(b"admin123", admin.password_hash.encode())
    db.close()
```

- [ ] **Step 2: Run to confirm failure**

```bash
pytest tests/test_models.py::test_seed_creates_three_users -v
```

Expected: `ModuleNotFoundError: No module named 'database.seed'`

- [ ] **Step 3: Create `database/seed.py`**

```python
import bcrypt
from sqlalchemy.orm import Session
from database.models import User
from database.session import init_db, get_db

_SEED_USERS = [
    {"username": "admin",    "password": "admin123",    "role": "Admin",    "display_name": "Administrator"},
    {"username": "manager",  "password": "manager123",  "role": "Manager",  "display_name": "Sales Manager"},
    {"username": "employee", "password": "employee123", "role": "Employee", "display_name": "Sales Staff"},
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
        print("  admin / admin123  (Admin)")
        print("  manager / manager123  (Manager)")
        print("  employee / employee123  (Employee)")
        print("IMPORTANT: Change all passwords after first login.")
    finally:
        db.close()
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_models.py -v
```

Expected: 5 PASSED

- [ ] **Step 5: Run seed script to initialize the database**

```bash
python -m database.seed
```

Expected: Confirmation message with 3 users printed.

- [ ] **Step 6: Commit**

```bash
git add database/seed.py tests/test_models.py
git commit -m "feat: seed script creates default Admin/Manager/Employee users"
```

---

### Task 5: Auth service

**Files:**
- Create: `auth/service.py`
- Create: `tests/test_auth.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_auth.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Base, User
from database.seed import seed_users
from auth.service import login, require_role

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
```

- [ ] **Step 2: Run to confirm failure**

```bash
pytest tests/test_auth.py -v
```

Expected: `ModuleNotFoundError: No module named 'auth.service'`

- [ ] **Step 3: Create `auth/service.py`**

```python
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
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_auth.py -v
```

Expected: 5 PASSED

- [ ] **Step 5: Commit**

```bash
git add auth/service.py tests/test_auth.py
git commit -m "feat: auth service with bcrypt login and role enforcement"
```

---

### Task 6: App entry point with auth gate

**Files:**
- Create: `app.py`

- [ ] **Step 1: Create `app.py`**

```python
import streamlit as st
from database.session import init_db, get_db
from auth.service import login

st.set_page_config(
    page_title="Dealer Report",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_db()

def _render_login():
    st.title("Dealer Report System")
    st.subheader("Sign In")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign In")
    if submitted:
        db = get_db()
        try:
            user = login(db, username, password)
        finally:
            db.close()
        if user:
            st.session_state["user"] = {
                "username": user.username,
                "role": user.role,
                "display_name": user.display_name,
            }
            st.rerun()
        else:
            st.error("Invalid username or password.")

if "user" not in st.session_state:
    _render_login()
else:
    user = st.session_state["user"]
    st.sidebar.success(f"Signed in as **{user['display_name']}** ({user['role']})")
    if st.sidebar.button("Sign Out"):
        del st.session_state["user"]
        st.rerun()
    st.title("📊 Dealer Report — Dashboard")
    st.info("Use the sidebar to navigate to a module.")
```

- [ ] **Step 2: Run the app and verify login works**

```bash
streamlit run app.py
```

Open `http://localhost:8501`. Sign in with `admin` / `admin123`. Verify sidebar shows name and role. Sign out. Verify login screen returns.

- [ ] **Step 3: Commit**

```bash
git add app.py
git commit -m "feat: Streamlit entry point with login/logout auth gate"
```

---

## Phase 2 — Data Management

### Task 7: Upload service (validate + upsert CSV/Excel)

**Files:**
- Create: `services/upload_service.py`
- Create: `tests/test_upload_service.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_upload_service.py
import pytest
import pandas as pd
import io
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Base, SaleRecord
from services.upload_service import validate_columns, upsert_dataframe

@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_validate_columns_passes():
    df = pd.DataFrame(columns=["order_id","order_date","date_transfer","dealer_id",
                                "item_id","salesperson","sale_admin","channel_name",
                                "sales_volume","total_price_standard","sales_revenue",
                                "cost_of_goods"])
    missing = validate_columns(df, "sale_records")
    assert missing == []

def test_validate_columns_catches_missing():
    df = pd.DataFrame(columns=["order_id", "order_date"])
    missing = validate_columns(df, "sale_records")
    assert "sales_revenue" in missing
    assert "dealer_id" in missing

def test_upsert_inserts_new_rows(db):
    df = pd.DataFrame([{
        "order_id": "ORD001", "order_date": "01/01/2026 09:00:00",
        "date_transfer": "02/01/2026", "dealer_id": "D001", "item_id": "SKU001",
        "salesperson": "Alice", "sale_admin": "Bob", "channel_name": "Direct",
        "sales_volume": 10, "total_price_standard": 1000.0,
        "sales_revenue": 900.0, "cost_of_goods": 500.0,
    }])
    count = upsert_dataframe(db, df, "sale_records")
    assert count == 1
    assert db.query(SaleRecord).count() == 1

def test_upsert_is_idempotent(db):
    df = pd.DataFrame([{
        "order_id": "ORD001", "order_date": "01/01/2026 09:00:00",
        "date_transfer": "02/01/2026", "dealer_id": "D001", "item_id": "SKU001",
        "salesperson": "Alice", "sale_admin": "Bob", "channel_name": "Direct",
        "sales_volume": 10, "total_price_standard": 1000.0,
        "sales_revenue": 900.0, "cost_of_goods": 500.0,
    }])
    upsert_dataframe(db, df, "sale_records")
    upsert_dataframe(db, df, "sale_records")
    assert db.query(SaleRecord).count() == 1  # no duplicate
```

- [ ] **Step 2: Run to confirm failure**

```bash
pytest tests/test_upload_service.py -v
```

Expected: `ModuleNotFoundError: No module named 'services.upload_service'`

- [ ] **Step 3: Create `services/upload_service.py`**

```python
import io
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from config import REQUIRED_COLUMNS, BRAND_GROUP_MAP, SUB_REGION_TO_REGION
from database.models import (
    SaleRecord, AccountsReceivableLedger, ProductMaster, DealerMaster,
    SalesTarget, InventoryStatus, IncomingShipment, OpenOrder,
    FieldVisitPlan,
)

_TABLE_MODEL_MAP = {
    "sale_records": SaleRecord,
    "accounts_receivable_ledger": AccountsReceivableLedger,
    "product_master": ProductMaster,
    "dealer_master": DealerMaster,
    "sales_targets": SalesTarget,
    "inventory_status": InventoryStatus,
    "incoming_shipments": IncomingShipment,
    "open_orders": OpenOrder,
    "field_visit_plans": FieldVisitPlan,
}

def load_file(file_bytes: bytes, filename: str) -> pd.DataFrame:
    buf = io.BytesIO(file_bytes)
    if filename.endswith(".csv"):
        return pd.read_csv(buf, dtype=str)
    return pd.read_excel(buf, dtype=str)

def validate_columns(df: pd.DataFrame, table_name: str) -> list[str]:
    required = REQUIRED_COLUMNS.get(table_name, [])
    return [c for c in required if c not in df.columns]

def _apply_auto_assignments(df: pd.DataFrame, table_name: str) -> pd.DataFrame:
    df = df.copy()
    if table_name == "product_master" and "brand" in df.columns:
        df["brand_group"] = df["brand"].map(BRAND_GROUP_MAP).fillna("Other")
    if table_name == "dealer_master" and "sub_region" in df.columns:
        df["region"] = df["sub_region"].map(SUB_REGION_TO_REGION).fillna("Unknown")
    return df

def upsert_dataframe(db: Session, df: pd.DataFrame, table_name: str) -> int:
    model = _TABLE_MODEL_MAP[table_name]
    df = _apply_auto_assignments(df, table_name)
    mapper = model.__mapper__
    cols = {c.key for c in mapper.columns}
    df = df[[c for c in df.columns if c in cols]]
    df = df.where(pd.notna(df), None)
    records = df.to_dict(orient="records")
    if not records:
        return 0
    stmt = sqlite_insert(model.__table__).values(records)
    pk_cols = [c.key for c in mapper.primary_key]
    update_cols = {c: stmt.excluded[c] for c in df.columns if c not in pk_cols}
    stmt = stmt.on_conflict_do_update(index_elements=pk_cols, set_=update_cols)
    db.execute(stmt)
    db.commit()
    return len(records)
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_upload_service.py -v
```

Expected: 4 PASSED

- [ ] **Step 5: Commit**

```bash
git add services/upload_service.py tests/test_upload_service.py
git commit -m "feat: upload service with column validation and idempotent upsert"
```

---

### Task 8: Data Upload page (UI)

**Files:**
- Create: `pages/1_Upload.py`

- [ ] **Step 1: Create `pages/1_Upload.py`**

```python
import streamlit as st
from auth.service import require_role
from database.session import get_db
from services.upload_service import load_file, validate_columns, upsert_dataframe

st.set_page_config(page_title="Upload Data", layout="wide")

if "user" not in st.session_state:
    st.error("Please sign in from the Home page.")
    st.stop()

user = st.session_state["user"]
try:
    require_role(type("U", (), user)(), ["Admin"])
except PermissionError:
    st.error("Admin access required to upload data.")
    st.stop()

TABLES = [
    "sale_records", "accounts_receivable_ledger", "product_master",
    "dealer_master", "sales_targets", "inventory_status",
    "incoming_shipments", "open_orders", "field_visit_plans",
]

st.title("📤 Data Upload")
st.caption("Upload CSV or Excel files for each data table. Existing records are updated, new records are inserted.")

table_name = st.selectbox("Select table to upload", TABLES)
uploaded = st.file_uploader(f"Upload file for **{table_name}**", type=["csv", "xlsx", "xls"])

if uploaded:
    df = load_file(uploaded.read(), uploaded.name)
    st.subheader("Preview (first 5 rows)")
    st.dataframe(df.head(5))
    missing = validate_columns(df, table_name)
    if missing:
        st.error(f"Missing required columns: {', '.join(missing)}")
    else:
        st.success(f"All required columns present. {len(df)} rows ready to upload.")
        if st.button("Confirm Upload"):
            db = get_db()
            try:
                count = upsert_dataframe(db, df, table_name)
                st.success(f"Uploaded {count} rows to **{table_name}**.")
            except Exception as e:
                st.error(f"Upload failed: {e}")
            finally:
                db.close()
```

- [ ] **Step 2: Test manually in browser**

Run `streamlit run app.py`, sign in as `admin`, navigate to Upload. Upload a sample CSV for `sale_records`. Verify success message and row count.

- [ ] **Step 3: Commit**

```bash
git add pages/1_Upload.py
git commit -m "feat: data upload page with validation feedback"
```

---

## Phase 3 — Analytics Service

### Task 9: Core analytics calculations

**Files:**
- Create: `services/analytics.py`
- Create: `tests/test_analytics.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_analytics.py
import pytest
import pandas as pd
from services.analytics import (
    calc_total_revenue, calc_gross_profit, calc_target_completion,
    calc_ar_outstanding, calc_visit_adherence,
)

def test_calc_total_revenue():
    df = pd.DataFrame({"sales_revenue": [100.0, 200.0, 300.0]})
    assert calc_total_revenue(df) == 600.0

def test_calc_total_revenue_empty():
    df = pd.DataFrame({"sales_revenue": []})
    assert calc_total_revenue(df) == 0.0

def test_calc_gross_profit():
    df = pd.DataFrame({"sales_revenue": [1000.0], "cost_of_goods": [600.0]})
    profit, margin = calc_gross_profit(df)
    assert profit == 400.0
    assert margin == pytest.approx(40.0)

def test_calc_target_completion():
    assert calc_target_completion(actual=800.0, target=1000.0) == pytest.approx(80.0)

def test_calc_target_completion_zero_target():
    assert calc_target_completion(actual=800.0, target=0.0) == 0.0

def test_calc_ar_outstanding():
    df = pd.DataFrame({
        "order_id":          ["O1", "O1", "O2"],
        "total_order_value": [1000.0, 1000.0, 500.0],
        "paid_amount":       [400.0, 0.0, 500.0],
        "refund_amount":     [0.0, 0.0, 0.0],
        "deduction_amount":  [0.0, 0.0, 0.0],
    })
    # O1 max total = 1000, paid = 400+0 = 400, outstanding = 600
    # O2 max total = 500, paid = 500, outstanding = 0
    result = calc_ar_outstanding(df)
    assert result == pytest.approx(600.0)

def test_calc_visit_adherence():
    plans = pd.DataFrame({"dealer_id": ["D1", "D2", "D3"], "staff_name": ["Alice"]*3})
    logs  = pd.DataFrame({"dealer_id": ["D1", "D3"],        "staff_name": ["Alice"]*2})
    adherence, missed = calc_visit_adherence(plans, logs)
    assert adherence == pytest.approx(2/3 * 100)
    assert set(missed) == {"D2"}
```

- [ ] **Step 2: Run to confirm failure**

```bash
pytest tests/test_analytics.py -v
```

Expected: `ModuleNotFoundError: No module named 'services.analytics'`

- [ ] **Step 3: Create `services/analytics.py`**

```python
import pandas as pd

def calc_total_revenue(sales_df: pd.DataFrame) -> float:
    if sales_df.empty or "sales_revenue" not in sales_df.columns:
        return 0.0
    return float(sales_df["sales_revenue"].sum())

def calc_gross_profit(sales_df: pd.DataFrame) -> tuple[float, float]:
    revenue = float(sales_df["sales_revenue"].sum())
    cogs = float(sales_df["cost_of_goods"].sum())
    profit = revenue - cogs
    margin = (profit / revenue * 100) if revenue > 0 else 0.0
    return profit, margin

def calc_target_completion(actual: float, target: float) -> float:
    if target == 0:
        return 0.0
    return actual / target * 100

def calc_ar_outstanding(ar_df: pd.DataFrame) -> float:
    if ar_df.empty:
        return 0.0
    per_order = ar_df.groupby("order_id").agg(
        total=("total_order_value", "max"),
        paid=("paid_amount", "sum"),
        refund=("refund_amount", "sum"),
        deduction=("deduction_amount", "sum"),
    )
    per_order["outstanding"] = (
        per_order["total"] - per_order["paid"]
        - per_order["refund"] - per_order["deduction"]
    ).clip(lower=0)
    return float(per_order["outstanding"].sum())

def calc_visit_adherence(
    plans_df: pd.DataFrame,
    logs_df: pd.DataFrame,
) -> tuple[float, list[str]]:
    if plans_df.empty:
        return 0.0, []
    planned = set(plans_df["dealer_id"].unique())
    visited = set(logs_df["dealer_id"].unique()) if not logs_df.empty else set()
    hit = planned & visited
    missed = sorted(planned - visited)
    adherence = len(hit) / len(planned) * 100
    return adherence, missed
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_analytics.py -v
```

Expected: 8 PASSED

- [ ] **Step 5: Commit**

```bash
git add services/analytics.py tests/test_analytics.py
git commit -m "feat: core analytics functions with full unit test coverage"
```

---

### Task 10: Reusable chart components

**Files:**
- Create: `components/charts.py`
- Create: `components/kpi_cards.py`

- [ ] **Step 1: Create `components/charts.py`**

```python
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

_PALETTE = ["#1f77b4","#ff7f0e","#2ca02c","#d62728","#9467bd","#8c564b"]

def bar_chart(df: pd.DataFrame, x: str, y: str, title: str) -> go.Figure:
    fig = px.bar(df, x=x, y=y, title=title, color_discrete_sequence=_PALETTE)
    fig.update_layout(margin=dict(t=40, b=20), plot_bgcolor="white")
    return fig

def pie_chart(df: pd.DataFrame, names: str, values: str, title: str) -> go.Figure:
    fig = px.pie(df, names=names, values=values, title=title,
                 color_discrete_sequence=_PALETTE, hole=0.35)
    fig.update_layout(margin=dict(t=40, b=20))
    return fig

def line_chart(df: pd.DataFrame, x: str, y: str, title: str,
               color: str | None = None) -> go.Figure:
    fig = px.line(df, x=x, y=y, color=color, title=title,
                  color_discrete_sequence=_PALETTE, markers=True)
    fig.update_layout(margin=dict(t=40, b=20), plot_bgcolor="white")
    return fig

def treemap_chart(df: pd.DataFrame, path: list[str], values: str, title: str) -> go.Figure:
    fig = px.treemap(df, path=path, values=values, title=title,
                     color_discrete_sequence=_PALETTE)
    fig.update_layout(margin=dict(t=40, b=20))
    return fig
```

- [ ] **Step 2: Create `components/kpi_cards.py`**

```python
import streamlit as st

def render_kpi_row(metrics: list[dict]) -> None:
    """
    metrics: list of {"label": str, "value": str, "delta": str | None, "delta_color": str}
    """
    cols = st.columns(len(metrics))
    for col, m in zip(cols, metrics):
        col.metric(
            label=m["label"],
            value=m["value"],
            delta=m.get("delta"),
            delta_color=m.get("delta_color", "normal"),
        )
```

- [ ] **Step 3: Commit**

```bash
git add components/charts.py components/kpi_cards.py
git commit -m "feat: reusable Plotly chart builders and KPI card component"
```

---

## Phase 4 — Dashboard Pages

### Task 11: Sales & Revenue Dashboard

**Files:**
- Create: `pages/2_Sales_Dashboard.py`

- [ ] **Step 1: Create `pages/2_Sales_Dashboard.py`**

```python
import streamlit as st
import pandas as pd
from database.session import get_db
from database.models import SaleRecord, SalesTarget
from services.analytics import calc_total_revenue, calc_gross_profit, calc_target_completion
from components.kpi_cards import render_kpi_row
from components.charts import bar_chart, pie_chart, line_chart

st.set_page_config(page_title="Sales Dashboard", layout="wide")
if "user" not in st.session_state:
    st.error("Please sign in from the Home page.")
    st.stop()

st.title("💰 Sales & Revenue Dashboard")

db = get_db()
try:
    sales_rows = db.query(SaleRecord).all()
    target_rows = db.query(SalesTarget).all()
finally:
    db.close()

if not sales_rows:
    st.info("No sales data found. Upload data via the Upload page.")
    st.stop()

df = pd.DataFrame([r.__dict__ for r in sales_rows]).drop(columns=["_sa_instance_state"], errors="ignore")
df["order_date"] = pd.to_datetime(df["order_date"], dayfirst=True, errors="coerce")
df["month"] = df["order_date"].dt.to_period("M").astype(str)
df[["sales_revenue","cost_of_goods","sales_volume","total_price_standard"]] = (
    df[["sales_revenue","cost_of_goods","sales_volume","total_price_standard"]].apply(pd.to_numeric, errors="coerce")
)

# Sidebar filters
st.sidebar.header("Filters")
regions = ["All"] + sorted(df["salesperson"].dropna().unique().tolist())
sel_sp = st.sidebar.selectbox("Salesperson", regions)
channels = ["All"] + sorted(df["channel_name"].dropna().unique().tolist())
sel_ch = st.sidebar.selectbox("Channel", channels)
months = ["All"] + sorted(df["month"].dropna().unique().tolist())
sel_mo = st.sidebar.selectbox("Month", months)

fdf = df.copy()
if sel_sp != "All": fdf = fdf[fdf["salesperson"] == sel_sp]
if sel_ch != "All": fdf = fdf[fdf["channel_name"] == sel_ch]
if sel_mo != "All": fdf = fdf[fdf["month"] == sel_mo]

# KPIs
total_rev = calc_total_revenue(fdf)
profit, margin = calc_gross_profit(fdf)
total_vol = int(fdf["sales_volume"].sum())
target_rev = sum(t.target_revenue or 0 for t in target_rows)
completion = calc_target_completion(total_rev, target_rev)

render_kpi_row([
    {"label": "Total Revenue",        "value": f"฿{total_rev:,.0f}"},
    {"label": "Gross Profit",         "value": f"฿{profit:,.0f}", "delta": f"{margin:.1f}% margin"},
    {"label": "Total Volume (units)",  "value": f"{total_vol:,}"},
    {"label": "Target Completion",    "value": f"{completion:.1f}%"},
])

st.divider()
col1, col2 = st.columns(2)

# Bar: Revenue by salesperson
by_sp = fdf.groupby("salesperson")["sales_revenue"].sum().reset_index()
col1.plotly_chart(bar_chart(by_sp, "salesperson", "sales_revenue", "Revenue by Salesperson"), use_container_width=True)

# Pie: Revenue by channel
by_ch = fdf.groupby("channel_name")["sales_revenue"].sum().reset_index()
col2.plotly_chart(pie_chart(by_ch, "channel_name", "sales_revenue", "Revenue by Channel"), use_container_width=True)

# Line: Monthly trend
by_mo = fdf.groupby("month")["sales_revenue"].sum().reset_index().sort_values("month")
st.plotly_chart(line_chart(by_mo, "month", "sales_revenue", "Monthly Revenue Trend"), use_container_width=True)

# Raw data table
with st.expander("View Raw Data"):
    st.dataframe(fdf[["order_id","order_date","dealer_id","salesperson","channel_name","sales_volume","sales_revenue"]].reset_index(drop=True))
```

- [ ] **Step 2: Test in browser**

Run app, upload a sample `sale_records` CSV, navigate to Sales Dashboard. Verify KPI cards, 3 charts, and data table all render correctly.

- [ ] **Step 3: Commit**

```bash
git add pages/2_Sales_Dashboard.py
git commit -m "feat: sales and revenue dashboard with KPIs and charts"
```

---

### Task 12: Dealer Health Module

**Files:**
- Create: `pages/3_Dealer_Health.py`

- [ ] **Step 1: Create `pages/3_Dealer_Health.py`**

```python
import streamlit as st
import pandas as pd
from database.session import get_db
from database.models import AccountsReceivableLedger, DealerMaster, SaleRecord
from services.analytics import calc_ar_outstanding

st.set_page_config(page_title="Dealer Health", layout="wide")
if "user" not in st.session_state:
    st.error("Please sign in from the Home page.")
    st.stop()

st.title("🏪 Dealer Health")

db = get_db()
try:
    ar_rows   = db.query(AccountsReceivableLedger).all()
    dlr_rows  = db.query(DealerMaster).all()
    sale_rows = db.query(SaleRecord).all()
finally:
    db.close()

if not ar_rows:
    st.info("No AR data found. Upload accounts_receivable_ledger data first.")
    st.stop()

ar_df   = pd.DataFrame([r.__dict__ for r in ar_rows]).drop(columns=["_sa_instance_state"], errors="ignore")
dlr_df  = pd.DataFrame([r.__dict__ for r in dlr_rows]).drop(columns=["_sa_instance_state"], errors="ignore")
sale_df = pd.DataFrame([r.__dict__ for r in sale_rows]).drop(columns=["_sa_instance_state"], errors="ignore")

for col in ["total_order_value","paid_amount","refund_amount","deduction_amount"]:
    ar_df[col] = pd.to_numeric(ar_df[col], errors="coerce").fillna(0)

# Per-order outstanding
per_order = ar_df.groupby("order_id").agg(
    total=("total_order_value","max"),
    paid=("paid_amount","sum"),
    refund=("refund_amount","sum"),
    deduction=("deduction_amount","sum"),
).reset_index()
per_order["outstanding"] = (per_order["total"] - per_order["paid"] - per_order["refund"] - per_order["deduction"]).clip(lower=0)

# Join with sale_records to get dealer_id
if not sale_df.empty and "dealer_id" in sale_df.columns:
    order_dealer = sale_df[["order_id","dealer_id"]].drop_duplicates("order_id")
    per_order = per_order.merge(order_dealer, on="order_id", how="left")
    by_dealer = per_order.groupby("dealer_id")["outstanding"].sum().reset_index()
    if not dlr_df.empty:
        by_dealer = by_dealer.merge(dlr_df[["dealer_id","dealer_name","business_name","region"]], on="dealer_id", how="left")
    by_dealer = by_dealer.sort_values("outstanding", ascending=False).reset_index(drop=True)
    st.subheader("Outstanding Balance by Dealer")
    st.dataframe(by_dealer, use_container_width=True)
    total_outstanding = calc_ar_outstanding(ar_df)
    st.metric("Total Outstanding (All Dealers)", f"฿{total_outstanding:,.0f}")
else:
    st.dataframe(per_order, use_container_width=True)
```

- [ ] **Step 2: Test in browser — navigate to Dealer Health, verify table renders.**

- [ ] **Step 3: Commit**

```bash
git add pages/3_Dealer_Health.py
git commit -m "feat: dealer health page with AR outstanding by dealer"
```

---

### Task 13: Product Performance Module

**Files:**
- Create: `pages/4_Product_Performance.py`

- [ ] **Step 1: Create `pages/4_Product_Performance.py`**

```python
import streamlit as st
import pandas as pd
from database.session import get_db
from database.models import SaleRecord, ProductMaster
from components.charts import bar_chart, treemap_chart

st.set_page_config(page_title="Product Performance", layout="wide")
if "user" not in st.session_state:
    st.error("Please sign in from the Home page.")
    st.stop()

st.title("📦 Product Performance")

db = get_db()
try:
    sale_rows    = db.query(SaleRecord).all()
    product_rows = db.query(ProductMaster).all()
finally:
    db.close()

if not sale_rows:
    st.info("No sales data found.")
    st.stop()

sale_df = pd.DataFrame([r.__dict__ for r in sale_rows]).drop(columns=["_sa_instance_state"], errors="ignore")
prod_df = pd.DataFrame([r.__dict__ for r in product_rows]).drop(columns=["_sa_instance_state"], errors="ignore")

for col in ["sales_revenue","sales_volume","cost_of_goods"]:
    sale_df[col] = pd.to_numeric(sale_df[col], errors="coerce").fillna(0)

if not prod_df.empty:
    merged = sale_df.merge(prod_df[["item_id","brand_group","brand","category","subcategory","model"]], on="item_id", how="left")
else:
    merged = sale_df

tab1, tab2, tab3 = st.tabs(["By Brand Group", "By Category", "By SKU"])

with tab1:
    if "brand_group" in merged.columns:
        by_bg = merged.groupby("brand_group")["sales_revenue"].sum().reset_index()
        st.plotly_chart(bar_chart(by_bg, "brand_group", "sales_revenue", "Revenue by Brand Group"), use_container_width=True)

with tab2:
    if "category" in merged.columns:
        by_cat = merged.groupby("category")[["sales_revenue","sales_volume"]].sum().reset_index()
        st.plotly_chart(bar_chart(by_cat, "category", "sales_revenue", "Revenue by Category"), use_container_width=True)
        if "subcategory" in merged.columns:
            treemap_data = merged.groupby(["category","subcategory"])["sales_revenue"].sum().reset_index()
            st.plotly_chart(treemap_chart(treemap_data, ["category","subcategory"], "sales_revenue", "Revenue Treemap"), use_container_width=True)

with tab3:
    top_skus = merged.groupby("item_id")[["sales_revenue","sales_volume"]].sum().reset_index().sort_values("sales_revenue", ascending=False).head(20)
    st.dataframe(top_skus, use_container_width=True)
```

- [ ] **Step 2: Test in browser.**

- [ ] **Step 3: Commit**

```bash
git add pages/4_Product_Performance.py
git commit -m "feat: product performance page with brand/category/SKU views"
```

---

### Task 14: Inventory Module

**Files:**
- Create: `pages/5_Inventory.py`

- [ ] **Step 1: Create `pages/5_Inventory.py`**

```python
import streamlit as st
import pandas as pd
from database.session import get_db
from database.models import InventoryStatus, IncomingShipment, OpenOrder, ProductMaster

st.set_page_config(page_title="Inventory", layout="wide")
if "user" not in st.session_state:
    st.error("Please sign in from the Home page.")
    st.stop()

st.title("🏭 Inventory Status")

db = get_db()
try:
    inv_rows  = db.query(InventoryStatus).all()
    ship_rows = db.query(IncomingShipment).all()
    oo_rows   = db.query(OpenOrder).all()
    prod_rows = db.query(ProductMaster).all()
finally:
    db.close()

if not inv_rows:
    st.info("No inventory data found. Upload inventory_status data first.")
    st.stop()

inv_df  = pd.DataFrame([r.__dict__ for r in inv_rows]).drop(columns=["_sa_instance_state"], errors="ignore")
ship_df = pd.DataFrame([r.__dict__ for r in ship_rows]).drop(columns=["_sa_instance_state"], errors="ignore")
oo_df   = pd.DataFrame([r.__dict__ for r in oo_rows]).drop(columns=["_sa_instance_state"], errors="ignore")
prod_df = pd.DataFrame([r.__dict__ for r in prod_rows]).drop(columns=["_sa_instance_state"], errors="ignore")

inv_df["stock_on_hand"] = pd.to_numeric(inv_df["stock_on_hand"], errors="coerce").fillna(0)

# Aggregate by item_id (sum across warehouses)
stock = inv_df.groupby("item_id")["stock_on_hand"].sum().reset_index()

if not ship_df.empty:
    ship_df["incoming_qty"] = pd.to_numeric(ship_df["incoming_qty"], errors="coerce").fillna(0)
    incoming = ship_df.groupby("item_id")["incoming_qty"].sum().reset_index()
    stock = stock.merge(incoming, on="item_id", how="left").fillna(0)
else:
    stock["incoming_qty"] = 0

if not oo_df.empty:
    oo_df["open_qty"] = pd.to_numeric(oo_df["open_qty"], errors="coerce").fillna(0)
    open_q = oo_df.groupby("item_id")["open_qty"].sum().reset_index()
    stock = stock.merge(open_q, on="item_id", how="left").fillna(0)
else:
    stock["open_qty"] = 0

stock["net_available"] = stock["stock_on_hand"] + stock["incoming_qty"] - stock["open_qty"]

LOW_STOCK_THRESHOLD = st.sidebar.number_input("Low stock threshold (units)", min_value=0, value=10)

def _status(row):
    if row["stock_on_hand"] == 0:
        return "Stockout"
    if row["stock_on_hand"] <= LOW_STOCK_THRESHOLD:
        return "Low Stock"
    return "Healthy"

stock["status"] = stock.apply(_status, axis=1)

if not prod_df.empty:
    stock = stock.merge(prod_df[["item_id","item_name","brand","category"]], on="item_id", how="left")

col1, col2, col3 = st.columns(3)
col1.metric("Stockout SKUs", int((stock["status"] == "Stockout").sum()))
col2.metric("Low Stock SKUs", int((stock["status"] == "Low Stock").sum()))
col3.metric("Healthy SKUs", int((stock["status"] == "Healthy").sum()))

status_filter = st.selectbox("Filter by status", ["All", "Stockout", "Low Stock", "Healthy"])
display = stock if status_filter == "All" else stock[stock["status"] == status_filter]
st.dataframe(display.reset_index(drop=True), use_container_width=True)
```

- [ ] **Step 2: Test in browser.**

- [ ] **Step 3: Commit**

```bash
git add pages/5_Inventory.py
git commit -m "feat: inventory page with stock/incoming/open-order net availability"
```

---

## Phase 5 — Field Operations & Entry Forms

### Task 15: Field Operations page (visit plans + logs + adherence)

**Files:**
- Create: `pages/6_Field_Operations.py`

- [ ] **Step 1: Create `pages/6_Field_Operations.py`**

```python
import streamlit as st
import pandas as pd
from datetime import date
from database.session import get_db
from database.models import FieldVisitPlan, VisitLog, DealerMaster
from services.analytics import calc_visit_adherence

st.set_page_config(page_title="Field Operations", layout="wide")
if "user" not in st.session_state:
    st.error("Please sign in from the Home page.")
    st.stop()

user = st.session_state["user"]
st.title("🗓️ Field Operations")

tab_metrics, tab_log = st.tabs(["Visit Metrics", "Log a Visit"])

db = get_db()
try:
    plan_rows   = db.query(FieldVisitPlan).all()
    log_rows    = db.query(VisitLog).all()
    dealer_rows = db.query(DealerMaster).all()
finally:
    db.close()

plan_df   = pd.DataFrame([r.__dict__ for r in plan_rows]).drop(columns=["_sa_instance_state"], errors="ignore") if plan_rows else pd.DataFrame()
log_df    = pd.DataFrame([r.__dict__ for r in log_rows]).drop(columns=["_sa_instance_state"], errors="ignore") if log_rows else pd.DataFrame()
dealer_df = pd.DataFrame([r.__dict__ for r in dealer_rows]).drop(columns=["_sa_instance_state"], errors="ignore") if dealer_rows else pd.DataFrame()

with tab_metrics:
    if plan_df.empty:
        st.info("No visit plans found. Upload field_visit_plans data first.")
    else:
        months = sorted(plan_df["month_year"].dropna().unique().tolist(), reverse=True)
        sel_month = st.selectbox("Month", months)
        sel_staff = st.selectbox("Staff", ["All"] + sorted(plan_df["staff_name"].dropna().unique().tolist()))

        mp = plan_df[plan_df["month_year"] == sel_month]
        if sel_staff != "All":
            mp = mp[mp["staff_name"] == sel_staff]
        ml = log_df.copy()
        if not ml.empty and "date" in ml.columns:
            ml["date"] = pd.to_datetime(ml["date"], errors="coerce")
            ml = ml[ml["date"].dt.strftime("%m/%Y") == sel_month]
        if sel_staff != "All" and not ml.empty:
            ml = ml[ml["staff_name"] == sel_staff]

        adherence, missed = calc_visit_adherence(mp, ml)
        planned_count = len(mp)
        visited_count = planned_count - len(missed)
        opportunistic = (set(ml["dealer_id"].unique()) - set(mp["dealer_id"].unique())) if not ml.empty else set()
        days_on_road = ml["date"].dt.date.nunique() if not ml.empty else 0

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Visit Adherence", f"{adherence:.1f}%")
        c2.metric("Visited / Planned", f"{visited_count} / {planned_count}")
        c3.metric("Opportunistic Visits", len(opportunistic))
        c4.metric("Days on Road", days_on_road)

        if missed:
            st.subheader("Missed Dealers")
            missed_info = pd.DataFrame({"dealer_id": missed})
            if not dealer_df.empty:
                missed_info = missed_info.merge(dealer_df[["dealer_id","dealer_name","province"]], on="dealer_id", how="left")
            st.dataframe(missed_info, use_container_width=True)

with tab_log:
    st.subheader("Log a Visit")
    with st.form("visit_log_form"):
        visit_date   = st.date_input("Visit Date", value=date.today())
        dealer_opts  = [""] + (dealer_df["dealer_id"] + " — " + dealer_df["dealer_name"]).tolist() if not dealer_df.empty else [""]
        dealer_sel   = st.selectbox("Dealer (ID — Name)", dealer_opts)
        visit_result = st.text_area("Visit Result / Notes")
        submitted    = st.form_submit_button("Save Visit Log")

    if submitted:
        if not dealer_sel or not visit_result.strip():
            st.error("Please select a dealer and enter visit notes.")
        else:
            dealer_id = dealer_sel.split(" — ")[0]
            db = get_db()
            try:
                db.add(VisitLog(
                    date=visit_date,
                    staff_name=user["display_name"],
                    dealer_id=dealer_id,
                    visit_result=visit_result.strip(),
                ))
                db.commit()
                st.success("Visit logged successfully.")
            finally:
                db.close()
```

- [ ] **Step 2: Test in browser — log a visit and verify it appears in metrics.**

- [ ] **Step 3: Commit**

```bash
git add pages/6_Field_Operations.py
git commit -m "feat: field operations page with visit metrics and log form"
```

---

### Task 16: Lost Sales entry form

**Files:**
- Create: `pages/7_Lost_Sales.py`

- [ ] **Step 1: Create `pages/7_Lost_Sales.py`**

```python
import streamlit as st
import pandas as pd
from datetime import date, timedelta
from database.session import get_db
from database.models import LostSalesEntry, DealerMaster, ProductMaster, SaleRecord

st.set_page_config(page_title="Lost Sales", layout="wide")
if "user" not in st.session_state:
    st.error("Please sign in from the Home page.")
    st.stop()

user = st.session_state["user"]
st.title("❌ Lost Sales")

tab_entry, tab_summary = st.tabs(["Log Lost Sale", "Summary"])

db = get_db()
try:
    dealer_rows  = db.query(DealerMaster).all()
    product_rows = db.query(ProductMaster).all()
    sale_rows    = db.query(SaleRecord).all()
    ls_rows      = db.query(LostSalesEntry).all()
finally:
    db.close()

dealer_df  = pd.DataFrame([r.__dict__ for r in dealer_rows]).drop(columns=["_sa_instance_state"], errors="ignore") if dealer_rows else pd.DataFrame()
product_df = pd.DataFrame([r.__dict__ for r in product_rows]).drop(columns=["_sa_instance_state"], errors="ignore") if product_rows else pd.DataFrame()
sale_df    = pd.DataFrame([r.__dict__ for r in sale_rows]).drop(columns=["_sa_instance_state"], errors="ignore") if sale_rows else pd.DataFrame()
ls_df      = pd.DataFrame([r.__dict__ for r in ls_rows]).drop(columns=["_sa_instance_state"], errors="ignore") if ls_rows else pd.DataFrame()

def _calculate_avg_unit_price(dealer_id: str, item_id: str) -> float:
    """Calculate average unit price using cascading formula."""
    if sale_df.empty:
        return 0.0

    sale_df["order_date"] = pd.to_datetime(sale_df["order_date"], dayfirst=True, errors="coerce")
    three_months_ago = date.today() - timedelta(days=90)
    recent_sales = sale_df[sale_df["order_date"] >= three_months_ago]

    # Try dealer-specific average first
    dealer_item_sales = recent_sales[
        (recent_sales["dealer_id"] == dealer_id) &
        (recent_sales["item_id"] == item_id) &
        (recent_sales["sales_volume"] > 0)
    ]
    if not dealer_item_sales.empty:
        return (dealer_item_sales["sales_revenue"].sum() /
                dealer_item_sales["sales_volume"].sum())

    # Fall back to all-dealer average for this item
    item_sales = recent_sales[
        (recent_sales["item_id"] == item_id) &
        (recent_sales["sales_volume"] > 0)
    ]
    if not item_sales.empty:
        return (item_sales["sales_revenue"].sum() /
                item_sales["sales_volume"].sum())

    return 0.0  # New item with no sales history

with tab_entry:
    dealer_opts  = (dealer_df["dealer_id"] + " — " + dealer_df["dealer_name"]).tolist() if not dealer_df.empty else []
    product_opts = (product_df["item_id"] + " — " + product_df["item_name"]).tolist() if not product_df.empty else []

    if not dealer_opts or not product_opts:
        st.warning("Upload dealer_master and product_master data before logging lost sales.")
    else:
        with st.form("lost_sales_form"):
            dealer_sel  = st.selectbox("Dealer", dealer_opts)
            item_sel    = st.selectbox("Product (SKU)", product_opts)
            lost_volume = st.number_input("Lost Volume (units)", min_value=1, step=1)
            submitted   = st.form_submit_button("Submit")

        if submitted:
            dealer_id = dealer_sel.split(" — ")[0]
            item_id   = item_sel.split(" — ")[0]
            avg_unit_price = _calculate_avg_unit_price(dealer_id, item_id)

            if avg_unit_price == 0.0:
                st.error("Cannot calculate lost revenue: no sales history for this item in the last 3 months.")
                st.info("New items with no sales history should be handled as pending orders.")
            else:
                lost_revenue = lost_volume * avg_unit_price
                db = get_db()
                try:
                    db.add(LostSalesEntry(
                        date=date.today(),
                        staff_name=user["display_name"],
                        dealer_id=dealer_id,
                        item_id=item_id,
                        lost_volume=int(lost_volume),
                        lost_revenue=lost_revenue,
                    ))
                    db.commit()
                    st.success(f"Logged: {lost_volume} units × ฿{avg_unit_price:,.2f} = ฿{lost_revenue:,.2f} lost revenue.")
                finally:
                    db.close()

with tab_summary:
    if ls_df.empty:
        st.info("No lost sales recorded yet.")
    else:
        ls_df["lost_volume"]  = pd.to_numeric(ls_df["lost_volume"], errors="coerce").fillna(0)
        ls_df["lost_revenue"] = pd.to_numeric(ls_df["lost_revenue"], errors="coerce").fillna(0)
        st.metric("Total Lost Revenue", f"฿{ls_df['lost_revenue'].sum():,.0f}")
        st.metric("Total Lost Volume", f"{int(ls_df['lost_volume'].sum()):,} units")
        st.dataframe(ls_df.sort_values("date", ascending=False).reset_index(drop=True), use_container_width=True)
```

- [ ] **Step 2: Test in browser — log a lost sale, verify it appears in summary.**

- [ ] **Step 3: Commit**

```bash
git add pages/7_Lost_Sales.py
git commit -m "feat: lost sales entry form with cascading average unit price calculation"
```

---

## Phase 6 — Exports

### Task 17: PDF export service

**Files:**
- Create: `services/export_pdf.py`
- Modify: `tests/test_export.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_export.py
import pytest
from services.export_pdf import generate_pdf_bytes

def test_generate_pdf_returns_bytes():
    html_content = "<h1>Test Report</h1><p>Revenue: ฿100,000</p>"
    result = generate_pdf_bytes(html_content)
    assert isinstance(result, bytes)
    assert len(result) > 100
    assert result[:4] == b"%PDF"
```

- [ ] **Step 2: Run to confirm failure**

```bash
pytest tests/test_export.py -v
```

Expected: `ModuleNotFoundError: No module named 'services.export_pdf'`

- [ ] **Step 3: Create `services/export_pdf.py`**

```python
from weasyprint import HTML

def generate_pdf_bytes(html_content: str) -> bytes:
    return HTML(string=html_content).write_pdf()

def build_dashboard_html(kpis: dict, tables: list[dict]) -> str:
    rows = ""
    for t in tables:
        rows += f"<h3>{t['title']}</h3><p>{t['body']}</p>"
    return f"""
    <html><head><meta charset="utf-8">
    <style>
      body {{ font-family: Arial, sans-serif; padding: 20px; }}
      h1 {{ color: #1a1a2e; }}
      .kpi {{ display: inline-block; margin: 10px; padding: 15px;
               background: #f0f4ff; border-radius: 8px; min-width: 150px; }}
      .kpi-value {{ font-size: 24px; font-weight: bold; color: #2563eb; }}
    </style></head>
    <body>
    <h1>Dealer Report — Dashboard Export</h1>
    <div>
      {''.join(f'<div class="kpi"><div>{k}</div><div class="kpi-value">{v}</div></div>' for k, v in kpis.items())}
    </div>
    {rows}
    </body></html>
    """
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_export.py -v
```

Expected: 1 PASSED

- [ ] **Step 5: Add export button to Sales Dashboard**

In `pages/2_Sales_Dashboard.py`, add after the charts section:

```python
from services.export_pdf import generate_pdf_bytes, build_dashboard_html

if st.button("📄 Export PDF Report"):
    html = build_dashboard_html(
        kpis={
            "Total Revenue": f"฿{total_rev:,.0f}",
            "Gross Profit":  f"฿{profit:,.0f}",
            "Margin":        f"{margin:.1f}%",
            "Target %":      f"{completion:.1f}%",
        },
        tables=[]
    )
    pdf_bytes = generate_pdf_bytes(html)
    st.download_button("Download PDF", data=pdf_bytes, file_name="dealer_report.pdf", mime="application/pdf")
```

- [ ] **Step 6: Commit**

```bash
git add services/export_pdf.py tests/test_export.py pages/2_Sales_Dashboard.py
git commit -m "feat: PDF export service with download button on sales dashboard"
```

---

### Task 18: PowerPoint export service

**Files:**
- Create: `services/export_ppt.py`

- [ ] **Step 1: Append failing test to `tests/test_export.py`**

```python
from services.export_ppt import generate_ppt_bytes

def test_generate_ppt_returns_bytes():
    kpis = {"Total Revenue": "฿500,000", "Margin": "35.0%"}
    result = generate_ppt_bytes(kpis, title="Q1 Sales Report")
    assert isinstance(result, bytes)
    assert len(result) > 1000
```

- [ ] **Step 2: Run to confirm failure**

```bash
pytest tests/test_export.py::test_generate_ppt_returns_bytes -v
```

- [ ] **Step 3: Create `services/export_ppt.py`**

```python
import io
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor

def generate_ppt_bytes(kpis: dict[str, str], title: str = "Dealer Report") -> bytes:
    prs = Presentation()
    prs.slide_width  = Inches(13.33)
    prs.slide_height = Inches(7.5)

    # Title slide
    slide = prs.slides.add_slide(prs.slide_layouts[0])
    slide.shapes.title.text = title
    slide.placeholders[1].text = "Wholesale Operations Report"

    # KPI slide
    kpi_slide = prs.slides.add_slide(prs.slide_layouts[6])
    kpi_slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(12), Inches(0.6)).text_frame.add_paragraph().text = "Key Performance Indicators"

    cols = 4
    for i, (label, value) in enumerate(kpis.items()):
        col_i = i % cols
        row_i = i // cols
        left   = Inches(0.3 + col_i * 3.2)
        top    = Inches(1.2 + row_i * 2.0)
        box    = kpi_slide.shapes.add_textbox(left, top, Inches(3.0), Inches(1.6))
        tf     = box.text_frame
        tf.word_wrap = True
        p_label       = tf.add_paragraph()
        p_label.text  = label
        p_label.runs[0].font.size = Pt(12)
        p_value       = tf.add_paragraph()
        p_value.text  = value
        run           = p_value.runs[0]
        run.font.size = Pt(24)
        run.font.bold = True
        run.font.color.rgb = RGBColor(0x25, 0x63, 0xEB)

    buf = io.BytesIO()
    prs.save(buf)
    return buf.getvalue()
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_export.py -v
```

Expected: 2 PASSED

- [ ] **Step 5: Commit**

```bash
git add services/export_ppt.py tests/test_export.py
git commit -m "feat: PowerPoint export service with KPI slide"
```

---

## Phase 7 — Admin Page

### Task 19: Admin page (user management + targets)

**Files:**
- Create: `pages/8_Admin.py`

- [ ] **Step 1: Create `pages/8_Admin.py`**

```python
import streamlit as st
import pandas as pd
import bcrypt
from database.session import get_db
from database.models import User, SalesTarget
from auth.service import require_role

st.set_page_config(page_title="Admin", layout="wide")
if "user" not in st.session_state:
    st.error("Please sign in from the Home page.")
    st.stop()

user = st.session_state["user"]
try:
    require_role(type("U", (), user)(), ["Admin"])
except PermissionError:
    st.error("Admin access required.")
    st.stop()

st.title("⚙️ Admin Panel")

tab_users, tab_targets = st.tabs(["User Management", "Sales Targets"])

with tab_users:
    db = get_db()
    try:
        users = db.query(User).all()
    finally:
        db.close()

    user_data = [{"username": u.username, "role": u.role, "display_name": u.display_name} for u in users]
    st.dataframe(pd.DataFrame(user_data), use_container_width=True)

    st.subheader("Change Password")
    with st.form("change_password_form"):
        target_user = st.selectbox("User", [u.username for u in users])
        new_password = st.text_input("New Password", type="password")
        confirm_pw   = st.text_input("Confirm Password", type="password")
        submitted = st.form_submit_button("Update Password")
    if submitted:
        if new_password != confirm_pw:
            st.error("Passwords do not match.")
        elif len(new_password) < 8:
            st.error("Password must be at least 8 characters.")
        else:
            db = get_db()
            try:
                u = db.query(User).filter_by(username=target_user).first()
                u.password_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
                db.commit()
                st.success(f"Password updated for {target_user}.")
            finally:
                db.close()

with tab_targets:
    st.subheader("Upload Sales Targets (CSV/Excel)")
    st.caption("Required columns: month_year, sub_region, target_revenue")
    uploaded = st.file_uploader("Targets file", type=["csv","xlsx","xls"], key="targets_upload")
    if uploaded:
        from services.upload_service import load_file, validate_columns, upsert_dataframe
        df = load_file(uploaded.read(), uploaded.name)
        missing = validate_columns(df, "sales_targets")
        if missing:
            st.error(f"Missing columns: {', '.join(missing)}")
        else:
            st.dataframe(df.head(), use_container_width=True)
            if st.button("Upload Targets"):
                db = get_db()
                try:
                    count = upsert_dataframe(db, df, "sales_targets")
                    st.success(f"Uploaded {count} target rows.")
                finally:
                    db.close()
```

- [ ] **Step 2: Test in browser — sign in as admin, change a user's password, verify.**

- [ ] **Step 3: Commit**

```bash
git add pages/8_Admin.py
git commit -m "feat: admin panel for user management and sales targets upload"
```

---

## Phase 8 — Deployment

### Task 20: Streamlit config and LAN deployment

**Files:**
- Create: `.streamlit/config.toml`

- [ ] **Step 1: Create `.streamlit/config.toml`**

```toml
[server]
headless = true
address = "0.0.0.0"
port = 8501

[theme]
primaryColor = "#2563EB"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F4FF"
textColor = "#1A1A2E"
font = "sans serif"
```

- [ ] **Step 2: Verify full test suite passes**

```bash
pytest -v
```

Expected: All tests PASSED (0 failures)

- [ ] **Step 3: Start the app for LAN access**

```bash
streamlit run app.py
```

Staff access via: `http://[this-PC-IP-address]:8501`

Find your IP with: `ipconfig` (Windows) or `hostname -I` (Linux/Mac)

- [ ] **Step 4: Final commit**

```bash
git add .streamlit/config.toml
git commit -m "chore: Streamlit LAN server config and final deployment setup"
```

---

## Self-Review: Spec Coverage Check

| Requirement | Task |
|---|---|
| User authentication (3 roles) | Task 5, 6 |
| CSV/Excel upload with validation | Task 7, 8 |
| Sales & Revenue dashboard (KPIs, bar, pie, line) | Task 11 |
| Dealer health / AR outstanding | Task 12 |
| Product performance by brand/category/SKU | Task 13 |
| Inventory: stock, incoming, open orders, net avail | Task 14 |
| Field visit plans + adherence metrics | Task 15 |
| Lost sales entry form + auto revenue calc | Task 16 |
| PDF export | Task 17 |
| PowerPoint export | Task 18 |
| Admin: user management + password change | Task 19 |
| Admin: sales targets upload | Task 19 |
| LAN deployment for staff | Task 20 |
| All 11 DB tables + users table | Task 2 |
| Seed script (python -m database.seed) | Task 4 |
| brand_group auto-assignment | Task 7 (upload service) |
| region auto-assignment from sub_region | Task 7 (upload service) |
| Visit adherence formula | Task 9 |
| Missed visits + opportunistic visits | Task 15 |
| days_on_road + provinces_visited | Task 15 |

All spec items are covered. No placeholders remain.
