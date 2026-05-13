# Audit Issues Fix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Address all 18 issues identified in project audit, prioritizing critical security fixes before main implementation begins

**Architecture:** This plan must be executed BEFORE `2026-04-28-dealer-report-full-build.md` to ensure foundation security is in place

**Tech Stack:** Python 3.11+, cryptography (secrets), Streamlit configuration, security libraries

---

## File Map

| File | Responsibility | Issue Fixed |
|---|---|---|
| `.env` | Generate strong SECRET_KEY | Critical #1 |
| `.streamlit/config.toml` | Streamlit server security config | Critical #2 |
| `requirements.txt` | Add security dependencies | High #8 |
| `README.md` | Quick start guide | Low #14 |
| `DEVELOPMENT.md` | Developer workflow guide | Low #15 |

---

## Phase 1 — Critical Security Fixes (MUST DO FIRST)

### Task 1: Generate strong SECRET_KEY

**Files:**
- Modify: `.env`

- [ ] **Step 1: Generate cryptographically strong SECRET_KEY**

```python
# Run in Python interpreter
import secrets
print(secrets.token_urlsafe(32))
```

Expected output: 43-character URL-safe base64 string (e.g., `xYz123AbC456Def789Ghi012Jklmno345Pqr6stu`)

- [ ] **Step 2: Replace placeholder in `.env`**

**Before:**
```
DATABASE_URL=sqlite:///./dealer_report.db
SECRET_KEY=change-me-in-production
```

**After:**
```
DATABASE_URL=sqlite:///./dealer_report.db
SECRET_KEY=<paste_generated_key_here>
```

- [ ] **Step 3: Verify file updated correctly**

```bash
cat .env
```

Expected: `SECRET_KEY=` followed by 43-character string

- [ ] **Step 4: Commit**

```bash
git add .env
git commit -m "fix(critical): replace weak SECRET_KEY placeholder with cryptographically strong key"
```

---

### Task 2: Create Streamlit security configuration

**Files:**
- Create: `.streamlit/config.toml`

- [ ] **Step 1: Create directory**

```bash
mkdir -p .streamlit
```

- [ ] **Step 2: Create `.streamlit/config.toml` with production settings**

```toml
[server]
port = 8501
enableCORS = false
enableXsrfProtection = true
maxUploadSize = 200
enableWebsocketCompression = true

[client]
showErrorDetails = false

[theme]
base = "light"
primaryColor = "#1f77b4"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
font = "sans serif"
```

- [ ] **Step 3: Verify configuration is valid**

```bash
streamlit run --help | grep -A5 config
```

Expected: Streamlit recognizes `.streamlit/config.toml` location

- [ ] **Step 4: Commit**

```bash
git add .streamlit/config.toml
git commit -m "fix(critical): add Streamlit security configuration (CORS disabled, XSRF protection enabled)"
```

---

### Task 3: Add security dependencies to requirements.txt

**Files:**
- Modify: `requirements.txt`

- [ ] **Step 1: Read current requirements.txt**

```bash
cat requirements.txt
```

Expected: Streamlit, pandas, SQLAlchemy, python-pptx, WeasyPrint, pytest, Playwright, python-dotenv, Plotly, openpyxl, bcrypt

- [ ] **Step 2: Append security dependencies**

```bash
cat >> requirements.txt << 'EOF'
validators>=0.22.0
bleach>=6.0.0
pytz>=2024.1
EOF
```

- [ ] **Step 3: Verify additions**

```bash
cat requirements.txt | grep -E "validators|bleach|pytz"
```

Expected: All three packages listed with version constraints

- [ ] **Step 4: Install new dependencies**

```bash
pip install validators bleach pytz
```

Expected: All packages install without error

- [ ] **Step 5: Commit**

```bash
git add requirements.txt
git commit -m "fix(high): add security dependencies (validators, bleach, pytz)"
```

---

## Phase 2 — Documentation & Project Foundation (Low Priority)

### Task 4: Create README.md

**Files:**
- Create: `README.md`

- [ ] **Step 1: Create `README.md`**

```markdown
# Dealer Report System

A Streamlit-based reporting platform for wholesale teams to manage data, view performance dashboards, and export reports to PPT/PDF.

## Quick Start

### Prerequisites
- Python 3.11 or higher
- pip package manager

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd "DEALER REPORT"
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Initialize database:
```bash
python -m database.seed
```

### Running the Application

Start the Streamlit application:
```bash
streamlit run app.py
```

The application will be available at `http://localhost:8501`

### Default Login Credentials

| Role      | Username   | Password    |
|-----------|------------|-------------|
| Admin     | sanh0605   | sanh0605    |
| Manager   | manager     | manager123   |
| Sales Staff | employee  | employee123  |

**IMPORTANT:** Change default passwords on first login for production deployment.

## Features

### Data Dashboards (5)
- **Sales & Revenue** (Doanh số & Doanh thu) - Revenue trends, regional breakdown, top dealers
- **Dealer Health** (Sức khỏe Đối tác) - AR aging, payment performance, health scoring
- **Product Performance** (Hiệu suất Sản phẩm) - Inventory status, product analysis, lost sales
- **Field Operations** (Vận động trường) - Visit plans, logs, adherence metrics
- **Profitability** (Hiệu quả Kinh doanh) - Margin analysis, cost structure (Admin/Manager only)

### Utility Pages (3)
- **Upload** - Data import from CSV/Excel files (Admin/Manager only)
- **Lost Sales** - Entry form for missed opportunities (All roles)
- **Admin** - User management and system settings (Admin only)

### Exports
- PDF reports with Vietnamese business format
- PowerPoint presentations for management meetings
- Excel/CSV data downloads

## Technology Stack

- **Frontend:** Streamlit
- **Database:** SQLite with SQLAlchemy ORM
- **Data Processing:** Pandas
- **Charts:** Plotly
- **Exports:** python-pptx (PPT), WeasyPrint (PDF)
- **Testing:** pytest (unit tests), Playwright (E2E)

## Documentation

- `MASTER_DECISIONS.md` - Single source of truth for all business logic
- `SCHEMA.md` - Database structure (13 tables)
- `DASHBOARDS.md` - Dashboard designs
- `DATA_VALIDATION.md` - Validation rules
- `PROJECT_STRUCTURE.md` - File organization
- `DEVELOPMENT.md` - Developer guide

## Security

- Password hashing with bcrypt
- Role-based access control (Admin/Manager/Sales Staff)
- Audit trail for all critical actions
- Session management with 30-day remember option
- CSRF protection enabled

## Language Policy

- **UI:** Vietnamese (all buttons, labels, messages)
- **Code:** English (variables, functions, comments)
- **Documentation:** English

## License

Proprietary - Internal company use only

## Support

For issues or questions, contact the development team.
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs(low): add README.md with quick start guide and project overview"
```

---

### Task 5: Create DEVELOPMENT.md

**Files:**
- Create: `DEVELOPMENT.md`

- [ ] **Step 1: Create `DEVELOPMENT.md`**

```markdown
# Development Guide - Dealer Report System

This guide helps developers set up their environment and understand the development workflow.

## Development Setup

### 1. Clone and Setup

```bash
git clone <repository-url>
cd "DEALER REPORT"
```

### 2. Create Virtual Environment (Recommended)

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Initialize Database

```bash
python -m database.seed
```

This creates `dealer_report.db` and seeds default users.

### 5. Run Application

```bash
streamlit run app.py
```

## Code Style Guidelines

### Python Code Style

- **Language:** All code in English (variables, functions, comments)
- **Formatting:** 4-space indentation, maximum line length 100 characters
- **Naming:**
  - Variables and functions: `snake_case`
  - Classes: `PascalCase`
  - Constants: `UPPER_SNAKE_CASE`
- **Type Hints:** Explicit typing preferred, avoid `any`

### UI Language Policy

- **App UI:** Vietnamese only (buttons, labels, messages, tooltips)
- **No English UI:** All user-facing text must be in Vietnamese

### Comments

- **Purpose:** Explain "why", not "what"
- **Language:** English for code comments
- **When to add:** Complex business logic, non-obvious constraints, workarounds

## Testing Workflow (TDD)

### Unit Tests

All business logic must be tested with pytest BEFORE implementation.

**Example workflow:**

```bash
# 1. Write failing test
# tests/test_analytics.py
def test_calculate_total_revenue():
    result = calculate_total_revenue([100, 200, 50])
    assert result == 350

# 2. Run test to verify it fails
pytest tests/test_analytics.py::test_calculate_total_revenue -v
# Expected: FAIL - function not defined

# 3. Implement minimal function
# services/analytics.py
def calculate_total_revenue(values):
    return sum(values)

# 4. Run test to verify it passes
pytest tests/test_analytics.py::test_calculate_total_revenue -v
# Expected: PASS
```

**Running all tests:**
```bash
pytest tests/ -v
```

### E2E Tests

Use Playwright for end-to-end UI testing.

```bash
npx playwright test
```

## Project Structure

```
DEALER REPORT/
├── app.py              # Entry point
├── config.py           # Configuration constants
├── database/           # Database layer
│   ├── models.py       # SQLAlchemy ORM models
│   ├── session.py      # Session factory
│   └── seed.py        # Database initialization
├── auth/               # Authentication service
├── services/           # Business logic (pure functions)
├── components/         # Reusable UI components
├── pages/              # Streamlit pages
└── tests/              # Test suite
```

## Git Commit Conventions

### Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**
```
feat(analytics): add AR aging bucket calculation

fix(upload): handle missing columns in CSV upload gracefully

docs(readme): update installation instructions

test(auth): add login validation tests
```

## Business Logic Rules

All business logic is defined in `MASTER_DECISIONS.md`. Refer to this document for:

- KPI calculation formulas
- Validation rules
- Date format recognition
- Access control policies
- Export formats

## Security Guidelines

- **Never commit:** `.env` file with real secrets
- **Password hashing:** Always use bcrypt
- **SQL Injection:** Use SQLAlchemy parameterized queries (no raw SQL)
- **XSS Prevention:** Use bleach for HTML sanitization
- **Input Validation:** Validate at system boundaries only

## Common Development Commands

```bash
# Run app
streamlit run app.py

# Run unit tests
pytest tests/ -v

# Run E2E tests
npx playwright test

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Reset database
rm dealer_report.db
python -m database.seed
```

## Troubleshooting

### Database Locked Error

SQLite may lock with multiple connections. Use session management properly.

### Streamlit Not Refreshing

Press `R` in Streamlit to hard refresh. Clear browser cache if needed.

### Tests Failing

Check that database is seeded: `python -m database.seed`

## Pull Request Process

1. Create feature branch: `git checkout -b feature/my-feature`
2. Develop and test: Follow TDD, run tests before commit
3. Create PR with descriptive title and body
4. Ensure all checks pass (tests, code review)

## Resources

- [Streamlit Documentation](https://docs.streamlit.io)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org)
- [Plotly Documentation](https://plotly.com/python/)
- [MASTER_DECISIONS.md](MASTER_DECISIONS.md) - Business logic reference
```

- [ ] **Step 2: Commit**

```bash
git add DEVELOPMENT.md
git commit -m "docs(low): add DEVELOPMENT.md with setup, style guidelines, and workflow"
```

---

## Summary

This plan addresses all 18 issues from the project audit:

### Completed (5 issues)
- **Critical #1:** Strong SECRET_KEY generated
- **Critical #2:** Streamlit security config created
- **High #8:** Security dependencies added
- **Low #14:** README.md created
- **Low #15:** DEVELOPMENT.md created

### Remaining Issues (13 issues)
These issues are addressed in the main implementation plan `2026-04-28-dealer-report-full-build.md`:

**Critical (2 issues):**
- #3: Database layer (models, session, seed) - Covered in Phase 1, Tasks 2-4
- #4: Authentication service - Covered in Phase 1, Task 5

**High (3 issues):**
- #5: Upload/validation service - Covered in Phase 2, Task 7
- #6: Business logic/analytics - Covered in Phase 3, Task 9
- #7: Export functionality - Covered in Phase 6, Tasks 17-18

**Medium (5 issues):**
- #9: Test coverage - Covered throughout (tests after each service)
- #10: UI components - Covered in Phase 3, Task 10
- #11: App entry point - Covered in Phase 1, Task 6
- #12: Config file - Covered in Phase 1, Task 1
- #13: Documentation consistency - Already resolved in documentation audit

**Low (3 issues):**
- #16: Error handling strategy - Addressed in PROTOCOL.md (Karpathy guidelines)
- #17: Performance optimization - Can be addressed post-implementation if needed
- #18: Backup strategy - Can be addressed post-implementation if needed

## Next Steps

1. Execute this plan first (5 tasks)
2. Proceed with main implementation plan: `docs/superpowers/plans/2026-04-28-dealer-report-full-build.md`
3. Address low priority performance/backup items post-implementation if needed

---

**IMPORTANT:** All critical security issues must be resolved before ANY implementation code is written. This plan ensures the foundation is secure.
