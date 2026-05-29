# Excel Report Redesign Spec

## Overview
Rewrite `services/export_excel.py` to generate a formatted Excel report matching the structure of "VX - DEALER REPORT" sample. No template copying -- generate from data.

## Data Sources
- `sale_records` (Google Sheets) -- primary sales data
- `dealer_master` (Google Sheets) -- dealer info, sub_region mapping
- `product_master` (Google Sheets) -- product_group mapping
- `sales_targets` (Google Sheets, NEW) -- target values per region/KPI
- `accounts_receivable` (Google Sheets, NEW) -- AR ledger for Doanh thu calculation

## Function Signature
```python
def generate_dashboard_excel(
    filtered_data: pd.DataFrame,      # data for selected period
    previous_filtered_data: pd.DataFrame,
    main_data: pd.DataFrame,          # full year data (for YTD)
    reference_date: datetime,          # the selected reference date
    selected_period_label: str,        # e.g. "Thang 05/2026"
) -> bytes:
```

## Sheet 1: Tong Quan (3 tables)

### Table 1: Ke Hoach 2026 (rows 1-10)
- Data: YTD from `sale_records`
- Columns: Chi so | Kenh ap dung | Target | Ket Qua | Tien do | Deadline
- Rows: Doanh so (Dai ly, Sieu thi), So luong xe (Dai ly, Sieu thi), So luong diem ban (Dai ly, Sieu thi), Clear hang ton kho
- Target from `sales_targets`, Ket Qua calculated from data

### Table 2: Thang XX/YYYY (rows 14-32)
- Data: **selected month only** for columns B-F; **YTD** for %LNG columns (G onwards)
- Columns: Khu Vuc | Doanh So | Target | % Target | LNG | % LNG | %LNG T1 | %LNG T2 | ... | %LNG YTD
- Rows: MB1+MB2, MB1, MB2, MB3+MB4, MB3, MB4, MN1+MN3, MN1, MN3, MN2, MN4+MN5+MN6, MN4, MN5, MN6, Sieu Thi, Grand Total
- %LNG columns show each month from T1 to selected month, plus YTD aggregate

### Table 3: Luy ke tu 01/01/YYYY - DD/MM/YYYY (rows 36-54)
- Data: YTD from start of year to end of selected month
- Columns: Khu Vuc | Doanh so | Doanh thu | % Thu hoi | Target | % Target
- Doanh so = sum(sales_revenue) from `sale_records`
- Doanh thu = sum(Deduction Amout + Paid Amout) from `accounts_receivable`, joined with `sale_records` on Order ID, filtered where sale_records has Date Transfer
- Group by sub_region, map to region groups
- Rows same structure as Table 2

## Sheet 2: Nhom San Pham
- Data: YTD, pivot by month (T1 to selected month + Grand Total)
- Structure: NHOM SAN PHAM | T1 | T2 | ... | Tn | Grand Total
- For each product_group (XE OEM, XE JAVA, XE GIANT, MAXXIS, PHU KIEN, KHAC):
  - Doanh so row
  - So luong row
  - % LNG row = (revenue - cost) / revenue

## Sheet 3: Top 10 KH - DS
- Data: YTD, pivot by month
- Structure: NHOM SAN PHAM | T1 | T2 | ... | Tn | Grand Total
- Top 10 dealers by Grand Total descending (overall, all product groups)
- Single value per cell: Doanh so
- Last row: Grand Total

## Sheet 4-7: Top 10 KH per brand (OEM, JAVA, GIANT, MAXXIS)
- Same structure as Sheet 3, filtered by product_group
- Each dealer has 2 rows: Doanh so + So luong
- Top 10 by Grand Total descending

## Sheet 8: RAW DATA
- Data: YTD from start of year to end of selected month
- Map columns from sale_records + dealer_master + product_master
- Headers matching template: Order Reference, Date Order, Date, Month, Sale Channel, Customer, Company Name, Dealer Region, Dealer Region Group, SKU, Brand, Brand Group, Category, Sub Category, Revenue, applied_cost, Gross Profit, Quantity, etc.

## Formatting
- **Borders**: thin borders on all data cells, thicker border on headers
- **Header row**: bold, white text on dark blue (#1F4E79) background
- **Sub-headers / section titles**: bold, light blue (#D6E4F0) background
- **Grand Total row**: bold, light yellow (#FFF2CC) background
- **Number format**: `#,##0` for currency (no "d" or "VND"), `#,##0.0%` for percentages, `#,##0` for quantities
- **Column width**: auto-fit based on content, min 12, max 30
- **Product group labels**: bold, merged cells across row, light gray (#F2F2F2) background
- **Negative values**: red font
- **Freeze panes**: header row frozen in RAW DATA sheet

## Implementation Notes
- Use openpyxl styles (Font, PatternFill, Border, Side, Alignment, numbers)
- Do NOT load/copy template file -- build workbook from scratch
- Pass `MainDataFrame` from dashboard to get full year data for YTD calculations
- YTD = filter MainDataFrame from Jan 1 of reference_date.year to end of selected month
- `accounts_receivable` read from Google Sheets at export time
- `sales_targets` read from Google Sheets at export time
