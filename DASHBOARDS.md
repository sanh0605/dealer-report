# DASHBOARDS.md - Dashboard Design Specification

## Dashboard Overview

**Language Requirement:** All dashboards must display in Vietnamese language throughout (buttons, labels, charts, messages, tooltips). For complete language policy, examples, and implementation requirements, see [MASTER_DECISIONS.md](MASTER_DECISIONS.md#language-policy).

---

## 1. Sales & Revenue Dashboard (Doanh số & Doanh thu)

### **Overview Cards:**
- Total Revenue (Doanh thu tổng) - VND format
- Sales Volume (Tổng số lượng) - units
- Growth Rate (Tốc độ tăng trưởng) - percentage vs previous period
- AR Ratio (Tỷ lệ công nợ) - percentage
- Average Order Value (Giá trị đơn hàng trung bình) - VND

### **Main Charts:**
- Revenue Trend Chart (Xu hướng doanh thu) - Line chart by month
- Regional Sales Breakdown (Phân vùng kinh doanh) - Stacked bar chart (Miền Nam/Miền Bắc/Miền Trung)
- Brand Performance (Hiệu suất thương hiệu) - Pie chart (Giant/Java/OEM/Gears/Others)
- Top 10 Dealers by Sales (Top 10 Đối tác theo Doanh số) - Horizontal bar chart
- Top 10 Dealers by Profit (Top 10 Đối tác theo Lợi nhuận) - Horizontal bar chart

### **Detailed Tables:**
- Regional Performance Table: Region | Revenue | Volume | Growth | AR Ratio
- Dealer Ranking Table: Rank | Dealer Name | Province | Revenue | Volume | Growth
- Salesperson Performance Table: Name | Dealers | Revenue | Volume | Growth

### **Filters:**
- Time Period: Hôm nay, Tuần này, Tháng này, Tháng trước, Quý, Năm, Tùy chỉnh
- Region: Tất cả, Miền Nam, Miền Bắc, Miền Trung
- Brand Group: Tất cả, Giant, Java, OEM, Gears, Others

---

## 2. Dealer Health Dashboard (Sức khỏe Đối tác)

### **Overview Cards:**
- Total Dealers (Tổng đối tác)
- Healthy Dealers (Đối tác tốt)
- At-Risk Dealers (Đối tác rủi ro)
- New Dealers (Đối tác mới) - added this month
- Inactive Dealers (Đối tác không hoạt động) - no sales in 90 days

### **Main Charts:**
- Dealer Health Distribution (Phân phối sức khỏe) - Donut chart (Good/Warning/Critical)
- AR Aging by Dealer (Công nợ theo đối tác) - Stacked bar chart

### **Detailed Tables:**
- Dealer Health Summary Table: Dealer | Province | Health Status | Revenue | AR Days | Payment Score
- At-Risk Dealers Alert Table: Dealer | Province | Risk Level | AR Amount | Days Overdue
- New Dealers Table: Dealer | Province | Start Date | First Order | Revenue

### **Dealer Health Criteria:**
- **Good (Tốt)**: Active sales, AR < 30 days, payment > 90%
- **Warning (Cảnh báo)**: Active sales, AR 30-60 days, payment 70-90%
- **Critical (Nguy hiểm)**: AR > 60 days, payment < 70%, or inactive

### **Filters:**
- Health Status: Tất cả, Tốt, Cảnh báo, Nguy hiểm
- Region: Tất cả, Miền Nam, Miền Bắc, Miền Trung
- AR Aging: Tất cả, <30, 30-60, >60 days

---

## 3. Product Performance Dashboard (Hiệu suất Sản phẩm)

### **Overview Cards:**
- Total Products (Tổng sản phẩm)
- In Stock (Có sẵn trong kho)
- Low Stock (Hàng sắp hết) - < 50 units
- Out of Stock (Hết hàng)
- Best Seller (Sản phẩm bán chạy nhất)

### **Main Charts:**
- Inventory by Brand (Kho theo thương hiệu) - Stacked bar chart
- Top 20 Products by Revenue (Top 20 sản phẩm theo doanh thu) - Bar chart
- Lost Sales Analysis (Phân tích hàng bán mất) - Area chart by month
- Product Performance Matrix (Ma trận hiệu suất sản phẩm) - Bubble chart (Revenue vs Volume)

### **Detailed Tables:**
- Product Performance Table: Product | Brand | Revenue | Volume | Margin | Stock Status
- Inventory Status Table: Product | Brand | Stock | Location | Status
- Lost Sales Leaders Table: Product | Brand | Lost Revenue | Lost Volume | Trend

### **Filters:**
- Brand Group: Tất cả, Giant, Java, OEM, Gears, Others
- Category: Tất cả, Bikes, Gears, CCDC, Services, Others
- Stock Status: Tất cả, Có sẵn, Sắp hết, Hết hàng
- Performance Period: 30 ngày qua, 3 tháng qua, 6 tháng qua

---

## 4. Field Operations Dashboard (Vận động trường)

### **Overview Cards:**
- Visits Completed (Đã hoàn thành)
- Visit Adherence Rate (Tỷ lệ hoàn thành kế hoạch) - percentage
- Days on Road (Số ngày đi thị trường)
- Provinces Visited (Tỉnh đã đi)
- Top Salesperson (Nhân viên xuất sắc nhất)

### **Main Charts:**
- Visit Completion by Staff (Hoàn thành chuyến đi) - Bar chart
- Regional Visit Distribution (Phân bổ chuyến đi theo vùng) - Pie chart
- Visit Frequency by Province (Tần suất chuyến đi theo tỉnh) - Heatmap
- Visit Results Analysis (Phân tích kết quả chuyến đi) - Donut chart

### **Detailed Tables:**
- Visit Plans Table: Staff | Month | Dealers Planned | Visits Completed | Adherence Rate | Days on Road
- Visit Logs Table: Date | Staff | Dealer | Province | Visit Result | Next Action
- Staff Performance Table: Staff | Visits | Adherence | Dealers | Revenue | Rating

### **Visit Result Categories:**
- **Thành công (Success)**: Sale made, relationship maintained
- **Cần theo dõi (Follow-up)**: Potential sale, needs follow-up
- **Vấn đề tồn kho (Stock Issue)**: Dealer needs inventory
- **Thanh toán (Payment)**: Payment collection discussion
- **Khác (Other)**: Other business discussed

### **Filters:**
- Staff: Tất cả, [Individual salespeople]
- Time Period: Tháng này, Tháng trước, Quý, Tùy chỉnh
- Visit Result: Tất cả, Thành công, Cần theo dõi, Vấn đề tồn kho, Thanh toán, Khác

---

## 5. Profitability Dashboard (Hiệu quả Kinh doanh)

### **⚠️ Admin & Manager Only - Not visible to Sales Staff**

### **Overview Cards:**
- Gross Margin (Biên lợi nhuận gộp) - percentage
- Net Profit (Lợi nhuận ròng) - VND
- Profit Growth (Tăng trưởng lợi nhuận) - percentage
- Average Margin per Unit (Biên lợi nhuận TB/đơn vị) - VND
- Cost Efficiency (Hiệu quả chi phí) - percentage

### **Main Charts:**
- Profit Trend (Xu hướng lợi nhuận) - Line chart by month
- Margin by Product (Biên lợi nhuận theo sản phẩm) - Stacked bar chart
- Profit by Dealer (Lợi nhuận theo đối tác) - Scatter chart
- Cost Structure (Cấu trúc chi phí) - Pie chart

### **Detailed Tables:**
- Profitability Summary Table: Product | Revenue | Cost | Profit | Margin | Rank
- Dealer Profitability Table: Dealer | Revenue | Cost | Profit | Margin | Status
- Regional Profitability Table: Region | Revenue | Cost | Profit | Margin | Growth

### **Profitability Analysis:**
- High Volume, Low Margin products
- Low Volume, High Margin products
- Best/Worst performing dealers by profit
- Cost reduction opportunities

### **Filters:**
- Time Period: Tháng này, Tháng trước, Quý, Năm, Tùy chỉnh
- Region: Tất cả, Miền Nam, Miền Bắc, Miền Trung
- Product Category: Tất cả, Bikes, Gears, CCDC, Services, Others
- Margin Range: Tất cả, <10%, 10-20%, >20%

---

## Dashboard Features

### **Common Features:**
- Vietnamese language throughout (buttons, labels, charts, messages)
- Download data to Excel/CSV
- Print dashboard to PDF
- Export dashboard to PPT
- Real-time data refresh
- Responsive design for desktop/tablet
- Color-coded indicators (green/good, red/bad, yellow/warning)

### **Interactive Elements:**
- Click charts to drill down to detailed data
- Hover for detailed tooltips
- Sortable tables
- Export individual charts
- Custom date range selector

### **Dashboard Navigation:**
- Sidebar navigation with Vietnamese labels
- Breadcrumb navigation for drill-down
- Quick filter presets
- Dashboard comparison view (side-by-side)

### **Data Refresh:**
- Auto-refresh every 5 minutes (configurable)
- Manual refresh button
- Last updated timestamp display
- Real-time indicator for live data