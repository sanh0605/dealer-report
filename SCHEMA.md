# SCHEMA.md - Database Schema & Structure

**Last Updated:** 2026-05-08  
**Purpose:** Database tables, fields, relationships, and auto-assignment logic  
**Total Tables:** 13 tables (11 business tables + 2 system tables)  
**Note:** For business logic, language policy, and export formats, see [MASTER_DECISIONS.md](MASTER_DECISIONS.md)

---

## Database Tables

### 1. Sales Transaction Table (`sale_records`)
*Primary fact table for sales performance and staff identity.*

| Column | Type | Description |
| :--- | :--- | :--- |
| `order_id` | Text | Unique identifier for the transaction. **Duplicates allowed** (multiple items per order). |
| `order_date` | Date | The date the dealer placed the order (for planning/scheduling). |
| `date_transfer` | Date | The date the goods were shipped. **Used for revenue calculations** - not order_date. |
| `dealer_id` | Text | Unique ID of the branch/shop. Links to dealer_master. |
| `item_id` | Text | The specific SKU ID. Links to product_master. |
| `salesperson` | Text | Person responsible for both sale and debt collection. |
| `sale_admin` | Text | Office staff for internal reference only. |
| `channel_name` | Text | Raw channel name from the source data. |
| `sales_volume` | Integer | Quantity of items sold. **Can be negative for returns** - subtracted from totals in KPIs. |
| `unit_price_standard`| Float | Standard unit price per item. **Can be negative for returns**. |
| `total_price_standard`| Float | Total value before discounts are applied. **Can be negative for returns**. |
| `sales_revenue` | Float | Net revenue after discounts. **Can be negative for returns** - reflected in all revenue KPIs. |
| `cost_of_goods` | Float | Total cost for this line item provided in source. **Can be negative for returns**. |

> **Note:** Unique identifier = `order_id + item_id` combination. Revenue and all KPIs use `date_transfer`, not `order_date`.

### 2. Accounts Receivable Ledger (`accounts_receivable_ledger`)
*Detailed transactional tracking of money, refunds, and adjustments.*

| Column | Type | Description |
| :--- | :--- | :--- |
| `order_id` | Text | Links to sale_records for identity and shipping date. **Duplicates allowed** (multiple payment records per order). |
| `order_date` | Date | The date the dealer placed the order. |
| `date_posted` | Date | The date the payment/refund action was recorded. |
| `due_date` | Date | The date payment is expected for this specific order. |
| `total_order_value` | Float | Base value (System uses MAX per order_id to avoid duplication). |
| `refund_amount` | Float | Amount reduced by returning goods. **Can be positive/negative**. |
| `deduction_amount` | Float | Amount reduced by credits or other adjustments. **Can be positive/negative**. |
| `paid_amount` | Float | Amount actually paid by the dealer. **Can be positive/negative**. |

> **Note:** No cross-validation with other order_id tables needed. Each table serves different business purpose (completed orders vs. payments vs. pending orders).

### 3. Product Master Table (`product_master`)
*Granular SKU details and hierarchical grouping.*

| Column | Type | Source / Logic |
| :--- | :--- | :--- |
| `item_id` | Text | **Uploaded:** Unique identifier (SKU). |
| `item_name` | Text | **Uploaded:** Full display name of the SKU. |
| `product_id` | Text | **Uploaded:** Parent product line identifier. |
| `product` | Text | **Uploaded:** Name of the parent product line. |
| `brand_group` | Text | **Auto-assigned:** Based on category + brand via rules (see logic below). |
| `brand` | Text | **Uploaded:** Raw brand name. |
| `category` | Text | **Uploaded:** Bikes, Gears, CCDC, Services, or Others. |
| `subcategory` | Text | **Uploaded:** Specific classification. |
| `model` | Text | **Uploaded:** NULL if category is not 'Bikes'. |
| `color` | Text | **Uploaded:** Specific color. |
| `size` | Text | **Uploaded:** Specific size. |

**Brand Group Auto-Assignment Logic:**
- If `category` = "Bikes" AND `brand` in (Giant, Liv, Momentum) → "Giant Group"
- If `category` = "Bikes" AND `brand` = "Java" → "Java"
- If `category` = "Bikes" AND `brand` is anything else → "OEM Group"
- If `category` = "Gears" → "Gears Group" (regardless of brand)
- All other categories (CCDC, Services, Others) → "Others"

### 4. Dealer Master Table (`dealer_master`)
*Client identity and geographic mapping.*

| Column | Type | Source / Logic |
| :--- | :--- | :--- |
| `dealer_id` | Text | **Uploaded:** Unique ID for the shop. |
| `dealer_name` | Text | **Uploaded:** Name of the shop. |
| `business_name` | Text | **Uploaded:** Main company name (for grouping rankings). |
| `province` | Text | **Uploaded:** Specific province where the dealer is located. |
| `sub_region` | Text | **Uploaded:** City or specific group of provinces (Parent of province). |
| `region` | Text | **Auto-assigned:** Mapped from sub_region code prefix (see logic below). **Values: Miền Bắc, Miền Trung, Miền Nam**. |
| `address` | Text | **Uploaded:** Full physical address for mapping. |
| `dealer_VX_id` | Text | **Uploaded:** Optional text field. |

**Region Auto-Assignment Logic (based on sub_region code prefix):**
- sub_region contains "MN" → "Miền Nam"
- sub_region contains "MB" → "Miền Bắc"
- sub_region contains "MT" → "Miền Trung"

### 5. Sales Targets Table (`sales_targets`)
*Revenue goals mapped to sub-regions.*

| Column | Type | Description |
| :--- | :--- | :--- |
| `target_id` | Text | Auto-generated unique ID. |
| `month_year` | Text | Reporting month (e.g. "05/2026"). |
| `sub_region` | Text | Sales territory code (e.g. "MN1", "MN2"). |
| `target_revenue` | Float | Revenue goal in VND for this sub-region/month. |

> **Note:** For sub_region validation workflow when value doesn't exist in dealer_master, see [MASTER_DECISIONS.md](MASTER_DECISIONS.md) (Data Validation Rules section).

### 6. Inventory Status Table (`inventory_status`)
| Column | Type | Source / Logic |
| :--- | :--- | :--- |
| `item_id` | Text | **Uploaded:** Unique SKU identifier. |
| `stock_on_hand` | Integer | **Uploaded:** Physical units currently in warehouse. |
| `location` | Text | **Uploaded:** Warehouse name. |
| `location_region`| Text | **Uploaded (Required):** North, Central, or South. **Must be: Miền Bắc, Miền Trung, Miền Nam** (same as dealer_master.region). |

> **Note:** location_region should use same Vietnamese values as dealer_master.region: Miền Bắc, Miền Trung, Miền Nam.

### 7. Incoming Shipments Table (`incoming_shipments`)
| Column | Type | Source / Logic |
| :--- | :--- | :--- |
| `item_id` | Text | **Uploaded:** Unique SKU identifier. |
| `incoming_qty` | Integer | **Uploaded:** Quantity in transit/scheduled. |
| `expected_arrival_date`| Date | **Uploaded:** Scheduled delivery date. |

### 8. Open Orders Table (`open_orders`)
*Pending commitments not yet fulfilled.*

| Column | Type | Source / Logic |
| :--- | :--- | :--- |
| `order_id` | Text | **Uploaded:** ID of uncompleted order. **Must be unique** (only pending orders). |
| `dealer_id` | Text | **Uploaded:** ID of dealer waiting for stock. |
| `item_id` | Text | **Uploaded:** SKU being requested. |
| `open_qty` | Integer | **Uploaded:** Quantity pending fulfillment. |

> **Note:** order_id unique constraint applies only to open_orders. No cross-validation with sale_records or accounts_receivable_ledger needed.

### 9. Lost Sales Entry Table (`lost_sales_entry`)
*Real-time missed opportunity tracking via app form.*

| Column | Type | Source / Logic |
| :--- | :--- | :--- |
| `entry_id` | Text | Auto-generated ID. |
| `date` | Date | Auto-captured at entry. |
| `staff_name` | Text | Auto-captured from logged-in user. |
| `dealer_id` | Text | **Selected:** Links to dealer_master. |
| `item_id` | Text | **Selected:** Links to product_master. |
| `lost_volume` | Integer | **Entered:** Quantity unavailable. |
| `lost_revenue` | Float | **Auto-calculated:** lost_volume × avg_revenue_per_unit. |

> **Note:** Lost sales calculation starts after first successful import to inventory_status table for the item. For lost revenue calculation formula and business rules, see [MASTER_DECISIONS.md](MASTER_DECISIONS.md) (Business Logic Decisions section).

### 10. Field Visit Plans Table (`field_visit_plans`)
*Target list of dealers to be visited each month.*

| Column | Type | Source / Logic |
| :--- | :--- | :--- |
| `plan_id` | Text | Auto-generated ID. |
| `staff_name` | Text | Person assigned to the visit. |
| `month_year` | Text | Reporting month (e.g., "05/2026"). |
| `dealer_id` | Text | **Target:** The specific shop intended for visit. |

### 11. Visit Logs Table (`visit_logs`)
*Actual activity recorded by staff.*

| Column | Type | Source / Logic |
| :--- | :--- | :--- |
| `log_id` | Text | Auto-generated ID. |
| `date` | Date | Actual date of the visit. |
| `staff_name` | Text | Who performed the visit. |
| `dealer_id` | Text | **Actual:** Selected via enhanced search (ID + Name + Address). |
| `plan_id` | Text | **Optional:** References field_visit_plans.plan_id. NULL = ad-hoc/impromptu visit. |
| `visit_result` | Text | Detailed outcome of the visit. |

> **Note:** plan_id is optional (NULL for ad-hoc visits). Visit adherence calculation only counts visits with matching plan_id as completed planned visits. Ad-hoc visits tracked separately but not counted in adherence metrics. For visit adherence definition, metrics, and business rules, see [MASTER_DECISIONS.md](MASTER_DECISIONS.md) (Business Logic Decisions section).

---

## System Tables

### 12. Users Table (`users`)
*User authentication and authorization.*

| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | Text | Auto-generated unique ID. |
| `username` | Text | Unique username for login. |
| `password_hash` | Text | Bcrypt hashed password (never store plaintext). |
| `role` | Text | User role: "Admin", "Manager", or "Sales Staff". |
| `display_name` | Text | Human-readable name for display in UI. |
| `created_at` | DateTime | Account creation timestamp. |
| `last_login` | DateTime | Last successful login timestamp (for display). |

> **Default Users (created by seed.py):**
> - Admin: username="sanh0605", password="sanh0605", role="Admin"
> - Manager: username="manager", password="manager123", role="Manager"  
> - Sales Staff: username="employee", password="employee123", role="Sales Staff"

### 13. Audit Logs Table (`audit_logs`)
*System audit trail for security and compliance.*

| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | Text | Auto-generated unique ID. |
| `timestamp` | DateTime | When the action occurred. |
| `username` | Text | Who performed the action. |
| `action_type` | Text | Type of action: "Create", "Modify", "Delete", "View", "Export", "Download". |
| `record_id` | Text | ID of affected record (if applicable). |
| `table_name` | Text | Name of affected table (if applicable). |
| `details` | Text | Additional details about the action. |

> **Audit Trail Configuration:**
> - **Retention:** 90 days (auto-delete records older than 90 days)
> - **Access:** Admin only
> - **Tracking Scope:** All modifications, viewing of sensitive data, exports, downloads
> - For complete audit trail requirements, see [SECURITY.md](SECURITY.md)

---

## Auto-Assignment Logic

### **Brand Group Assignment** (product_master table)
See Product Master Table above for complete logic.

### **Region Assignment** (dealer_master table)
See Dealer Master Table above for complete logic.

### **Region Values Standardization**
> For complete region value standardization and auto-assignment business logic, see [MASTER_DECISIONS.md](MASTER_DECISIONS.md) (Business Logic Decisions section).
- **Applies to:** `dealer_master.region` (auto-assigned), `inventory_status.location_region` (validated)

---

## Table Relationships & Validation Rules

### **Order ID Handling**
> For complete order ID duplication rules and business logic, see [MASTER_DECISIONS.md](MASTER_DECISIONS.md) (Business Logic Decisions section).

### **Negative Value Handling**
> For complete negative values policy and business rules, see [MASTER_DECISIONS.md](MASTER_DECISIONS.md) (Data Validation Rules section).
- **Revenue Calculation:** Always use `date_transfer`, not `order_date`

### **Visit Log Relationships**
> For plan_id foreign key constraint decision, see [MASTER_DECISIONS.md](MASTER_DECISIONS.md) (Ambiguity Resolutions section).
- `visit_logs.plan_id`: Optional reference to `field_visit_plans.plan_id`
- **Planned visits:** Have matching plan_id (counted in adherence)
- **Ad-hoc visits:** plan_id is NULL (not counted in adherence, tracked separately)

---

## Business Rules & System Configuration

> **🔗 All business rules, language policies, date formats, and export specifications are documented in [MASTER_DECISIONS.md](MASTER_DECISIONS.md).**
>
> This document (SCHEMA.md) focuses exclusively on:
> - Database table structures (13 tables total)
> - Field descriptions and relationships
> - Auto-assignment logic for `brand_group` and `region`
> - Table relationships and validation rules
>
> **For the following information, refer to MASTER_DECISIONS.md:**
> - Lost sales calculation (cascading formula, timing triggers)
> - Visit adherence definition and metrics (planned vs ad-hoc visits)
> - AR aging configuration (bucket_size=30, max_days=180 in config.py)
> - Sales records business rules (negative values, revenue calculation timing)
> - Language policy (Vietnamese UI, English development)
> - Date format recognition rules
> - PPT/PDF export formats and structure (competitor analysis is manual)
> - Data validation workflow and error messages
> - Security and access control requirements
> - User roles and dashboard access permissions
> - Dashboard architecture (5 data dashboards + 3 utility pages)

---

## Summary

**Total Tables:** 13 tables (11 business tables + 2 system tables)
- **Business Tables (11):** sale_records, accounts_receivable_ledger, product_master, dealer_master, sales_targets, inventory_status, incoming_shipments, open_orders, lost_sales_entry, field_visit_plans, visit_logs
- **System Tables (2):** users, audit_logs

**Auto-Calculated Fields:** `brand_group` (product_master), `region` (dealer_master), `lost_revenue` (lost_sales_entry)
**Auto-Generated IDs:** All id fields across 13 tables
**Foreign Key Relationships:** visit_logs.plan_id → field_visit_plans.plan_id (optional)
**Region Standardization:** All region fields use exact values: Miền Bắc, Miền Trung, Miền Nam
**Revenue Calculation:** Always uses `date_transfer`, never `order_date`

**Dashboard Architecture:**
- **5 Data Dashboards:** Sales & Revenue, Dealer Health, Product Performance, Field Operations, Profitability
- **3 Utility Pages:** Upload (1_), Lost Sales (7_), Admin (8_)

For complete implementation guidance, see [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md).
