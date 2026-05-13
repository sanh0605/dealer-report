# DATA_VALIDATION.md - Data Validation Rules

**Last Updated:** 2026-05-08  
**Purpose:** Table-specific validation rules for all 11 database tables  
**Note:** For date format recognition and general validation principles, see [MASTER_DECISIONS.md](MASTER_DECISIONS.md)

---

## General Validation Principles

> **🔗 For date format recognition, auto-detection rules, and upload error handling policies, see [MASTER_DECISIONS.md](MASTER_DECISIONS.md) (Data Validation Rules section).**
>
> This document focuses exclusively on table-specific field validation rules.

### **Data Types:**
- **Integer**: Whole numbers only (e.g., 100, 99, 1) - used for quantities
- **Decimal/Float**: Numbers with decimals (e.g., 100.5, 99.99, 0.01) - used for money amounts

---

## Table-Specific Validation Rules

### 1. sale_records Table

| Field | Validation Rules | Required? |
|-------|-----------------|-----------|
| `order_id` | Text, not empty, duplicates allowed (multiple items per order) | ✅ Yes |
| `order_date` | Valid date format (auto-recognize), not future date | ✅ Yes |
| `date_transfer` | Valid date (auto-recognize), >= order_date | ✅ Yes |
| `dealer_id` | Text, not empty, must exist in dealer_master table | ✅ Yes |
| `item_id` | Text, not empty, must exist in product_master table | ✅ Yes |
| `salesperson` | Text, not empty | ✅ Yes |
| `sale_admin` | Text, not empty | ✅ Yes |
| `channel_name` | Text, not empty | ✅ Yes |
| `sales_volume` | Integer (can be negative for returns) | ✅ Yes |
| `unit_price_standard` | Decimal number (can be negative for returns) | ✅ Yes |
| `total_price_standard` | Decimal number (can be negative for returns) | ✅ Yes |
| `sales_revenue` | Decimal number (can be negative for returns) | ✅ Yes |
| `cost_of_goods` | Decimal number (can be negative for returns) | ✅ Yes |

> **Note:** Revenue calculated only when date_transfer is set. For business rules on negative values, see [MASTER_DECISIONS.md](MASTER_DECISIONS.md).

---

### 2. accounts_receivable_ledger Table

| Field | Validation Rules | Required? |
|-------|-----------------|-----------|
| `order_id` | Text, not empty, duplicates allowed | ✅ Yes |
| `date_posted` | Valid date format (auto-recognize), required | ✅ Yes |
| `due_date` | Valid date format (auto-recognize), required | ✅ Yes |
| `total_order_value` | Decimal number (can be positive/negative) | ✅ Yes |
| `refund_amount` | Decimal number (can be positive/negative) | ✅ Yes |
| `deduction_amount` | Decimal number (can be positive/negative) | ✅ Yes |
| `paid_amount` | Decimal number (can be positive/negative) | ✅ Yes |

**Note:** order_id is independent - used for lookup between tables, no validation against sale_records required.

---

### 3. product_master Table

| Field | Validation Rules | Required? |
|-------|-----------------|-----------|
| `item_id` | Text, not empty, must be unique | ✅ Yes |
| `item_name` | Text, not empty | ✅ Yes |
| `product_id` | Text, not empty | ✅ Yes |
| `product` | Text, not empty | ✅ Yes |
| `brand` | Text, not empty | ✅ Yes |
| `category` | Must be: Bikes, Gears, CCDC, Services, or Others | ✅ Yes |
| `subcategory` | Text | ❌ Optional |
| `model` | Text (NULL if category != 'Bikes') | ❌ Optional |
| `color` | Text | ❌ Optional |
| `size` | Text | ❌ Optional |

**Auto-calculated fields (no validation needed):**
- `brand_group` - automatically assigned based on category + brand rules (see [SCHEMA.md](SCHEMA.md))

---

### 4. dealer_master Table

| Field | Validation Rules | Required? |
|-------|-----------------|-----------|
| `dealer_id` | Text, not empty, must be unique | ✅ Yes |
| `dealer_name` | Text, not empty | ✅ Yes |
| `business_name` | Text, not empty | ✅ Yes |
| `province` | Text, not empty | ✅ Yes |
| `sub_region` | Text, not empty | ✅ Yes |
| `address` | Text, not empty | ✅ Yes |
| `dealer_VX_id` | Text | ❌ Optional |

**Auto-calculated fields (no validation needed):**
- `region` - automatically assigned based on sub_region code prefix (MN, MB, MT) (see [SCHEMA.md](SCHEMA.md))

---

### 5. sales_targets Table

| Field | Validation Rules | Required? |
|-------|-----------------|-----------|
| `target_id` | Text, not empty, must be unique (auto-generated) | ✅ Yes |
| `month_year` | Format: MM/YYYY (can be past, present, future) | ✅ Yes |
| `sub_region` | Text, not empty (with decision workflow if not in dealer_master) | ✅ Yes |
| `target_revenue` | Decimal number (positive or negative) | ✅ Yes |

**sub_region Validation Workflow:**
> **For complete validation workflow and user interaction details, see [MASTER_DECISIONS.md](MASTER_DECISIONS.md) (Data Validation Rules section).**

---

### 6. inventory_status Table

| Field | Validation Rules | Required? |
|-------|-----------------|-----------|
| `item_id` | Text, not empty, must exist in product_master | ✅ Yes |
| `stock_on_hand` | Integer (can be positive/negative) | ✅ Yes |
| `location` | Text, not empty | ✅ Yes |
| `location_region` | Must be: Miền Bắc, Miền Trung, Miền Nam | ✅ Yes |

---

### 7. incoming_shipments Table

| Field | Validation Rules | Required? |
|-------|-----------------|-----------|
| `item_id` | Text, not empty, must exist in product_master | ✅ Yes |
| `incoming_qty` | Integer (can be positive/negative) | ✅ Yes |
| `expected_arrival_date` | Valid date format (auto-recognize) | ✅ Yes |

---

### 8. open_orders Table

| Field | Validation Rules | Required? |
|-------|-----------------|-----------|
| `order_id` | Text, not empty, must be unique | ✅ Yes |
| `dealer_id` | Text, not empty, must exist in dealer_master | ✅ Yes |
| `item_id` | Text, not empty, must exist in product_master | ✅ Yes |
| `open_qty` | Integer (can be positive/negative) | ✅ Yes |

---

### 9. lost_sales_entry Table

| Field | Validation Rules | Required? |
|-------|-----------------|-----------|
| `entry_id` | Text, not empty, must be unique (auto-generated) | ✅ Yes |
| `date` | Valid date format (auto-recognize) | ✅ Yes |
| `staff_name` | Text, not empty | ✅ Yes |
| `dealer_id` | Text, not empty, must exist in dealer_master | ✅ Yes |
| `item_id` | Text, not empty, must exist in product_master | ✅ Yes |
| `lost_volume` | Integer (must be positive - cannot have negative lost sales) | ✅ Yes |
| `lost_revenue` | Decimal number (auto-calculated) | ✅ Auto |

> **Note:** For lost revenue calculation formula and business rules (cascading formula, new items exception), see [MASTER_DECISIONS.md](MASTER_DECISIONS.md) (Business Logic Decisions section).

---

### 10. field_visit_plans Table

| Field | Validation Rules | Required? |
|-------|-----------------|-----------|
| `plan_id` | Text, not empty, must be unique (auto-generated) | ✅ Yes |
| `staff_name` | Text, not empty | ✅ Yes |
| `month_year` | Format: MM/YYYY | ✅ Yes |
| `dealer_id` | Text, not empty, must exist in dealer_master | ✅ Yes |

---

### 11. visit_logs Table

| Field | Validation Rules | Required? |
|-------|-----------------|-----------|
| `log_id` | Text, not empty, must be unique (auto-generated) | ✅ Yes |
| `date` | Valid date format (auto-recognize) | ✅ Yes |
| `staff_name` | Text, not empty | ✅ Yes |
| `dealer_id` | Text, not empty, must exist in dealer_master | ✅ Yes |
| `visit_result` | Text, not empty | ✅ Yes |

> **Note:** For visit adherence definition, structured outcomes, and business rules, see [MASTER_DECISIONS.md](MASTER_DECISIONS.md) (Business Logic Decisions section).

---

## Validation Error Messages

All validation error messages must be displayed in Vietnamese:

### **Common Errors:**
- "Trường [field_name] không được để trống" - Field [field_name] cannot be empty
- "Giá trị [field_name] không hợp lệ" - Value [field_name] is invalid
- "Định dạng ngày không hợp lệ" - Invalid date format
- "[id] không tồn tại trong bảng [table_name]" - [id] does not exist in table [table_name]
- "[field_name] phải là số nguyên" - [field_name] must be an integer
- "[field_name] phải là số thập phân" - [field_name] must be a decimal number
- "[field_name] không được nhỏ hơn [min_value]" - [field_name] cannot be less than [min_value]
- "[field_name] không được lớn hơn [max_value]" - [field_name] cannot be greater than [max_value]

### **Specific Errors:**
- "order_id này đã tồn tại" - This order_id already exists (for unique order_id requirements)
- "item_id không tồn tại trong product_master" - item_id does not exist in product_master
- "dealer_id không tồn tại trong dealer_master" - dealer_id does not exist in dealer_master
- "category phải là: Bikes, Gears, CCDC, Services, hoặc Others" - category must be: Bikes, Gears, CCDC, Services, or Others
- "location_region phải là: Miền Bắc, Miền Trung, Miền Nam" - location_region must be: Miền Bắc, Miền Trung, Miền Nam

### **Decision Workflow Messages:**
> **For complete decision workflow messages and user interaction, see [MASTER_DECISIONS.md](MASTER_DECISIONS.md) (Data Validation Rules section).**

---

## Summary

This document provides table-specific validation rules for all 11 database tables. For:

- **Date format recognition and auto-detection** → See [MASTER_DECISIONS.md](MASTER_DECISIONS.md)
- **Upload error handling policies** → See [MASTER_DECISIONS.md](MASTER_DECISIONS.md)
- **Business logic rules** (lost sales, visit adherence, AR aging) → See [MASTER_DECISIONS.md](MASTER_DECISIONS.md)
- **Database structure and relationships** → See [SCHEMA.md](SCHEMA.md)
- **Security and access control** → See [SECURITY.md](SECURITY.md)
