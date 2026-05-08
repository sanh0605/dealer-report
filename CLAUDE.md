# CLAUDE.md - Dealer Report System

## Project Overview
A Streamlit-based reporting platform for wholesale teams to manage data, view performance dashboards, and export reports to PPT/PDF.

## Tech Stack
- **Frontend:** Streamlit, Frontend-Design (Aesthetic focus)
- **Data Processing:** Pandas
- **Database:** SQLite (SQLAlchemy)
- **Exports:** python-pptx (PowerPoint), WeasyPrint (PDF)
- **Testing:** Playwright (Web), Pytest (TDD)
- **Expert Skills:** Brainstorming, Feature-Dev, Systematic-Debugging, TDD, Context7

## Key Workflows
- **Design:** Brainstorming -> Visual Mockups (via browser) -> Design Doc.
- **Development:** TDD (Failing test first) -> Implementation -> Automated Testing.
- **Debugging:** Systematic Root Cause Analysis (No guessing).
- **Documentation:** Fetch up-to-date info via Context7.

## Common Commands
- Run App: `streamlit run app.py`
- Seed Database: `python -m database.seed`
- Install Dependencies: `pip install -r requirements.txt`
- Run Tests: `pytest` or `npx playwright test`
- Fetch Docs: `curl -s "https://context7.com/api/v2/context?libraryId=LIB_ID&query=TOPIC&type=txt"`

## Language Policy
All app UI must be in Vietnamese (buttons, labels, charts, messages). For complete language policy and examples, see [MASTER_DECISIONS.md](MASTER_DECISIONS.md#language-policy).

## Important Notes
- **Single Source of Truth:** MASTER_DECISIONS.md contains all business logic, rules, and policies
- **Start Here:** Always begin with MASTER_DECISIONS.md for implementation requirements
- **Project Structure:** See PROJECT_STRUCTURE.md for complete file organization
- **Implementation Plan:** Follow docs/superpowers/plans/2026-04-28-dealer-report-full-build.md
