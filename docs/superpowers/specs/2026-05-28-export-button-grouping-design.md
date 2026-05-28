# Export Button Grouping Design

## Summary
Group 3 export buttons (PPT, Excel, CSV) into a single `st.popover("Xuất dữ liệu")` dropdown. Remove the PDF export button entirely.

## Current State
In `views/2_Sales_Dashboard.py` (lines 352-391), 4 export buttons are laid out in `st.columns(4)`:
- Column 1: "Tạo báo cáo PDF"
- Column 2: "Tạo báo cáo PPT"
- Column 3: "Tạo báo cáo Excel"
- Column 4: "Tải CSV (Raw Data)"

## Changes

### Remove
- PDF export button and its logic (lines 352-367)
- Import of `export_pdf` module (line 348)
- The 4-column layout (`st.columns(4)`)

### Add
- Single `st.popover("Xuất dữ liệu")` containing 3 buttons in order:
  1. `st.button("Tạo báo cáo PPT")` -- calls `generate_ppt_bytes()`
  2. `st.button("Tạo báo cáo Excel")` -- calls `generate_dashboard_excel()`
  3. `st.download_button("Tải CSV (Raw Data)")` -- downloads CSV as-is

### Keep Unchanged
- All PPT, Excel, CSV export logic and parameters
- Imports: `export_ppt`, `export_excel`, `ui_utils`
- Everything else in the dashboard

## Approach
`st.popover` -- one click opens a small popup with the 3 options. Minimal code change, compact UI.

## Scope
Single file: `views/2_Sales_Dashboard.py`
