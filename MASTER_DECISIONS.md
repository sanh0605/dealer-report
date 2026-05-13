# MASTER_DECISIONS.md - All Business & Technical Decisions

**Last Updated:** 2026-05-11
**Purpose:** Single source of truth for all business logic, rules, policies, and implementation decisions
**Status:** ⭐ AUTHORITATIVE - All other documentation references this document
**Version:** 3.2 - Complete documentation audit resolution (inconsistencies, redundancies, ambiguities)

> **IMPORTANT:** This is the SINGLE SOURCE OF TRUTH for the entire project.
> - All business rules are defined here
> - All language policies are defined here  
> - All export formats are defined here
> - All user roles and permissions are defined here
> - All validation workflows are defined here
>
> Other documents (SCHEMA.md, SECURITY.md, DATA_VALIDATION.md) reference this document
> and focus on their specific areas (database structure, security implementation, validation rules).

This document summarizes all critical decisions made during requirements gathering and planning phase. These rules MUST be followed strictly during implementation.

---

## Database & Architecture

### **Database Technology**
- **Decision:** SQLite with SQLAlchemy ORM
- **Rationale:** Simple deployment, no external database server required, suitable for ~10 staff LAN environment
- **Configuration:** DATABASE_URL=sqlite:///./dealer_report.db

### **Schema Structure**
- **Total Tables:** 13 tables (11 business tables + 2 system tables)
- **Business Tables (11):** sale_records, accounts_receivable_ledger, product_master, dealer_master, sales_targets, inventory_status, incoming_shipments, open_orders, lost_sales_entry, field_visit_plans, visit_logs
- **System Tables (2):** users (authentication), audit_logs (security audit trail)
- **Key Changes from Original Plan:**
  - `unit_price_standard` moved from `product_master` to `sale_records`
  - `sales_targets` simplified to 4 fields: target_id, month_year, sub_region, target_revenue
  - `dealer_VX_id` added to `dealer_master` (optional text field)
  - `subcategory` in `product_master` is optional (not required)
  - `users` table added for authentication (12th table)
  - `audit_logs` table added for security audit trail (13th table)
  - `visit_logs.plan_id` added as optional field to distinguish planned vs ad-hoc visits

---

## Data Validation Rules

### **General Validation Principles**
- **Error Handling:** System has full rights to reject uploads with validation errors, but must warn about typing errors
- **Foreign Keys:** Prevent entry if ID doesn't exist in master tables
- **Decision Workflow:** For `sales_targets.sub_region` that doesn't exist in `dealer_master`:
  - Show warning: "Sub_region 'XYZ99' không tồn tại trong dealer_master"
  - User must click "Chấp nhận" (Accept) or "Từ chối" (Decline)
  - System remembers decision for future uploads
  - Auto-ignore warning if `dealer_master` is updated

### **Negative Values Policy**
- **Allowed:** All numeric fields can be negative to handle returns
- **Specific Fields:** `sales_volume`, `unit_price_standard`, `sales_revenue`, `cost_of_goods`, `paid_amount`, `refund_amount`, `deduction_amount`
- **Business Logic:** Returns are legitimate business transactions
- **KPI Handling:** Negative values are included in all KPI calculations (subtracted from totals)
  - Revenue KPIs: Include negative `sales_revenue` values (revenue - returns)
  - Volume KPIs: Include negative `sales_volume` values (sales - returns)
  - Profit KPIs: Include negative `cost_of_goods` values (proper return cost handling)
  - No exclusion of negative values from any business metrics
- **Exception:** `lost_sales_entry.lost_volume` must be positive (cannot have negative lost sales - lost sales represent missed opportunities, not returns)

### **Date Format Recognition**
- **Auto-Detection:** System recognizes multiple date formats automatically:
  - dd/mm/yyyy, dd/mm/yyyy hh:mm:ss
  - yyyy/mm/dd, yyyy/mm/dd hh:mm:ss
  - yyyy-mm-dd, yyyy-mm-dd hh:mm:ss
- **Conversion:** All dates converted to standard format for storage

### **Specific Table Validations**
See `DATA_VALIDATION.md` for complete validation rules for all 11 tables.

---

## Business Logic Decisions

### **Lost Sales Calculation**
1. **Warehouse Import Required:** Lost sales calculation starts after first successful import to `inventory_status` table for the specific item
   - **Trigger:** `inventory_status` table contains records for the item
   - **Definition:** "Warehouse import" = importing data into `inventory_status` table
   - **New Items Exception:** Items with no data in `inventory_status` cannot have lost sales logged
2. **New Items Exception:** New items with no sales history never logged as lost sales
3. **Cascading Revenue Formula:**
   - Step 1: Calculate `avg_revenue_per_unit` for `dealer_id` + `item_id` over last 3 months
   - Step 2: If dealer never purchased this item, use all-dealer average for this `item_id` over last 3 months
   - Step 3: Exclude new items with no sales history

### **Visit Adherence Definition**
1. **Structured Outcomes Required:** Staff must select from:
   - **Thành công (Success):** Sale made, relationship maintained
   - **Cần theo dõi (Follow-up):** Potential sale, needs follow-up
   - **Vấn đề tồn kho (Stock Issue):** Dealer needs inventory
   - **Thanh toán (Payment):** Payment collection discussion
   - **Khác (Other):** Other business discussed
2. **Free Notes Required:** Text field for additional context
3. **Completed Visit Definition:** Both structured outcome AND free notes required
4. **Ad-hoc Visits Allowed:** System permits visits to dealers not in monthly plan (marked as opportunistic visits)
5. **Visit Log Relationships:**
   - `visit_logs.plan_id` is optional (NULL for ad-hoc visits)
   - **Planned visits:** Have matching `plan_id` (counted in adherence)
   - **Ad-hoc visits:** `plan_id` is NULL (not counted in adherence, tracked separately)
   - **No strict foreign key constraint:** Plan may be deleted but visit log retained for historical purposes

### **AR Aging Configuration**
- **Configuration Storage:** Parameters stored in `config.py` as constants (not database)
  - `AR_BUCKET_SIZE = 30` (days per bucket)
  - `AR_MAX_DAYS = 180` (maximum days to display)
- **User-Configurable Parameters:**
  - `bucket_size`: Duration of each aging bucket (e.g., 30 days, 7 days)
  - `max_days`: Maximum days to display (e.g., 120 days, 150 days, 180 days)
- **Auto-Bucket Generation:** System creates buckets: 0-X, X-2X, 2X-3X... up to max_days, plus max_days+ bucket
- **Examples:**
  - bucket_size=30, max_days=90: 0-30, 30-60, 60-90, 90+ days
  - bucket_size=30, max_days=180: 0-30, 30-60, 60-90, 90-120, 120-150, 150-180, 180+ days
- **Future Enhancement:** Could add `system_settings` table for runtime configuration

### **Sales Records Business Rules**
- **Revenue Calculation:** Revenue calculated using `date_transfer` field (not `order_date`)
  - **Dashboard KPIs:** Always use `date_transfer` for revenue and all time-based calculations
  - **Order Date Usage:** `order_date` used for planning/scheduling purposes only
  - **Revenue Timing:** Revenue recognized when goods are shipped (`date_transfer` is set)
- **Order ID Duplication:** `order_id` naturally duplicates because one order contains multiple items
  - Unique identifier = `order_id + item_id` combination
  - **No Cross-Table Validation:** Different order_id states allowed across tables (sale_records, accounts_receivable_ledger, open_orders)
- **Returns Handling:** Negative values in all numeric fields to handle returns properly
  - **KPI Impact:** Negative values subtract from totals in all business metrics

---

## Security & Access Control

### **User Roles**
- **Admin (Quản trị viên):** Full system rights
- **Manager (Quản lý):** Business data management
- **Sales Staff (Nhân viên bán hàng):** Restricted access (no cost/profit data)

### **Password Policy**
- **Length:** 8-20 characters
- **Complexity:** Must include letters, numbers, special characters, uppercase, lowercase
- **Expiration:** Never expires
- **History:** Allow reuse of old passwords
- **Default Admin:** Created on first startup with username: `sanh0605`, password: `sanh0605`

### **Session Management**
- **Standard Session:** No timeout (stay logged in until logout)
- **Remember Me Feature:** Must include "Ghi nhớ tôi" checkbox
- **Remember Me Duration:** 30 days
- **Password Change:** Session expires immediately
- **Last Login Display:** Show "Đăng nhập lần cuối: [date/time]"
- **Logout Confirmation:** Must confirm before actually logging out

### **Dashboard Access**
- **Admin:** All 5 data dashboards + 3 utility pages (Sales, Dealer Health, Product Performance, Field Operations, Profitability, Upload, Lost Sales, Admin)
- **Manager:** All 5 data dashboards + 2 utility pages (Sales, Dealer Health, Product Performance, Field Operations, Profitability, Upload, Lost Sales) - NO Admin page
- **Sales Staff:** 4 data dashboards + 2 utility pages (Sales, Dealer Health, Product Performance, Field Operations, Lost Sales) - NO Profitability, NO Upload, NO Admin
- **Access Control Implementation:** Page-level role checking before rendering. Unauthorized users redirected with Vietnamese error message.

### **Feature Permissions**
| Feature | Admin | Manager | Sales Staff |
|---------|--------|---------|-------------|
| Upload Data | ✅ | ✅ | ❌ |
| Export PDF/PPT | ✅ | ✅ | ❌ |
| Manage Users | ✅ | ✅ | ❌ |
| Edit Existing Data | ✅ | ✅ | ❌ |
| Full System Settings | ✅ | ❌ | ❌ |

### **Audit Trail**
- **Retention:** 90 days
- **Access:** Admin only
- **Tracking Scope:**
  - Modifications: Create, modify, delete records (user + date/time)
  - Viewing: Sensitive data, exports, downloads (user + details)
- **Log Fields:** Timestamp, Username, Action Type, Record ID/Table, Details

---

## Dashboard Design

### **Application Architecture: 5 Data Dashboards + 3 Utility Pages**

**Data Dashboards (5):**
1. Sales & Revenue Dashboard (Doanh số & Doanh thu)
2. Dealer Health Dashboard (Sức khỏe Đối tác)
3. Product Performance Dashboard (Hiệu suất Sản phẩm)
4. Field Operations Dashboard (Vận động trường)
5. Profitability Dashboard (Hiệu quả Kinh doanh)

**Utility Pages (3):**
- Upload Page (pages/1_Upload.py) - Data upload interface (Admin/Manager only)
- Lost Sales Page (pages/7_Lost_Sales.py) - Lost sales entry form (All roles)
- Admin Page (pages/8_Admin.py) - User management and settings (Admin only)

**Page Numbering:** 1_Upload.py, 2_Sales_Dashboard.py, 3_Dealer_Health.py, 4_Product_Performance.py, 5_Profitability_Dashboard.py, 6_Field_Operations.py, 7_Lost_Sales.py, 8_Admin.py

**Note:** Inventory status and stock tracking are integrated into the Product Performance Dashboard (pages/4_Product_Performance.py). There is no separate Inventory dashboard page.

---

### **5 Complete Data Dashboards**
1. **Sales & Revenue Dashboard (Doanh số & Doanh thu)**
   - Overview: Revenue, Volume, Growth, AR Ratio, Average Order Value
   - Charts: Revenue trend, Regional breakdown, Brand performance, Top 10 dealers
   - Tables: Regional performance, Dealer ranking, Salesperson performance

2. **Dealer Health Dashboard (Sức khỏe Đối tác)**
   - Overview: Total, Healthy, At-Risk, New, Inactive dealers
   - Charts: Health distribution, AR aging, Sales frequency, Payment performance
   - Tables: Health summary, At-risk alerts, New dealers
   - Health Criteria: Good (AR<30, payment>90%), Warning (AR30-60, payment70-90%), Critical (AR>60, payment<70%)

3. **Product Performance Dashboard (Hiệu suất Sản phẩm)**
   - Overview: Total products, In stock, Low stock (<50 units), Out of stock, Best seller
   - Charts: Inventory by brand, Top 20 products, Lost sales analysis, Product matrix
   - Tables: Product performance, Inventory status, Lost sales leaders

4. **Field Operations Dashboard (Vận động trường)**
   - Overview: Visits completed, Adherence rate, Days on road, Provinces visited, Top salesperson
   - Charts: Visit completion, Regional distribution, Visit frequency, Visit results
   - Tables: Visit plans, Visit logs, Staff performance
   - Visit Results: Thành công, Cần theo dõi, Vấn đề tồn kho, Thanh toán, Khác

5. **Profitability Dashboard (Hiệu quả Kinh doanh)**
   - ⚠️ Admin & Manager Only - Not visible to Sales Staff
   - Overview: Gross margin, Net profit, Profit growth, Average margin, Cost efficiency
   - Charts: Profit trend, Margin by product, Profit by dealer, Cost structure
   - Tables: Profitability summary, Dealer profitability, Regional profitability

### **Dashboard Features**
- **Language:** All Vietnamese UI (buttons, labels, charts, messages, tooltips)
- **Interactive:** Click to drill down, hover tooltips, sortable tables, export individual charts
- **Filters:** Time period, region, brand, category, health status, etc.
- **Export:** Excel/CSV download, PDF print, PPT export
- **Real-time:** Auto-refresh every 5 minutes (configurable), manual refresh button

---

## Export System

### **PPT Export Format**
- **Structure:** Matches Vietnamese business report template exactly
- **Sections:**
  - A. Doanh số (Sales) - Regional/brand breakdown, top dealers
  - B. Doanh thu (Revenue) - Regional revenue with AR ratios
  - II. Hàng hóa & Lost Sales - Inventory by brand, monthly tracking
  - III. Kế hoạch & Kết quả Đi thị trường - Visit plans and results
  - IV. Đối thủ cạnh tranh - Competitor analysis (manual business insight section)
  - V. KẾT LUẬN - Conclusions with 5 key points addressed, 5 points to resolve
  - Gửi RAW DATA - Export instructions
- **Format:** Tabular Excel-style layout (columns A-W), green highlighting for key columns, numbered subsections
- **Language:** All labels in Vietnamese
- **Competitor Analysis Scope:** Manual business insight section in PPT exports, not automated dashboard feature. No competitor tracking data fields required in schema.

### **PDF Export Format**
- **Structure:** Same as PPT export format
- **Content:** KPIs and charts/tables as displayed in PPT
- **Generated:** WeasyPrint-based PDF generation

---

## Language Policy

### **App UI**
- **Required:** All app UI must be in Vietnamese (buttons, labels, charts, messages, tooltips)
- **Examples:** "Đăng nhập", "Tải lên", "Xuất báo cáo", "Bộ lọc"

### **Development Language**
- **Code:** English language for variable names, function names, comments
- **Documentation:** English language for technical documentation
- **Database Values:** Region names use Vietnamese: Miền Bắc, Miền Trung, Miền Nam

---

## Technical Implementation Rules

### **Must Follow Strictly**
1. **All UI in Vietnamese** - No English text visible to end users
2. **TDD Approach** - Write failing tests first, then implement
3. **Pure Function Services** - All business logic in pure functions, no Streamlit dependencies
4. **Role-Based Access** - All features must respect user role permissions
5. **Audit Trail** - All critical actions must be logged (Admin only access)
6. **Validation First** - No data enters system without passing validation rules
7. **Error Messages** - All error messages in Vietnamese
8. **Configuration** - Use .env file for sensitive data, never hardcode credentials

### **Technology Stack**
- **Frontend:** Streamlit
- **Database:** SQLite with SQLAlchemy ORM
- **Data Processing:** Pandas
- **Charts:** Plotly
- **Exports:** python-pptx (PPT), WeasyPrint (PDF)
- **Testing:** pytest (unit tests), Playwright (E2E tests)
- **Security:** bcrypt (password hashing), python-dotenv (configuration)
- **Chart Types Supported:** Plotly supports all chart types specified in DASHBOARDS.md (bar, horizontal bar, pie, line, donut, stacked bar, scatter, histogram, bubble, treemap, area, heatmap)

### **Database Configuration**
- **Environment:** Single database for LAN deployment (~10 staff)
- **Configuration:** DATABASE_URL=sqlite:///./dealer_report.db in .env file
- **Multi-Environment:** Not required for current LAN deployment. Single database approach correct.
- **Future Enhancement:** Could add environment support (development.db, staging.db, production.db) if needed

---

## Integration Strategy

### **Phase 1 (Current): Manual Upload**
- **Data Source:** CSV/Excel files uploaded by Admin/Manager
- **Validation:** All uploaded data must pass validation rules
- **Import:** Successful data imported into SQLite database

### **Phase 2 (Future): Odoo API Integration**
- **Data Source:** Direct API calls to Odoo ERP system
- **Sync:** Real-time or periodic data synchronization
- **Conflict Handling:** Manual upload takes precedence over ERP data (business rule)

---

## Sample Data Strategy

### **Current Status**
- **Action Required:** User will provide sample CSV/Excel files when ready
- **Focus:** Real Odoo/ERP export data for accurate testing
- **Validation:** Sample data used to test all validation rules and business logic

### **Data Requirements**
- **Required Tables:** All 13 tables need sample data for comprehensive testing
  - **Business Tables (11):** sale_records, accounts_receivable_ledger, product_master, dealer_master, sales_targets, inventory_status, incoming_shipments, open_orders, lost_sales_entry, field_visit_plans, visit_logs
  - **System Tables (2):** users (seed script creates default users), audit_logs (auto-generated during testing)
- **Specific Needs:** Real column names from user's Odoo exports
- **Testing Purpose:** Validate data import, validation, and dashboard generation

---

## Clarifications & Resolutions

### **Dashboard Architecture Clarification**
- **5 Data Dashboards:** Sales & Revenue, Dealer Health, Product Performance, Field Operations, Profitability
- **3 Utility Pages:** Upload (Admin/Manager), Lost Sales (All roles), Admin (Admin only)
- **Page Access Control:** Page-level role checking. Sales Staff blocked from Profitability Dashboard entirely.
- **Implementation:** Check user role before rendering page, redirect with Vietnamese error message if unauthorized.

### **Competitor Analysis Scope**
- **PPT Export:** Section IV "Đối thủ cạnh tranh" is for manual business insights, not automated features
- **Dashboard Features:** No competitor tracking or analysis features required in dashboards
- **Data Schema:** No competitor-related data fields needed in any table
- **Business Use Case:** Managers manually add competitor insights during report generation

### **Order ID Validation Clarification**
- **Different States Allowed:** No cross-validation needed between tables
- **sale_records.order_id:** Multiple items per order allowed (order_id + item_id = unique)
- **accounts_receivable_ledger.order_id:** Multiple payment records per order allowed
- **open_orders.order_id:** Must be unique (only pending orders)
- **Business Logic:** Each table serves different purpose/state, no conflicts

### **Region Value Standardization**
- **Standard Values:** All region fields use exact Vietnamese values: Miền Bắc, Miền Trung, Miền Nam
- **Auto-Assignment:** dealer_master.region auto-assigned from sub_region codes (MN→Miền Nam, MB→Miền Bắc, MT→Miền Trung)
- **Validation:** inventory_status.location_region must be one of: Miền Bắc, Miền Trung, Miền Nam
- **Consistency:** Both tables use same Vietnamese region values

### **Lost Sales Timing Trigger**
- **Definition:** "Warehouse import" = importing data into `inventory_status` table
- **Trigger:** Lost sales calculation starts after `inventory_status` table has data for the specific item
- **Business Logic:** Items with no inventory status cannot have lost sales logged
- **Implementation:** Check `inventory_status` table for item existence before allowing lost sales entry

### **Dashboard Access Control Implementation**
- **Page-Level Restriction:** Check user role before rendering dashboard page
- **Profitability Dashboard:** Admin and Manager only - Sales Staff completely blocked
- **Upload Page:** Admin and Manager only - Sales Staff completely blocked
- **Admin Page:** Admin only - Manager and Sales Staff completely blocked
- **Implementation:** Role check in each page file, redirect with Vietnamese error message if unauthorized

### **AR Aging Configuration Storage**
- **Current Approach:** Store in `config.py` as constants (AR_BUCKET_SIZE=30, AR_MAX_DAYS=180)
- **No Database Table:** No system_settings table needed for current implementation
- **Future Enhancement:** Could add database configuration for runtime changes if needed
- **Implementation:** Hardcoded in config.py, accessible to analytics service

### **Audit Trail Table Specification**
- **Table Name:** `audit_logs` (13th table in schema)
- **Purpose:** Track all critical actions for security and compliance
- **Access:** Admin only (90-day retention, auto-delete older records)
- **Implementation:** Auto-logging in services for CRUD operations, exports, sensitive data viewing

### **Revenue Calculation Date Field**
- **Rule:** Always use `date_transfer` for revenue and all KPI calculations
- **Order Date:** `order_date` used for planning/scheduling purposes only
- **Dashboard KPIs:** All time-based revenue metrics use `date_transfer`
- **Business Logic:** Revenue recognized when goods are shipped (date_transfer set)

### **Chart Library Verification**
- **Library:** Plotly (confirmed support for all specified chart types)
- **Supported Types:** Bar, pie, line, donut, stacked bar, scatter, histogram, bubble, treemap, area, heatmap
- **No Substitutions Needed:** All chart types in DASHBOARDS.md are supported by Plotly
- **Implementation:** Use Plotly Express and Graph Objects for chart generation

### **Database Environment Approach**
- **Current Deployment:** Single database for LAN deployment (~10 staff)
- **Configuration:** DATABASE_URL=sqlite:///./dealer_report.db in .env file
- **Multi-Environment:** Not required for current LAN deployment
- **Future Enhancement:** Could add environment support (development.db, staging.db, production.db) if scaling needs change

---

## Critical Documentation Resolutions (2026-05-11)

This section documents the resolution of critical inconsistencies identified during workspace audit. All decisions below are authoritative and must be followed during implementation.

### **1. Table Count - Authoritative Decision**
- **Total Tables:** 13 tables (11 business tables + 2 system tables)
- **System Tables:** users (authentication), audit_logs (security audit trail)
- **Business Tables:** sale_records, accounts_receivable_ledger, product_master, dealer_master, sales_targets, inventory_status, incoming_shipments, open_orders, lost_sales_entry, field_visit_plans, visit_logs
- **Resolution:** All documentation updated to consistently reference 13 tables. Implementation plan test updated to include audit_logs.

### **2. Dashboard Structure - Authoritative Decision**
- **5 Data Dashboards:**
  1. Sales & Revenue Dashboard (pages/2_Sales_Dashboard.py)
  2. Dealer Health Dashboard (pages/3_Dealer_Health.py)
  3. Product Performance Dashboard (pages/4_Product_Performance.py) - includes inventory status tracking
  4. Field Operations Dashboard (pages/6_Field_Operations.py)
  5. Profitability Dashboard (pages/5_Profitability_Dashboard.py) - Admin/Manager only
- **3 Utility Pages:**
  - Upload Page (pages/1_Upload.py) - Admin/Manager only
  - Lost Sales Page (pages/7_Lost_Sales.py) - All roles
  - Admin Page (pages/8_Admin.py) - Admin only
- **Resolution:** Renamed pages/5_Inventory.py to pages/5_Profitability_Dashboard.py. Inventory functionality integrated into Product Performance Dashboard.

### **3. Role Naming - Authoritative Decision**
- **Standard Role Names:** Admin, Manager, Sales Staff
- **Role Display Names:** Administrator, Sales Manager, Sales Staff
- **Resolution:** All documentation updated to use "Sales Staff" instead of "Employee". Implementation plan updated with corrected role names.

### **4. Location Region Requirement - Authoritative Decision**
- **Field:** inventory_status.location_region
- **Requirement:** Required field
- **Valid Values:** Miền Bắc, Miền Trung, Miền Nam
- **Business Justification:** Required for consistency with dealer_master.region (which is auto-assigned) and for proper region-based inventory filtering
- **Resolution:** DATA_VALIDATION.md updated to mark location_region as required (✅ Yes) instead of optional (❌ Optional).

### **5. Page Numbering - Authoritative Decision**
- **Complete Page Structure:**
  - pages/1_Upload.py (Admin/Manager)
  - pages/2_Sales_Dashboard.py (All roles)
  - pages/3_Dealer_Health.py (All roles)
  - pages/4_Product_Performance.py (All roles)
  - pages/5_Profitability_Dashboard.py (Admin/Manager)
  - pages/6_Field_Operations.py (All roles)
  - pages/7_Lost_Sales.py (All roles)
  - pages/8_Admin.py (Admin only)
- **Resolution:** Profitability Dashboard now has proper page number (5) and all documentation reflects this structure.

### **6. Ambiguity Resolutions (Implementation Decisions)**

This section documents explicit decisions for previously ambiguous implementation details.

#### **plan_id Foreign Key Constraint**
- **Decision:** Application-level only, NO database-level foreign key constraint
- **Business Justification:** Plans may be deleted but visit logs must be retained for historical purposes
- **Implementation:** Use soft validation (check existence on read, optional constraint on write)
- **Files Affected:** database/models.py (visit_logs table)

#### **Session Storage Mechanism**
- **Decision:** Streamlit built-in session state (st.session_state) for LAN deployment
- **Business Justification:** Simple deployment, no external session store required for ~10 users
- **Remember Me Feature:** Use Streamlit session with 30-day expiration (if available) or browser cookies
- **Implementation:** Store user object in st.session_state["user"], check on page load
- **Files Affected:** auth/service.py, app.py

#### **Lost Sales Revenue Calculation Timing**
- **Decision:** Calculate at time of lost sales entry (real-time)
- **Business Justification:** Most accurate revenue representation at time of missed opportunity
- **Formula:** `lost_revenue = lost_volume × avg_revenue_per_unit` (3-month dealer/item average)
- **Fallback:** If no dealer history, use all-dealer average for that item
- **Implementation:** Calculate in analytics.py, store in database
- **Files Affected:** services/analytics.py, database/models.py (lost_sales_entry table)

#### **Chart Export Format for PDF**
- **Decision:** Convert Plotly charts to static images (PNG) before PDF generation
- **Business Justification:** WeasyPrint doesn't support interactive charts; images are printable
- **Implementation:** Use Plotly's `to_image()` method to convert charts to base64 PNG
- **Resolution:** 1920x1080 pixels for high-quality print
- **Files Affected:** services/export_pdf.py

#### **Audit Log Retention Mechanism**
- **Decision:** Automated cleanup on application startup (not cron job)
- **Business Justification:** Simpler deployment for LAN environment, no external scheduler needed
- **Implementation:** Add cleanup function to database/seed.py, call on app startup
- **Retention:** Delete records older than 90 days from audit_logs table
- **Files Affected:** database/seed.py, app.py

#### **Concurrent User Access for SQLite**
- **Decision:** No special handling required for ~10 staff LAN deployment
- **Business Justification:** SQLite handles read concurrency well; write conflicts rare for this use case
- **Implementation:** Use SQLAlchemy session management with automatic retry on write conflicts
- **Performance:** Connection pooling with timeout of 30 seconds
- **Files Affected:** database/session.py

#### **TDD Scope for UI Components**
- **Decision:** TDD applies to business logic services, NOT to Streamlit page UI
- **Business Justification:** UI changes frequently; testing business logic provides more value
- **Implementation:** Write tests for services/ (analytics, upload_service, export), manual testing for pages/
- **E2E Testing:** Use Playwright for end-to-end UI testing
- **Files Affected:** tests/ directory structure

#### **Vietnamese Character Encoding**
- **Decision:** UTF-8 encoding for all database storage and file operations
- **Business Justification:** Industry standard, supports all Vietnamese characters
- **Implementation:** SQLAlchemy uses UTF-8 by default, no explicit configuration needed
- **Files Affected:** database/models.py, database/session.py

#### **Error Handling Approach**
- **Decision:** Follow Karpathy Guidelines - minimal error handling for impossible scenarios
- **Business Justification:** Avoids code bloat; focuses on actual failure cases
- **Implementation:** Validate at system boundaries (user input, database, external APIs)
- **Files Affected:** All service modules

---

## Next Steps

### **Before Coding Begins**
✅ All requirements documented
✅ All business logic defined
✅ All validation rules specified
✅ All security requirements detailed
✅ All dashboard designs completed
✅ All export formats specified
✅ All language policies established
✅ **Documentation audit complete:** All inconsistencies, redundancies, and ambiguities resolved (Version 3.2)
✅ **Single source of truth established:** All rules documented in MASTER_DECISIONS.md
✅ **Implementation decisions documented:** 9 ambiguity resolutions for development guidance

### **Coding Phase**
⏳ Implement authentication system
⏳ Implement data upload service with validation
⏳ Implement all 5 dashboards
⏳ Implement export services (PPT/PDF)
⏳ Implement audit trail system
⏳ Comprehensive testing (unit tests + E2E tests)

---

**CRITICAL:** This document serves as the single source of truth for all implementation decisions. Any changes to requirements must be documented here before implementation.