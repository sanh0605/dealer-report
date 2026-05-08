# YEAR_TARGET_REPORT.md - Year Target Observation Report Specification

**Last Updated:** 2026-05-08  
**Purpose:** Specification for annual target observation and tracking report  
**Language:** Vietnamese (all UI elements, labels, charts, messages)  
**Access Level:** Admin & Manager only (Sales Staff restricted)

---

## Report Overview

### **Business Purpose:**
Provide comprehensive year-over-year performance tracking to observe annual targets across:
- Revenue targets by region and sub-region
- Sales volume goals
- Dealer performance benchmarks
- Product category targets
- Field operations metrics
- Profitability objectives

### **Report Structure:**
This is a **specialized exportable report** (not a live dashboard) that can be generated as:
1. **PowerPoint (PPT)** - For executive presentations
2. **PDF** - For archival and distribution

---

## Report Sections (Vietnamese)

### **1. Tổng quan (Executive Summary)**

#### **Key Metrics Cards:**
- **Doanh thu năm (Annual Revenue)** - Total revenue YTD vs Target
- **Tỷ lệ hoàn thành (Completion Rate)** - Target achievement percentage
- **Công nợ trung bình (Average AR)** - Accounts receivable days
- **Biên lợi nhuận (Gross Margin)** - Overall profitability
- **Số lượng bán (Sales Volume)** - Total units sold YTD
- **Tăng trưởng so với năm trước (YoY Growth)** - Growth vs previous year

#### **Visual Elements:**
- Circular progress indicators for target completion
- Color coding: Green (>100%), Yellow (80-99%), Red (<80%)
- Year-over-year comparison arrows (↑↓)

---

### **2. Hiệu suất theo Vùng (Regional Performance)**

#### **Metrics Table:**
| Vùng | Doanh thu thực tế | Mục tiêu năm | Tỷ lệ hoàn thành | Tăng trưởng | Số lượng |
|------|------------------|--------------|------------------|-------------|----------|
| Miền Bắc | [Value] VND | [Target] VND | [XX]% | [+/-XX]% | [Units] |
| Miền Trung | [Value] VND | [Target] VND | [XX]% | [+/-XX]% | [Units] |
| Miền Nam | [Value] VND | [Target] VND | [XX]% | [+/-XX]% | [Units] |
| **Tổng cộng** | **[Total]** VND | **[Target]** VND | **[XX]%** | **[+/-XX]%** | **[Units]** |

#### **Charts:**
- **Bar Chart:** Actual vs Target by Region (side-by-side bars)
- **Line Chart:** Monthly progress by region (cumulative)
- **Treemap:** Revenue distribution by sub-region

---

### **3. Phân tích theo Thương hiệu (Brand Performance)**

#### **Metrics Table:**
| Thương hiệu | Doanh thu | Tỷ trọng | Tăng trưởng YoY | Biên lợi nhuận |
|-------------|-----------|----------|-----------------|----------------|
| Giant Group | [Value] VND | [XX]% | [+/-XX]% | [XX]% |
| Java | [Value] VND | [XX]% | [+/-XX]% | [XX]% |
| OEM Group | [Value] VND | [XX]% | [+/-XX]% | [XX]% |
| Gears Group | [Value] VND | [XX]% | [+/-XX]% | [XX]% |
| Others | [Value] VND | [XX]% | [+/-XX]% | [XX]% |

#### **Charts:**
- **Pie Chart:** Revenue share by brand group
- **Stacked Bar:** Monthly revenue by brand
- **Scatter Plot:** Margin vs Volume by brand

---

### **4. Hiệu suất Đối tác (Dealer Performance)**

#### **Top 10 Dealers by Revenue:**
| Xếp hạng | Tên đối tác | Tỉnh | Doanh thu | Tăng trưởng | Đánh giá |
|----------|-------------|------|-----------|-------------|----------|
| 1 | [Dealer Name] | [Province] | [Value] VND | [+/-XX]% | ⭐⭐⭐⭐⭐ |
| 2 | [Dealer Name] | [Province] | [Value] VND | [+/-XX]% | ⭐⭐⭐⭐ |
| ... | ... | ... | ... | ... | ... |

#### **Dealer Health Distribution:**
- **Đối tác xuất sắc (Excellent):** [Count] - Top 20% by revenue
- **Đối tác tốt (Good):** [Count] - 60-80% percentile
- **Cần cải thiện (Needs Improvement):** [Count] - 40-60% percentile
- **Đối tác rủi ro (At Risk):** [Count] - Below 40% percentile

#### **Charts:**
- **Horizontal Bar:** Top 20 dealers by revenue
- **Donut Chart:** Dealer health distribution
- **Heatmap:** Dealer performance by province

---

### **5. Tồn kho & Sản phẩm (Inventory & Products)**

#### **Inventory Status:**
| Trạng thái | Số lượng sản phẩm | Tổng giá trị | Tỷ trọng |
|------------|------------------|--------------|----------|
| Hàng có sẵn (In Stock) | [Count] | [Value] VND | [XX]% |
| Sắp hết hàng (Low Stock) | [Count] | [Value] VND | [XX]% |
| Hết hàng (Out of Stock) | [Count] | [Value] VND | [XX]% |

#### **Product Performance:**
- **Top 10 sản phẩm bán chạy:** [Product Name] - [Revenue] VND - [Volume] units
- **Sản phẩm tồn kho cao nhất:** [Product Name] - [Stock] units
- **Hàng bán mất (Lost Sales):** [Total Revenue] VND - [Total Volume] units

#### **Charts:**
- **Bar Chart:** Top 20 products by revenue
- **Area Chart:** Lost sales trend by month
- **Stacked Bar:** Inventory status by brand

---

### **6. Vận động Trường (Field Operations)**

#### **Visit Performance:**
| Nhân viên | Số chuyến đi | Tỷ lệ hoàn thành | Số ngày đi thị trường | Số tỉnh đã đi | Đánh giá |
|-----------|-------------|-------------------|----------------------|--------------|----------|
| [Name] | [Count] | [XX]% | [Days] | [Count] | ⭐⭐⭐⭐ |

#### **Visit Results Distribution:**
- **Thành công (Success):** [Count] - [XX]%
- **Cần theo dõi (Follow-up):** [Count] - [XX]%
- **Vấn đề tồn kho (Stock Issue):** [Count] - [XX]%
- **Thanh toán (Payment):** [Count] - [XX]%
- **Khác (Other):** [Count] - [XX]%

#### **Charts:**
- **Bar Chart:** Visit completion by staff
- **Pie Chart:** Visit results distribution
- **Heatmap:** Visit frequency by province

---

### **7. Công nợ & Thanh toán (Accounts Receivable)**

#### **AR Aging Summary:**
| Kỳ hạn công nợ | Số lượng đơn hàng | Giá trị công nợ | Tỷ trọng |
|----------------|------------------|-----------------|----------|
| < 30 ngày | [Count] | [Value] VND | [XX]% |
| 30-60 ngày | [Count] | [Value] VND | [XX]% |
| 60-90 ngày | [Count] | [Value] VND | [XX]% |
| > 90 ngày | [Count] | [Value] VND | [XX]% |
| **Tổng cộng** | **[Count]** | **[Value] VND** | **100%** |

#### **Top 10 Dealers by Outstanding AR:**
| Xếp hạng | Tên đối tác | Công nợ | Số ngày quá hạn |
|----------|-------------|---------|----------------|
| 1 | [Dealer Name] | [Value] VND | [Days] |
| 2 | [Dealer Name] | [Value] VND | [Days] |
| ... | ... | ... | ... |

#### **Charts:**
- **Stacked Bar:** AR aging by dealer
- **Line Chart:** AR trend by month
- **Scatter Plot:** Payment performance vs revenue

---

### **8. Hiệu quả Kinh doanh (Profitability)**

#### **Profitability Summary:**
| Chỉ tiêu | Giá trị | Tỷ trọng doanh thu |
|----------|---------|-------------------|
| Doanh thu tổng (Total Revenue) | [Value] VND | 100% |
| Giá vốn hàng bán (COGS) | [Value] VND | [XX]% |
| Biên lợi nhuận gộp (Gross Margin) | [Value] VND | [XX]% |
| Chi phí vận hành (Operating Expenses) | [Value] VND | [XX]% |
| **Lợi nhuận ròng (Net Profit)** | **[Value] VND** | **[XX]%** |

#### **Profitability by Product Category:**
| Danh mục | Doanh thu | Chi phí | Lợi nhuận | Biên lợi nhuận |
|----------|-----------|---------|-----------|----------------|
| Bikes | [Value] VND | [Value] VND | [Value] VND | [XX]% |
| Gears | [Value] VND | [Value] VND | [Value] VND | [XX]% |
| CCDC | [Value] VND | [Value] VND | [Value] VND | [XX]% |
| Services | [Value] VND | [Value] VND | [Value] VND | [XX]% |
| Others | [Value] VND | [Value] VND | [Value] VND | [XX]% |

#### **Charts:**
- **Pie Chart:** Cost structure
- **Stacked Bar:** Profit by category
- **Line Chart:** Profit trend by month

---

### **9. Kết luận & Khuyến nghị (Conclusions & Recommendations)**

#### **Key Highlights:**
- **Thành tích nổi bật (Key Achievements):** [Bullet points of positive outcomes]
- **Thách thức chính (Main Challenges):** [Bullet points of areas needing improvement]
- **Cơ hội tăng trưởng (Growth Opportunities):** [Bullet points of potential opportunities]

#### **Action Items:**
1. **Ngắn hạn (Short-term - 30 days):** [Immediate actions]
2. **Trung hạn (Medium-term - 90 days):** [Strategic improvements]
3. **Dài hạn (Long-term - 1 year):** [Long-term initiatives]

#### **Risk Assessment:**
- **Rủi ro cao (High Risk):** [Critical issues requiring immediate attention]
- **Rủi ro trung bình (Medium Risk):** [Issues to monitor closely]
- **Rủi ro thấp (Low Risk):** [Minor issues to track]

---

## Data Sources & Calculations

### **Required Data Tables:**
1. **sale_records** - Revenue, volume, date_transfer
2. **sales_targets** - Monthly/annual targets by sub-region
3. **dealer_master** - Dealer information, region mapping
4. **product_master** - Product details, brand grouping
5. **inventory_status** - Current inventory levels
6. **lost_sales_entry** - Missed sales opportunities
7. **field_visit_plans** - Planned visits
8. **visit_logs** - Actual visit results
9. **accounts_receivable_ledger** - Payment tracking, AR aging
10. **incoming_shipments** - Future inventory

### **Key Calculations:**

#### **Target Completion Rate:**
```
Completion Rate (%) = (Actual Revenue / Target Revenue) × 100
```

#### **Year-over-Year Growth:**
```
YoY Growth (%) = ((Current Year - Previous Year) / Previous Year) × 100
```

#### **AR Aging Bucket:**
```
Days Overdue = Current Date - Due Date
Bucket = FLOOR(Days Overdue / bucket_size)
```

#### **Visit Adherence:**
```
Adherence Rate (%) = (Planned Visits Completed / Total Planned Visits) × 100
```

#### **Gross Margin:**
```
Gross Margin (%) = (Revenue - COGS) / Revenue × 100
```

---

## Report Generation Workflow

### **User Interface (Vietnamese):**

#### **Report Configuration Page:**
```
BÁO CÁO MỤC TIÊU NĂM (Year Target Report)

Năm báo cáo (Report Year): [Dropdown: 2024, 2025, 2026, ...]
Kỳ báo cáo (Report Period):
  ☑️ Quý 1 (Q1)
  ☑️ Quý 2 (Q2)
  ☑️ Quý 3 (Q3)
  ☑️ Quý 4 (Q4)
  ☑️ Cả năm (Full Year)

Vùng (Region):
  ☑️ Tất cả (All)
  ☐ Miền Bắc
  ☐ Miền Trung
  ☐ Miền Nam

Thương hiệu (Brand):
  ☑️ Tất cả (All)
  ☐ Giant
  ☐ Java
  ☐ OEM
  ☐ Gears
  ☐ Others

Nội dung báo cáo (Report Sections):
  ☑️ Tổng quan (Executive Summary)
  ☑️ Hiệu suất theo Vùng (Regional Performance)
  ☑️ Phân tích theo Thương hiệu (Brand Performance)
  ☑️ Hiệu suất Đối tác (Dealer Performance)
  ☑️ Tồn kho & Sản phẩm (Inventory & Products)
  ☑️ Vận động Trường (Field Operations)
  ☑️ Công nợ & Thanh toán (Accounts Receivable)
  ☑️ Hiệu quả Kinh doanh (Profitability)
  ☑️ Kết luận & Khuyến nghị (Conclusions & Recommendations)

[📊 Tạo báo cáo (Generate Report)]
```

#### **Export Options:**
```
Định dạng xuất (Export Format):
  ⭘ PowerPoint (PPTX) - Dành cho trình bày (For presentations)
  ⭘ PDF - Dành cho lưu trữ (For archiving)

[💾 Xuất báo cáo (Export Report)]
```

---

## Implementation Requirements

### **Technical Specifications:**

#### **PPT Export (python-pptx):**
- **Slide Layout:**
  - Slide 1: Title slide with company logo and report metadata
  - Slide 2: Executive Summary (6 KPI cards)
  - Slides 3-4: Regional Performance (table + charts)
  - Slide 5: Brand Performance (table + pie chart)
  - Slides 6-7: Dealer Performance (table + charts)
  - Slide 8: Inventory & Products (table + charts)
  - Slide 9: Field Operations (table + charts)
  - Slide 10: Accounts Receivable (table + charts)
  - Slide 11: Profitability (table + charts)
  - Slide 12: Conclusions & Recommendations

- **Visual Design:**
  - Company colors: Blue (primary), Green (success), Red (warning), Yellow (caution)
  - Font: Arial or Roboto (support Vietnamese characters)
  - Chart colors: Consistent color scheme across all charts
  - Table formatting: Alternating row colors, bold headers, right-aligned numbers

#### **PDF Export (WeasyPrint):**
- **Page Layout:**
  - A4 portrait orientation
  - Header: Report title, year, generated date
  - Footer: Page number, company name
  - Margins: 1 inch on all sides

- **Styling:**
  - Professional business report format
  - Table of contents with page numbers
  - Section headers with clear hierarchy
  - Print-friendly colors (avoid dark backgrounds)

---

## Business Logic & Rules

### **Target Source:**
- **Annual Targets:** Stored in `sales_targets` table aggregated by sub-region
- **Monthly Targets:** Summed for annual totals
- **Target Allocation:** Targets distributed by sub-region based on historical performance

### **Comparison Logic:**
- **Year-over-Year:** Compare current YTD vs same period previous year
- **Target vs Actual:** Compare actual revenue/volume vs annual target
- **Quarterly Breakdown:** Show progress by quarter for full-year reports

### **Performance Thresholds:**
- **Excellent:** >100% of target, >20% YoY growth
- **Good:** 80-100% of target, 5-20% YoY growth
- **Needs Improvement:** 60-80% of target, -5% to 5% YoY growth
- **At Risk:** <60% of target, <-5% YoY growth

### **Data Freshness:**
- **Real-time data:** All KPIs calculated from current database state
- **Historical comparisons:** Previous year data from `sale_records` filtered by year
- **Trend analysis:** Monthly aggregations for line charts and trends

---

## Access Control & Security

### **Role Permissions:**
- **Admin:** Full access to generate and export all reports
- **Manager:** Full access to generate and export all reports
- **Sales Staff:** **NO ACCESS** to year target report (profitability sensitive)

### **Audit Trail:**
- **Log Generation:** Every report generation logged in `audit_logs` table
- **Track User:** Username, timestamp, report parameters
- **Export Tracking:** Export format (PPT/PDF), file size, download count

### **Data Privacy:**
- **No Personal Data:** Report contains aggregated business metrics only
- **Dealer Anonymization:** Option to mask dealer names in non-executive versions
- **Sensitive Data:** Profitability section available to Admin & Manager only

---

## Testing Requirements

### **Unit Tests:**
- KPI calculation accuracy (target completion, YoY growth, AR aging)
- Data aggregation logic (regional, brand, dealer totals)
- Chart data preparation (correct series, labels, values)
- Report section generation (all 9 sections)

### **Integration Tests:**
- End-to-end PPT generation with sample data
- End-to-end PDF generation with sample data
- Export file validation (format, content, Vietnamese character encoding)
- Database query performance (report generation < 30 seconds)

### **E2E Tests (Playwright):**
- User interface navigation (report configuration page)
- Report generation workflow (button clicks, form submission)
- Export functionality (file download, format verification)
- Role-based access control (Sales Staff denied access)

---

## Performance Considerations

### **Query Optimization:**
- **Indexed Columns:** date_transfer, dealer_id, item_id, sub_region, month_year
- **Aggregation Caching:** Cache monthly aggregations for faster reporting
- **Lazy Loading:** Generate sections on-demand for large reports

### **File Size Management:**
- **PPTX Limit:** Keep file size < 10MB (optimize images, compress charts)
- **PDF Limit:** Keep file size < 5MB (optimize fonts, compress images)
- **Generation Timeout:** Set 60-second timeout for report generation

---

## Future Enhancements

### **Phase 2 Features:**
- **Comparative Reports:** Compare multiple years side-by-side
- **Forecasting:** Predict year-end performance based on current trends
- **Drill-Down:** Click on charts to see detailed dealer/product data
- **Scheduled Reports:** Auto-generate and email reports monthly/quarterly
- **Custom Templates:** User-defined report templates and layouts

### **Advanced Analytics:**
- **Dealer Segmentation:** Cluster analysis for dealer performance groups
- **Product Lifecycle:** Track product performance over time
- **Market Analysis:** Competitor benchmarking (manual data entry)
- **Predictive Models:** Machine learning for sales forecasting

---

## Related Documentation

- **Business Logic:** [MASTER_DECISIONS.md](MASTER_DECISIONS.md)
- **Database Schema:** [SCHEMA.md](SCHEMA.md)
- **Dashboard Designs:** [DASHBOARDS.md](DASHBOARDS.md)
- **Data Validation:** [DATA_VALIDATION.md](DATA_VALIDATION.md)
- **Security:** [SECURITY.md](SECURITY.md)
- **Implementation Plan:** [docs/superpowers/plans/2026-04-28-dealer-report-full-build.md](docs/superpowers/plans/2026-04-28-dealer-report-full-build.md)

---

**This specification provides the complete blueprint for implementing the Year Target Observation Report feature. All UI elements, data sources, calculations, and export formats are defined in Vietnamese as required by the language policy.**
