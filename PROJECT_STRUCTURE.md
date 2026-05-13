# PROJECT_STRUCTURE.md - Project Directory & File Organization

**Last Updated:** 2026-05-08 (Updated with YEAR_TARGET_REPORT.md)  
**Purpose:** Complete project structure reference - what exists and what will be created  
**Status:** Planning phase complete, ready for implementation

---

## 📁 Current Project Structure (What Exists NOW)

```
DEALER REPORT/
├── .env                                    # Environment variables (DB URL, SECRET_KEY)
├── requirements.txt                        # Python dependencies
│
├── CLAUDE.md                               # Project overview & tech stack
├── MASTER_DECISIONS.md ⭐                  # Single source of truth - ALL business logic
├── SCHEMA.md                               # Database structure (13 tables)
├── SECURITY.md                             # Security implementation details
├── DASHBOARDS.md                           # 5 dashboard designs (Vietnamese UI)
├── DATA_VALIDATION.md                      # Table-specific validation rules
├── DOCUMENTATION_INDEX.md                  # Navigation guide for all documentation
├── PROTOCOL.md                             # Development workflow & guidelines
├── PROJECT_STRUCTURE.md                    # This file - complete project structure
├── YEAR_TARGET_REPORT.md                   # Year Target Observation Report specification
│
├── docs/
│   └── superpowers/
│       └── plans/
│           └── 2026-04-28-dealer-report-full-build.md  # Detailed implementation plan (2,067 lines)
│
└── sample_data/                            # Directory for sample CSV/Excel files (EMPTY - awaiting user data)
```

---

## 🏗️ Planned Project Structure (What Will Be Created)

```
DEALER REPORT/
├── app.py                                  # Streamlit entry point with auth gate
├── config.py                               # Configuration constants and mappings
├── requirements.txt                        # Python dependencies (EXISTS)
├── .env                                    # Environment variables (EXISTS)
│
├── database/                               # Database layer
│   ├── __init__.py                         # Package initialization
│   ├── models.py                           # SQLAlchemy ORM models (11 tables)
│   ├── session.py                          # Database session factory
│   └── seed.py                             # Seed script for initial data
│
├── auth/                                   # Authentication & authorization
│   ├── __init__.py                         # Package initialization
│   └── service.py                          # Login, session management, role checking
│
├── services/                               # Business logic (pure functions)
│   ├── __init__.py                         # Package initialization
│   ├── upload_service.py                   # CSV/Excel upload with validation
│   ├── analytics.py                        # KPI calculations and metrics
│   ├── export_pdf.py                       # PDF export service (WeasyPrint)
│   └── export_ppt.py                       # PowerPoint export service (python-pptx)
│
├── components/                             # Reusable UI components
│   ├── __init__.py                         # Package initialization
│   ├── charts.py                           # Plotly chart builders
│   └── kpi_cards.py                        # KPI card rendering components
│
├── pages/                                  # Streamlit multi-page app
│   ├── 1_Upload.py                         # Data upload page (Admin/Manager only)
│   ├── 2_Sales_Dashboard.py                # Sales & Revenue Dashboard
│   ├── 3_Dealer_Health.py                  # Dealer Health Dashboard
│   ├── 4_Product_Performance.py            # Product Performance Dashboard (includes inventory status)
│   ├── 5_Profitability_Dashboard.py        # Profitability Dashboard (Admin/Manager only)
│   ├── 6_Field_Operations.py               # Field visit plans & logs
│   ├── 7_Lost_Sales.py                     # Lost sales entry form
│   └── 8_Admin.py                          # Admin panel (user management, targets)
│
├── tests/                                  # Test suite
│   ├── __init__.py                         # Package initialization
│   ├── test_models.py                      # ORM model tests
│   ├── test_auth.py                        # Authentication service tests
│   ├── test_upload_service.py               # Upload validation tests
│   ├── test_analytics.py                   # KPI calculation tests
│   ├── test_export.py                      # PDF/PPT export tests
│   └── e2e/                                # End-to-end tests
│       ├── __init__.py                     # Package initialization
│       └── test_app.spec.ts                # Playwright E2E tests
│
├── docs/                                   # Documentation (EXISTS)
│   └── superpowers/
│       └── plans/
│           └── 2026-04-28-dealer-report-full-build.md  # Implementation plan (EXISTS)
│
├── sample_data/                            # Sample data directory (EXISTS, EMPTY)
│
├── CLAUDE.md                               # Project overview (EXISTS)
├── MASTER_DECISIONS.md ⭐                  # Single source of truth (EXISTS)
├── SCHEMA.md                               # Database schema (EXISTS)
├── SECURITY.md                             # Security requirements (EXISTS)
├── DASHBOARDS.md                           # Dashboard designs (EXISTS)
├── DATA_VALIDATION.md                      # Validation rules (EXISTS)
├── DOCUMENTATION_INDEX.md                  # Documentation navigation (EXISTS)
├── PROTOCOL.md                             # Development guidelines (EXISTS)
└── PROJECT_STRUCTURE.md                    # This file (NEW)
```

---

## 📊 Current vs Planned Structure Comparison

### **Currently Exists (Planning Phase):**
- ✅ Documentation: 9 markdown files
- ✅ Configuration: 2 files (.env, requirements.txt)
- ✅ Implementation plan: 1 comprehensive guide
- ✅ Directory structure: docs/, sample_data/ (empty)
- ❌ **NO CODE FILES YET**

### **Will Be Created (Implementation Phase):**
- 📝 Python application code: 18+ files
- 📝 Database layer: 4 files (models, session, seed)
- 📝 Authentication service: 2 files
- 📝 Business logic services: 5 files
- 📝 UI components: 3 files
- 📝 Dashboard pages: 8 files
- 📝 Test suite: 7+ files
- 📝 Streamlit configuration: .streamlit/config.toml

---

## 🎯 File-by-File Breakdown

### **Root Application Files:**

| File | Purpose | Status |
|------|---------|--------|
| `app.py` | Streamlit entry point, auth gate, page navigation | ⏳ To Create |
| `config.py` | Configuration constants, brand/region mappings | ⏳ To Create |
| `requirements.txt` | Python dependencies | ✅ Exists |
| `.env` | Environment variables (DB URL, SECRET_KEY) | ✅ Exists |

---

### **Database Layer (`database/`):**

| File | Purpose | Status |
|------|---------|--------|
| `database/__init__.py` | Package initialization | ⏳ To Create |
| `database/models.py` | 11 SQLAlchemy ORM models | ⏳ To Create |
| `database/session.py` | Database session factory, engine setup | ⏳ To Create |
| `database/seed.py` | Seed script for default users | ⏳ To Create |

**Database Models (11 tables):**
1. SaleRecord
2. AccountsReceivableLedger
3. ProductMaster
4. DealerMaster
5. SalesTarget
6. InventoryStatus
7. IncomingShipment
8. OpenOrder
9. LostSalesEntry
10. FieldVisitPlan
11. VisitLog
12. User (for authentication)

---

### **Authentication Layer (`auth/`):**

| File | Purpose | Status |
|------|---------|--------|
| `auth/__init__.py` | Package initialization | ⏳ To Create |
| `auth/service.py` | Login, session management, role checking | ⏳ To Create |

**Auth Functions:**
- `login()` - Password verification with bcrypt
- `get_session_user()` - Get current user from session
- `require_role()` - Role-based access control

---

### **Business Logic Services (`services/`):**

| File | Purpose | Status |
|------|---------|--------|
| `services/__init__.py` | Package initialization | ⏳ To Create |
| `services/upload_service.py` | CSV/Excel upload, validation, upsert | ⏳ To Create |
| `services/analytics.py` | KPI calculations (pure functions) | ⏳ To Create |
| `services/export_pdf.py` | PDF generation (WeasyPrint) | ⏳ To Create |
| `services/export_ppt.py` | PowerPoint generation (python-pptx) | ⏳ To Create |

**Key Functions:**
- `load_file()` - Load CSV/Excel into DataFrame
- `validate_columns()` - Check required columns
- `upsert_dataframe()` - Insert/update database records
- `calc_total_revenue()` - Revenue calculation
- `calc_gross_profit()` - Profit and margin calculation
- `calc_target_completion()` - Target vs actual comparison
- `calc_ar_outstanding()` - Accounts receivable balance
- `calc_visit_adherence()` - Visit completion rate
- `generate_pdf_bytes()` - Convert HTML to PDF
- `generate_ppt_bytes()` - Create PowerPoint presentation

---

### **UI Components (`components/`):**

| File | Purpose | Status |
|------|---------|--------|
| `components/__init__.py` | Package initialization | ⏳ To Create |
| `components/charts.py` | Reusable Plotly chart builders | ⏳ To Create |
| `components/kpi_cards.py` | KPI card rendering components | ⏳ To Create |

**Chart Functions:**
- `bar_chart()` - Bar chart builder
- `pie_chart()` - Pie chart builder
- `line_chart()` - Line chart builder
- `treemap_chart()` - Treemap chart builder

---

### **Dashboard Pages (`pages/`):**

| File | Purpose | Access Level | Status |
|------|---------|--------------|--------|
| `pages/1_Upload.py` | Data upload interface | Admin/Manager | ⏳ To Create |
| `pages/2_Sales_Dashboard.py` | Sales & Revenue dashboard | All roles | ⏳ To Create |
| `pages/3_Dealer_Health.py` | Dealer health monitoring | All roles | ⏳ To Create |
| `pages/4_Product_Performance.py` | Product analytics + inventory status | All roles | ⏳ To Create |
| `pages/5_Profitability_Dashboard.py` | Profitability dashboard | Admin/Manager | ⏳ To Create |
| `pages/6_Field_Operations.py` | Visit plans & logs | All roles | ⏳ To Create |
| `pages/7_Lost_Sales.py` | Lost sales entry | All roles | ⏳ To Create |
| `pages/8_Admin.py` | User management | Admin only | ⏳ To Create |

---

### **Test Suite (`tests/`):**

| File | Purpose | Status |
|------|---------|--------|
| `tests/__init__.py` | Package initialization | ⏳ To Create |
| `tests/test_models.py` | ORM model creation tests | ⏳ To Create |
| `tests/test_auth.py` | Authentication service tests | ⏳ To Create |
| `tests/test_upload_service.py` | Upload validation tests | ⏳ To Create |
| `tests/test_analytics.py` | KPI calculation tests | ⏳ To Create |
| `tests/test_export.py` | PDF/PPT export tests | ⏳ To Create |
| `tests/e2e/__init__.py` | E2E package initialization | ⏳ To Create |
| `tests/e2e/test_app.spec.ts` | Playwright E2E tests | ⏳ To Create |

---

### **Documentation (`docs/` & Root):**

| File | Purpose | Status |
|------|---------|--------|
| `CLAUDE.md` | Project overview, tech stack, commands | ✅ Exists |
| `MASTER_DECISIONS.md` ⭐ | Single source of truth - ALL business logic | ✅ Exists |
| `SCHEMA.md` | Database schema (13 tables) | ✅ Exists |
| `SECURITY.md` | Security implementation requirements | ✅ Exists |
| `DASHBOARDS.md` | 5 dashboard designs (Vietnamese UI) | ✅ Exists |
| `DATA_VALIDATION.md` | Table-specific validation rules | ✅ Exists |
| `DOCUMENTATION_INDEX.md` | Navigation guide for all documentation | ✅ Exists |
| `PROTOCOL.md` | Development workflow & guidelines | ✅ Exists |
| `PROJECT_STRUCTURE.md` | Complete project structure reference | ✅ Exists |
| `YEAR_TARGET_REPORT.md` | Year Target Observation Report specification | ✅ New |
| `docs/superpowers/plans/2026-04-28-dealer-report-full-build.md` | Detailed implementation plan | ✅ Exists |

---

### **Configuration:**

| File | Purpose | Status |
|------|---------|--------|
| `.streamlit/config.toml` | Streamlit server configuration | ⏳ To Create |
| `requirements.txt` | Python dependencies | ✅ Exists |
| `.env` | Environment variables | ✅ Exists |

---

## 🔄 Implementation Order

### **Phase 1: Foundation** (6 tasks)
1. Project skeleton & dependencies
2. Database models & tests
3. Session factory
4. Seed script
5. Auth service & tests
6. App entry point

### **Phase 2: Data Management** (2 tasks)
7. Upload service & tests
8. Upload page UI

### **Phase 3: Analytics** (2 tasks)
9. Analytics service & tests
10. Chart & KPI components

### **Phase 4: Dashboards** (4 tasks)
11. Sales Dashboard
12. Dealer Health Dashboard
13. Product Performance Dashboard (includes inventory)
14. Profitability Dashboard (Admin/Manager only)

### **Phase 5: Field Operations** (2 tasks)
15. Field Operations page
16. Lost Sales page

### **Phase 6: Exports** (2 tasks)
17. PDF export service
18. PPT export service

### **Phase 7: Admin** (1 task)
19. Admin page

### **Phase 8: Deployment** (1 task)
20. Streamlit config & LAN setup

---

## 📝 Directory Creation Commands

```bash
# Create all directories
mkdir -p database auth services components pages tests/e2e
mkdir -p docs/superpowers/plans
mkdir -p sample_data
mkdir -p .streamlit

# Create all __init__.py files
touch database/__init__.py
touch auth/__init__.py
touch services/__init__.py
touch components/__init__.py
touch tests/__init__.py
touch tests/e2e/__init__.py
```

---

## 🔗 Related Documentation

- **For implementation steps:** See `docs/superpowers/plans/2026-04-28-dealer-report-full-build.md`
- **For database details:** See `SCHEMA.md`
- **For business logic:** See `MASTER_DECISIONS.md`
- **For dashboard designs:** See `DASHBOARDS.md`
- **For validation rules:** See `DATA_VALIDATION.md`
- **For security requirements:** See `SECURITY.md`
- **For documentation navigation:** See `DOCUMENTATION_INDEX.md`

---

## 📊 Project Statistics

**Current State (Planning Phase):**
- Total files: 15
- Code files: 0
- Documentation files: 10
- Configuration files: 2
- Directories: 3 (docs, docs/superpowers, docs/superpowers/plans)

**Final State (After Implementation):**
- Total files: 41+
- Code files: 25+
- Test files: 7+
- Documentation files: 11
- Configuration files: 3
- Directories: 8

---

**This document serves as the definitive reference for project structure. All file organization, creation order, and implementation details are documented here for easy reference.**
