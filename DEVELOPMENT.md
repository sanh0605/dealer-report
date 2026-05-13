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
