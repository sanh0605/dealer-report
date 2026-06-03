# Streamlit Cloud Deployment Fix

## Problem
App at `dealerapp.streamlit.app` fails with "Error installing requirements." The `pip install` returns non-zero exit code during dependency installation on Streamlit Cloud.

## Root Cause
1. **Dev dependencies in production requirements**: `pytest` and `pytest-playwright` are in `requirements.txt`. Playwright downloads browser binaries (Chromium, Firefox, WebKit) during `pip install`, which fails on Streamlit Cloud's restricted environment.
2. **Missing `runtime.txt`**: No Python version pinned, so Streamlit Cloud uses its default which may cause compatibility issues.
3. **Incorrect version specifier**: `st-gsheets-connection>=0.0.36` references a version that doesn't exist on PyPI (available: 0.1.0, 0.0.4, 0.0.3).

## Fix
1. Remove `pytest` and `pytest-playwright` from `requirements.txt`
2. Create `requirements-dev.txt` with dev-only packages
3. Fix `st-gsheets-connection` to `>=0.0.3` (or pin to `==0.1.0`)
4. Add `runtime.txt` to pin Python version to 3.12

## Files Changed
- `requirements.txt` -- remove dev deps, fix version specifier
- `requirements-dev.txt` -- new file for dev dependencies
- `runtime.txt` -- new file pinning Python version
