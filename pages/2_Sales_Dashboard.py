import streamlit as st
import pandas as pd
from database.session import get_db
from database.models import SaleRecord, DealerMaster, ProductMaster, SalesTarget
from services.analytics import calc_total_revenue, calc_gross_profit, calc_target_completion
from services.export_ppt import generate_ppt_bytes
from components.kpi_cards import render_kpi_row
from components.charts import bar_chart, pie_chart, line_chart, horizontal_bar_chart, stacked_bar_chart
from components.ui_utils import show_centered_loader

# Display centered loading animation during initial render
PageLoader = show_centered_loader()

try:
    try:
        from services.export_pdf import generate_pdf_bytes, build_dashboard_html
        PdfExportAvailable = True
    except (ImportError, OSError):
        PdfExportAvailable = False

    st.set_page_config(page_title="Báo cáo Doanh số & Doanh thu", layout="wide")

    if "user" not in st.session_state:
        st.error("Vui lòng đăng nhập từ trang chủ.")
        st.stop()

    CurrentUser = st.session_state["user"]
    st.caption("Doanh số > Tổng quan")
    st.title("Doanh số")

    DatabaseSession = get_db()
    try:
        SalesRows = DatabaseSession.query(SaleRecord).all()
        DealerRows = DatabaseSession.query(DealerMaster).all()
        ProductRows = DatabaseSession.query(ProductMaster).all()
        TargetRows = DatabaseSession.query(SalesTarget).all()
    finally:
        DatabaseSession.close()

    if not SalesRows:
        st.info("Không có dữ liệu bán hàng. Vui lòng tải dữ liệu lên qua trang Upload.")
        PageLoader.empty()
        st.stop()

    MainDataFrame = pd.DataFrame([r.__dict__ for r in SalesRows]).drop(columns=["_sa_instance_state"], errors="ignore")
    MainDataFrame["date_transfer"] = pd.to_datetime(MainDataFrame["date_transfer"], format="mixed", errors="coerce")
    MainDataFrame["month_year"] = MainDataFrame["date_transfer"].dt.strftime("%m/%Y")
    MainDataFrame[["sales_revenue", "cost_of_goods", "sales_volume", "total_price_standard"]] = (
        MainDataFrame[["sales_revenue", "cost_of_goods", "sales_volume", "total_price_standard"]].apply(pd.to_numeric, errors="coerce")
    )

    # Join with Dealer Master to retrieve geographic region
    if DealerRows:
        DealerDataFrame = pd.DataFrame([r.__dict__ for r in DealerRows]).drop(columns=["_sa_instance_state"], errors="ignore")
        DealerDataFrame["dealer_id"] = DealerDataFrame["dealer_id"].str.strip()
        MainDataFrame["dealer_id"] = MainDataFrame["dealer_id"].str.strip()
        
        def FixRegion(row):
            """Apply auto-assignment rule for region based on sub_region code"""
            if pd.notna(row.get("region")) and str(row.get("region")).strip() not in ["", "Unknown"]:
                return row["region"]
            SubRegionCode = str(row.get("sub_region", "")).strip().upper()
            if "MN" in SubRegionCode: return "Miền Nam"
            if "MB" in SubRegionCode: return "Miền Bắc"
            if "MT" in SubRegionCode: return "Miền Trung"
            return "Unknown"
        
        DealerDataFrame["region"] = DealerDataFrame.apply(FixRegion, axis=1)
        MainDataFrame = MainDataFrame.merge(DealerDataFrame[["dealer_id", "dealer_name", "region", "province"]], on="dealer_id", how="left")
    else:
        MainDataFrame["dealer_name"] = ""
        MainDataFrame["region"] = "Unknown"
        MainDataFrame["province"] = ""

    # Join with Product Master to retrieve brand grouping
    if ProductRows:
        ProductDataFrame = pd.DataFrame([r.__dict__ for r in ProductRows]).drop(columns=["_sa_instance_state"], errors="ignore")
        ProductDataFrame["item_id"] = ProductDataFrame["item_id"].str.strip()
        MainDataFrame["item_id"] = MainDataFrame["item_id"].str.strip()
        
        def FixProductGroup(row):
            """Apply custom business rules for product categorization"""
            Category = str(row.get("category", "")).strip().lower()
            BrandName = str(row.get("brand", "")).strip().lower()
            SubCategory = str(row.get("subcategory", "")).strip().lower()
            
            if Category == "gears":
                if BrandName == "maxxis": return "maxxis"
                return "gears"
            if Category == "bikes":
                if any(x in SubCategory for x in ["e-bikes", "e-scooters"]): return "others"
                if any(x in BrandName for x in ["jeep", "hitasa"]): return "oem bikes"
                if any(x in BrandName for x in ["giant", "liv", "momentum"]): return "giant bikes"
                if "java" in BrandName: return "java bikes"
                return "oem bikes"
            return "others"
        
        ProductDataFrame["product_group"] = ProductDataFrame.apply(FixProductGroup, axis=1)
        MainDataFrame = MainDataFrame.merge(ProductDataFrame[["item_id", "product_group", "brand", "category", "subcategory", "model", "color", "size", "item_name"]], on="item_id", how="left")
    else:
        MainDataFrame["product_group"] = "others"
        MainDataFrame["brand"] = ""
        MainDataFrame["category"] = ""
        MainDataFrame["subcategory"] = ""
        MainDataFrame["model"] = ""
        MainDataFrame["color"] = ""
        MainDataFrame["size"] = ""
        MainDataFrame["item_name"] = ""

    MainDataFrame["region"] = MainDataFrame["region"].fillna("Unknown")
    MainDataFrame["product_group"] = MainDataFrame["product_group"].fillna("others")

    ProductGroupLabelMap = {
        "gears": "Phụ kiện",
        "maxxis": "Maxxis",
        "giant bikes": "Xe Giant",
        "java bikes": "Xe Java",
        "oem bikes": "Xe OEM",
        "others": "Khác"
    }
    MainDataFrame["product_group"] = MainDataFrame["product_group"].map(ProductGroupLabelMap).fillna("Khác")

    st.sidebar.header("Bộ lọc")

    TimeOptions = {
        "Hôm nay": "D",
        "Tuần này": "W",
        "Tháng này": "M",
        "Tháng trước": "LM",
        "Quý": "Q",
        "Quý trước": "LQ",
        "Năm": "Y",
        "Năm trước": "LY",
        "Tùy chỉnh": "Custom"
    }
    SelectedTime = st.sidebar.selectbox("Khoảng thời gian", list(TimeOptions.keys()), index=2)

    RegionList = sorted(MainDataFrame["region"].dropna().unique().tolist())
    SelectedRegion = st.sidebar.multiselect("Vùng miền", RegionList)

    ProductGroupList = sorted(MainDataFrame["product_group"].dropna().unique().tolist())
    SelectedBrand = st.sidebar.multiselect("Nhóm sản phẩm", ProductGroupList)

    SalespersonList = sorted(MainDataFrame["salesperson"].dropna().unique().tolist())
    SelectedSalesperson = st.sidebar.multiselect("Nhân viên bán hàng", SalespersonList)

    ChannelList = sorted(MainDataFrame["channel_name"].dropna().unique().tolist())
    SelectedChannel = st.sidebar.multiselect("Kênh", ChannelList)

    Today = pd.Timestamp.now()
    FilteredData = MainDataFrame.copy()
    PreviousFilteredData = MainDataFrame.copy()

    if SelectedTime == "Hôm nay":
        FilteredData = FilteredData[FilteredData["date_transfer"].dt.date == Today.date()]
        PreviousFilteredData = PreviousFilteredData[PreviousFilteredData["date_transfer"].dt.date == Today.date() - pd.Timedelta(days=1)]
    elif SelectedTime == "Tuần này":
        WeekStart = Today - pd.Timedelta(days=Today.weekday())
        FilteredData = FilteredData[FilteredData["date_transfer"] >= WeekStart]
        PreviousFilteredData = PreviousFilteredData[(PreviousFilteredData["date_transfer"] >= WeekStart - pd.Timedelta(days=7)) & (PreviousFilteredData["date_transfer"] < WeekStart)]
    elif SelectedTime == "Tháng này":
        FilteredData = FilteredData[(FilteredData["date_transfer"].dt.month == Today.month) & (FilteredData["date_transfer"].dt.year == Today.year)]
        PreviousMonth = Today - pd.DateOffset(months=1)
        PreviousFilteredData = PreviousFilteredData[(PreviousFilteredData["date_transfer"].dt.month == PreviousMonth.month) & 
                            (PreviousFilteredData["date_transfer"].dt.year == PreviousMonth.year) &
                            (PreviousFilteredData["date_transfer"].dt.date <= PreviousMonth.date())]
    elif SelectedTime == "Tháng trước":
        LastMonth = Today - pd.DateOffset(months=1)
        FilteredData = FilteredData[(FilteredData["date_transfer"].dt.month == LastMonth.month) & (FilteredData["date_transfer"].dt.year == LastMonth.year)]
        PreviousToLastMonth = LastMonth - pd.DateOffset(months=1)
        PreviousFilteredData = PreviousFilteredData[(PreviousFilteredData["date_transfer"].dt.month == PreviousToLastMonth.month) & (PreviousFilteredData["date_transfer"].dt.year == PreviousToLastMonth.year)]
    elif SelectedTime == "Quý":
        Quarter = (Today.month - 1) // 3 + 1
        FilteredData = FilteredData[(FilteredData["date_transfer"].dt.quarter == Quarter) & (FilteredData["date_transfer"].dt.year == Today.year)]
        PreviousQuarterDate = Today - pd.DateOffset(months=3)
        PreviousQuarter = (PreviousQuarterDate.month - 1) // 3 + 1
        PreviousFilteredData = PreviousFilteredData[(PreviousFilteredData["date_transfer"].dt.quarter == PreviousQuarter) & 
                            (PreviousFilteredData["date_transfer"].dt.year == PreviousQuarterDate.year) &
                            (PreviousFilteredData["date_transfer"].dt.date <= PreviousQuarterDate.date())]
    elif SelectedTime == "Quý trước":
        LastQuarterDate = Today - pd.DateOffset(months=3)
        LastQuarter = (LastQuarterDate.month - 1) // 3 + 1
        FilteredData = FilteredData[(FilteredData["date_transfer"].dt.quarter == LastQuarter) & (FilteredData["date_transfer"].dt.year == LastQuarterDate.year)]
        PrevToLastQuarterDate = LastQuarterDate - pd.DateOffset(months=3)
        PrevToLastQuarter = (PrevToLastQuarterDate.month - 1) // 3 + 1
        PreviousFilteredData = PreviousFilteredData[(PreviousFilteredData["date_transfer"].dt.quarter == PrevToLastQuarter) & (PreviousFilteredData["date_transfer"].dt.year == PrevToLastQuarterDate.year)]
    elif SelectedTime == "Năm":
        FilteredData = FilteredData[FilteredData["date_transfer"].dt.year == Today.year]
        PreviousYear = Today - pd.DateOffset(years=1)
        PreviousFilteredData = PreviousFilteredData[(PreviousFilteredData["date_transfer"].dt.year == PreviousYear.year) &
                            (PreviousFilteredData["date_transfer"].dt.date <= PreviousYear.date())]
    elif SelectedTime == "Năm trước":
        LastYear = Today.year - 1
        FilteredData = FilteredData[FilteredData["date_transfer"].dt.year == LastYear]
        PrevToLastYear = Today.year - 2
        PreviousFilteredData = PreviousFilteredData[PreviousFilteredData["date_transfer"].dt.year == PrevToLastYear]
    elif SelectedTime == "Tùy chỉnh":
        DateRangeInput = st.sidebar.date_input("Chọn khoảng thời gian", [Today - pd.Timedelta(days=30), Today])
        if len(DateRangeInput) == 2:
            FilteredData = FilteredData[(FilteredData["date_transfer"].dt.date >= DateRangeInput[0]) & (FilteredData["date_transfer"].dt.date <= DateRangeInput[1])]
            RangeDelta = DateRangeInput[1] - DateRangeInput[0] + pd.Timedelta(days=1)
            PreviousStart = DateRangeInput[0] - RangeDelta
            PreviousEnd = DateRangeInput[0] - pd.Timedelta(days=1)
            PreviousFilteredData = PreviousFilteredData[(PreviousFilteredData["date_transfer"].dt.date >= PreviousStart) & (PreviousFilteredData["date_transfer"].dt.date <= PreviousEnd)]

    if SelectedRegion:
        FilteredData = FilteredData[FilteredData["region"].isin(SelectedRegion)]
        PreviousFilteredData = PreviousFilteredData[PreviousFilteredData["region"].isin(SelectedRegion)]
    if SelectedBrand:
        FilteredData = FilteredData[FilteredData["product_group"].isin(SelectedBrand)]
        PreviousFilteredData = PreviousFilteredData[PreviousFilteredData["product_group"].isin(SelectedBrand)]
    if SelectedSalesperson:
        FilteredData = FilteredData[FilteredData["salesperson"].isin(SelectedSalesperson)]
        PreviousFilteredData = PreviousFilteredData[PreviousFilteredData["salesperson"].isin(SelectedSalesperson)]
    if SelectedChannel:
        FilteredData = FilteredData[FilteredData["channel_name"].isin(SelectedChannel)]
        PreviousFilteredData = PreviousFilteredData[PreviousFilteredData["channel_name"].isin(SelectedChannel)]

    if FilteredData.empty:
        st.warning("Không có dữ liệu phù hợp với bộ lọc đã chọn.")
        st.stop()

    CurrentTotalRevenue = calc_total_revenue(FilteredData)
    _, MarginValue = calc_gross_profit(FilteredData)
    CurrentTotalVolume = int(FilteredData["sales_volume"].sum())
    CurrentTotalOrders = FilteredData["order_id"].nunique()
    CurrentAvgOrderValue = CurrentTotalRevenue / CurrentTotalOrders if CurrentTotalOrders > 0 else 0.0

    if not PreviousFilteredData.empty:
        PreviousRevenue = calc_total_revenue(PreviousFilteredData)
        PreviousVolume = int(PreviousFilteredData["sales_volume"].sum())
        PreviousOrders = PreviousFilteredData["order_id"].nunique()
        PreviousAvgOrder = PreviousRevenue / PreviousOrders if PreviousOrders > 0 else 0.0

        RevenueGrowth = ((CurrentTotalRevenue - PreviousRevenue) / PreviousRevenue * 100) if PreviousRevenue > 0 else 0.0
        VolumeGrowth = ((CurrentTotalVolume - PreviousVolume) / PreviousVolume * 100) if PreviousVolume > 0 else 0.0
        OrderGrowth = ((CurrentTotalOrders - PreviousOrders) / PreviousOrders * 100) if PreviousOrders > 0 else 0.0
        AvgOrderGrowth = ((CurrentAvgOrderValue - PreviousAvgOrder) / PreviousAvgOrder * 100) if PreviousAvgOrder > 0 else 0.0

        RevenueDelta = f"{RevenueGrowth:+.1f}% (Cùng kỳ)"
        VolumeDelta = f"{VolumeGrowth:+.1f}% (Cùng kỳ)"
        OrderDelta = f"{OrderGrowth:+.1f}% (Cùng kỳ)"
        AvgOrderDelta = f"{AvgOrderGrowth:+.1f}% (Cùng kỳ)"
    else:
        RevenueDelta = "N/A"
        VolumeDelta = "N/A"
        OrderDelta = "N/A"
        AvgOrderDelta = "N/A"

    if not SelectedRegion:
        RelevantTargets = TargetRows
    else:
        RegionCodeMap = {"Miền Nam": "MN", "Miền Bắc": "MB", "Miền Trung": "MT"}
        SelectedRegionCodes = [RegionCodeMap.get(r) for r in SelectedRegion if r in RegionCodeMap]
        if SelectedRegionCodes:
            RelevantTargets = [t for t in TargetRows if t.sub_region and any(t.sub_region.startswith(code) for code in SelectedRegionCodes)]
        else:
            RelevantTargets = TargetRows

    TargetRevenue = sum(t.target_revenue or 0 for t in RelevantTargets)
    CompletionRate = calc_target_completion(CurrentTotalRevenue, TargetRevenue)

    render_kpi_row([
        {"label": "Doanh số tổng", "value": f"₫{CurrentTotalRevenue:,.0f}", "delta": RevenueDelta},
        {"label": "Tổng số đơn", "value": f"{CurrentTotalOrders:,}", "delta": OrderDelta},
        {"label": "Tổng số lượng", "value": f"{CurrentTotalVolume:,}", "delta": VolumeDelta},
        {"label": "Giá trị đơn hàng", "value": f"₫{CurrentAvgOrderValue:,.0f}", "delta": AvgOrderDelta},
        {"label": "Hoàn thành mục tiêu", "value": f"{CompletionRate:.1f}%", "delta": f"Mục tiêu: ₫{TargetRevenue:,.0f}"},
    ])

    if PdfExportAvailable:
        ColExp1, ColExp2, ColExp3 = st.columns(3)
        with ColExp1:
            if st.button("Xuất PDF"):
                DashboardHtml = build_dashboard_html(
                    kpis={
                        "Doanh số tổng": f"₫{CurrentTotalRevenue:,.0f} ({RevenueDelta})",
                        "Tổng số đơn": f"{CurrentTotalOrders:,} ({OrderDelta})",
                        "Tổng số lượng": f"{CurrentTotalVolume:,} ({VolumeDelta})",
                        "Giá trị đơn hàng": f"₫{CurrentAvgOrderValue:,.0f} ({AvgOrderDelta})",
                        "Hoàn thành mục tiêu": f"{CompletionRate:.1f}% (Mục tiêu: ₫{TargetRevenue:,.0f})",
                    },
                    tables=[]
                )
                PdfBytesContent = generate_pdf_bytes(DashboardHtml)
                st.download_button("Tải PDF", data=PdfBytesContent, file_name="bao_cao_dealer_report.pdf", mime="application/pdf")
        
        with ColExp2:
            if st.button("Xuất PowerPoint"):
                PptBytesContent = generate_ppt_bytes(
                    kpis={
                        "Doanh số tổng": f"₫{CurrentTotalRevenue:,.0f} ({RevenueDelta})",
                        "Tổng số đơn": f"{CurrentTotalOrders:,} ({OrderDelta})",
                        "Tổng số lượng": f"{CurrentTotalVolume:,} ({VolumeDelta})",
                        "Giá trị đơn hàng": f"₫{CurrentAvgOrderValue:,.0f} ({AvgOrderDelta})",
                        "Hoàn thành mục tiêu": f"{CompletionRate:.1f}% (Mục tiêu: ₫{TargetRevenue:,.0f})",
                    }
                )
                st.download_button("Tải PowerPoint", data=PptBytesContent, file_name="bao_cao_dealer_report.pptx", mime="application/vnd.openxmlformats-officedocument.presentationml.presentation")

        with ColExp3:
            CsvDataContent = FilteredData.to_csv(index=False).encode("utf-8-sig")
            st.download_button("Tải CSV", data=CsvDataContent, file_name="du_lieu_ban_hang.csv", mime="text/csv")
    else:
        st.info("Tính năng xuất PDF không khả dụng (thiếu thư viện GTK). Vui lòng cài đặt GTK để sử dụng PDF export.")

    st.divider()

    # --- TABS FOR MERGED VIEW ---
    tab_overview, tab_products, tab_dealers, tab_staff, tab_profit = st.tabs([
        "📊 Tổng quan", "📦 Phân tích Sản phẩm", "🏢 Đối tác", "👤 Nhân viên", "💰 Hiệu quả KD"
    ])

    with tab_overview:
        c1, c2 = st.columns(2)
        with c1:
            with st.container(border=True):
                st.subheader("Xu hướng doanh thu")
                MonthlyRevenueTrend = FilteredData.groupby("month_year")["sales_revenue"].sum().reset_index().sort_values("month_year")
                st.plotly_chart(line_chart(MonthlyRevenueTrend, "month_year", "sales_revenue", ""), use_container_width=True)
                
        with c2:
            with st.container(border=True):
                st.subheader("Doanh số theo Vùng")
                RegionalCurrentStats = FilteredData.groupby("region").agg(
                    revenue=("sales_revenue", "sum"),
                    volume=("sales_volume", "sum"),
                    dealers=("dealer_id", "nunique")
                ).reset_index()

                RegionalPreviousRevenue = PreviousFilteredData.groupby("region")["sales_revenue"].sum().reset_index().rename(columns={"sales_revenue": "revenue"})
                RegionalComparisonData = RegionalCurrentStats.merge(RegionalPreviousRevenue, on="region", how="left", suffixes=("", "_prev"))

                RegionalComparisonData["growth"] = ((RegionalComparisonData["revenue"] - RegionalComparisonData["revenue_prev"]) / RegionalComparisonData["revenue_prev"] * 100).fillna(0)
                RegionalComparisonData["Tăng trưởng"] = RegionalComparisonData["growth"].map(lambda x: f"{x:+.1f}%")

                st.plotly_chart(bar_chart(RegionalCurrentStats, "region", "revenue", ""), use_container_width=True)
                
                RegionalDisplayTable = RegionalComparisonData[["region", "revenue", "volume", "dealers", "Tăng trưởng"]].copy()
                RegionalDisplayTable.columns = ["Vùng", "Doanh số (VND)", "Số lượng", "Số đối tác", "Tăng trưởng"]
                st.dataframe(
                    RegionalDisplayTable.sort_values("Doanh số (VND)", ascending=False), 
                    use_container_width=True, 
                    hide_index=True,
                    column_config={
                        "Doanh số (VND)": st.column_config.NumberColumn(format="%,d"),
                        "Số lượng": st.column_config.NumberColumn(format="%,d"),
                        "Số đối tác": st.column_config.NumberColumn(format="%,d")
                    }
                )

    with tab_products:
        c1, c2 = st.columns([1, 1])
        with c1:
            with st.container(border=True):
                st.subheader("Theo Nhóm Thương hiệu")
                BrandCurrentStats = FilteredData.groupby("product_group").agg(
                    revenue=("sales_revenue", "sum"),
                    volume=("sales_volume", "sum")
                ).reset_index()

                BrandPreviousRevenue = PreviousFilteredData.groupby("product_group")["sales_revenue"].sum().reset_index().rename(columns={"sales_revenue": "revenue"})
                BrandComparisonData = BrandCurrentStats.merge(BrandPreviousRevenue, on="product_group", how="left", suffixes=("", "_prev"))

                BrandComparisonData["growth"] = ((BrandComparisonData["revenue"] - BrandComparisonData["revenue_prev"]) / BrandComparisonData["revenue_prev"] * 100).fillna(0)
                BrandComparisonData["Tăng trưởng"] = BrandComparisonData["growth"].map(lambda x: f"{x:+.1f}%")

                st.plotly_chart(bar_chart(BrandCurrentStats.sort_values("revenue", ascending=False), "product_group", "revenue", ""), use_container_width=True)
                
                BrandDisplayTable = BrandComparisonData.sort_values("revenue", ascending=False)
                BrandDisplayTable = BrandDisplayTable[["product_group", "revenue", "volume", "Tăng trưởng"]]
                BrandDisplayTable.columns = ["Nhóm sản phẩm", "Doanh số (VND)", "Số lượng", "Tăng trưởng"]
                st.dataframe(
                    BrandDisplayTable, 
                    use_container_width=True, 
                    hide_index=True,
                    column_config={
                        "Doanh số (VND)": st.column_config.NumberColumn(format="%,d"),
                        "Số lượng": st.column_config.NumberColumn(format="%,d")
                    }
                )
        with c2:
            with st.container(border=True):
                st.subheader("Theo Danh mục")
                
                # Category stats with comparison
                CategoryCurrentStats = FilteredData.groupby("category").agg(
                    revenue=("sales_revenue", "sum"),
                    volume=("sales_volume", "sum")
                ).reset_index()

                CategoryPreviousRevenue = PreviousFilteredData.groupby("category")["sales_revenue"].sum().reset_index().rename(columns={"sales_revenue": "revenue"})
                CategoryComparisonData = CategoryCurrentStats.merge(CategoryPreviousRevenue, on="category", how="left", suffixes=("", "_prev"))

                CategoryComparisonData["growth"] = ((CategoryComparisonData["revenue"] - CategoryComparisonData["revenue_prev"]) / CategoryComparisonData["revenue_prev"] * 100).fillna(0)
                CategoryComparisonData["Tăng trưởng"] = CategoryComparisonData["growth"].map(lambda x: f"{x:+.1f}%")

                st.plotly_chart(bar_chart(CategoryCurrentStats, "category", "revenue", ""), use_container_width=True)
                
                CategoryDisplayTable = CategoryComparisonData[["category", "revenue", "volume", "Tăng trưởng"]].copy()
                CategoryDisplayTable.columns = ["Danh mục", "Doanh số (VND)", "Số lượng", "Tăng trưởng"]
                st.dataframe(
                    CategoryDisplayTable.sort_values("Doanh số (VND)", ascending=False), 
                    use_container_width=True, 
                    hide_index=True,
                    column_config={
                        "Doanh số (VND)": st.column_config.NumberColumn(format="%,d"),
                        "Số lượng": st.column_config.NumberColumn(format="%,d")
                    }
                )
        
        with st.container(border=True):
            st.subheader("Phân tích SKU & Top Sản phẩm")
            
            # --- TOP BIKES (Excel Pivot Compact Form) ---
            st.markdown("**Bảng tổng hợp Xe (BIKES) - Pivot View**")
            
            bikes_data = FilteredData[FilteredData["category"] == "BIKES"].copy()
            prev_bikes_data = PreviousFilteredData[PreviousFilteredData["category"] == "BIKES"].copy()
            
            def render_bikes_pivot_html(b_data, p_data):
                if b_data.empty:
                    st.info("Không có dữ liệu Xe.")
                    return

                # Group by Brand / Model for Summary
                bikes_summary = b_data.groupby(["brand", "model"]).agg(
                    revenue=("sales_revenue", "sum"),
                    volume=("sales_volume", "sum")
                ).reset_index()

                # Get Previous Summary for Growth
                prev_summary = p_data.groupby(["brand", "model"]).agg(
                    rev_prev=("sales_revenue", "sum"),
                    vol_prev=("sales_volume", "sum")
                ).reset_index()

                # Merge and calculate summary growth
                bikes_summary = bikes_summary.merge(prev_summary, on=["brand", "model"], how="left").fillna(0)
                bikes_summary["rev_growth"] = ((bikes_summary["revenue"] - bikes_summary["rev_prev"]) / bikes_summary["rev_prev"] * 100).replace([float('inf'), -float('inf')], 0).fillna(0)
                bikes_summary["vol_growth"] = ((bikes_summary["volume"] - bikes_summary["vol_prev"]) / bikes_summary["vol_prev"] * 100).replace([float('inf'), -float('inf')], 0).fillna(0)
                
                bikes_summary = bikes_summary.sort_values("volume", ascending=False)

                html_parts = []
                html_parts.append('''
                <style>
                .grid-table { display: flex; flex-direction: column; width: 100%; font-family: "Source Sans Pro", sans-serif; font-size: 14px; }
                .grid-row { display: flex; border-bottom: 1px solid #f0f2f6; align-items: center; padding: 12px 0; transition: background-color 0.2s; }
                .grid-row:hover { background-color: #f8f9fa; }
                
                .grid-header { position: sticky; top: 0; background-color: white; z-index: 10; font-weight: 600; color: #6c757d; text-transform: uppercase; font-size: 12px; border-bottom: 2px solid #e6e6e6; padding: 8px 0; margin-top: 0; }
                .child-header { font-weight: 600; color: #888; font-size: 11px; background-color: #fafafa; border-bottom: 1px solid #eee; padding: 6px 0; }
                
                .c-name { flex: 4.5; text-align: left; padding-left: 10px; font-weight: 600; color: #333; }
                .c-sku { flex: 2.0; text-align: left; padding-left: 50px; color: #555; font-size: 13px; }
                .c-color { flex: 1.5; text-align: left; color: #555; font-size: 13px; }
                .c-size { flex: 1.0; text-align: left; color: #555; font-size: 13px; }
                
                .c-rev { flex: 1.5; text-align: right; }
                .c-rg { flex: 1.0; text-align: right; }
                .c-vol { flex: 1.0; text-align: right; }
                .c-vg { flex: 1.0; text-align: right; }
                .c-tog { flex: 0.5; display: flex; justify-content: flex-end; padding-right: 10px; }

                .toggle-btn { display: none; }
                .toggle-label { cursor: pointer; border: 1px solid #ccc; border-radius: 4px; width: 24px; height: 24px; display: flex; align-items: center; justify-content: center; font-weight: bold; color: #555; background-color: white; transition: all 0.2s; margin-left: auto; }
                .toggle-label:hover { border-color: #1f77b4; color: #1f77b4; }
                .toggle-label::after { content: "＋"; }
                .toggle-btn:checked ~ .grid-row .toggle-label::after { content: "−"; }

                .child-container { display: none; flex-direction: column; background-color: #fafafa; border-bottom: 1px solid #f0f2f6; }
                .toggle-btn:checked ~ .child-container { display: flex; }

                .child-row { display: flex; align-items: center; padding: 8px 0; border-top: 1px dashed #eee; }
                
                .growth-pos { color: #28a745; font-weight: 500; }
                .growth-neg { color: #dc3545; font-weight: 500; }
                
                /* Custom Scrollbar for Webkit */
                .scroll-container::-webkit-scrollbar { width: 8px; }
                .scroll-container::-webkit-scrollbar-track { background: #f1f1f1; border-radius: 4px; }
                .scroll-container::-webkit-scrollbar-thumb { background: #ccc; border-radius: 4px; }
                .scroll-container::-webkit-scrollbar-thumb:hover { background: #aaa; }
                </style>
                <div class="scroll-container" style="max-height: 480px; overflow-y: auto; border: 1px solid #e6e6e6; border-radius: 4px;">
                    <div class="grid-table">
                        <div class="grid-row grid-header">
                        <div class="c-name">Dòng xe (Brand / Model)</div>
                        <div class="c-rev">Doanh số</div>
                        <div class="c-rg">∆ DS</div>
                        <div class="c-vol">Số lượng</div>
                        <div class="c-vg">∆ SL</div>
                        <div class="c-tog"></div>
                    </div>
                ''')

                for i, row in bikes_summary.iterrows():
                    brand = row['brand']
                    model = row['model']
                    row_key = f"toggle_{i}"
                    
                    rg = row['rev_growth']
                    color_rg = "growth-pos" if rg >= 0 else "growth-neg"
                    sign_rg = "+" if rg > 0 else ""
                    
                    vg = row['vol_growth']
                    color_vg = "growth-pos" if vg >= 0 else "growth-neg"
                    sign_vg = "+" if vg > 0 else ""

                    html_parts.append(f'''
                    <div>
                        <input type="checkbox" id="{row_key}" class="toggle-btn">
                        <div class="grid-row">
                            <div class="c-name">{brand} / {model}</div>
                            <div class="c-rev" style="font-weight: 500;">₫{row['revenue']:,.0f}</div>
                            <div class="c-rg {color_rg}">{sign_rg}{rg:.1f}%</div>
                            <div class="c-vol" style="font-weight: 500;">{row['volume']:,} chiếc</div>
                            <div class="c-vg {color_vg}">{sign_vg}{vg:.1f}%</div>
                            <div class="c-tog">
                                <label for="{row_key}" class="toggle-label"></label>
                            </div>
                        </div>
                        <div class="child-container">
                            <div class="grid-row child-header">
                                <div class="c-sku">Mã SKU</div>
                                <div class="c-color">Màu sắc</div>
                                <div class="c-size">Kích cỡ</div>
                                <div class="c-rev">Doanh số</div>
                                <div class="c-rg">∆ DS</div>
                                <div class="c-vol">Số lượng</div>
                                <div class="c-vg">∆ SL</div>
                                <div class="c-tog"></div>
                            </div>
                    ''')

                    # --- CHILD ROWS ---
                    details = b_data[(b_data["brand"] == brand) & (b_data["model"] == model)].copy()
                    variant_stats = details.groupby(["item_id", "color", "size"]).agg(
                        revenue=("sales_revenue", "sum"),
                        volume=("sales_volume", "sum")
                    ).reset_index()

                    prev_details = p_data[(p_data["brand"] == brand) & (p_data["model"] == model)]
                    prev_variant_stats = prev_details.groupby(["item_id", "color", "size"]).agg(
                        rev_prev=("sales_revenue", "sum"),
                        vol_prev=("sales_volume", "sum")
                    ).reset_index()

                    merged_details = variant_stats.merge(prev_variant_stats, on=["item_id", "color", "size"], how="left").fillna(0)
                    merged_details["rev_growth"] = ((merged_details["revenue"] - merged_details["rev_prev"]) / merged_details["rev_prev"] * 100).replace([float('inf'), -float('inf')], 0).fillna(0)
                    merged_details["vol_growth"] = ((merged_details["volume"] - merged_details["vol_prev"]) / merged_details["vol_prev"] * 100).replace([float('inf'), -float('inf')], 0).fillna(0)
                    merged_details = merged_details.sort_values("volume", ascending=False)

                    for _, c_row in merged_details.iterrows():
                        crg = c_row['rev_growth']
                        color_crg = "growth-pos" if crg >= 0 else "growth-neg"
                        sign_crg = "+" if crg > 0 else ""
                        
                        cvg = c_row['vol_growth']
                        color_cvg = "growth-pos" if cvg >= 0 else "growth-neg"
                        sign_cvg = "+" if cvg > 0 else ""

                        html_parts.append(f'''
                            <div class="child-row">
                                <div class="c-sku">{c_row['item_id']}</div>
                                <div class="c-color">{c_row['color']}</div>
                                <div class="c-size">{c_row['size']}</div>
                                <div class="c-rev">₫{c_row['revenue']:,.0f}</div>
                                <div class="c-rg {color_crg}">{sign_crg}{crg:.1f}%</div>
                                <div class="c-vol">{c_row['volume']:,}</div>
                                <div class="c-vg {color_cvg}">{sign_cvg}{cvg:.1f}%</div>
                                <div class="c-tog"></div>
                            </div>
                        ''')
                    
                    html_parts.append('''
                        </div>
                    </div>
                    ''')

                html_parts.append('</div>')
                html_parts.append('</div>') # Close scroll-container
                
                final_html = "\n".join([line.strip() for line in "".join(html_parts).split("\n")])
                st.markdown(final_html, unsafe_allow_html=True)

            # Call the html render function
            render_bikes_pivot_html(bikes_data, prev_bikes_data)

            st.divider()

            # --- TOP GEARS (Standard Table) ---

    with tab_dealers:
        with st.container(border=True):
            st.subheader("Top 10 Đối tác")
            TopDealerData = FilteredData.groupby(["dealer_id", "dealer_name"]).agg(
                revenue=("sales_revenue", "sum"),
                volume=("sales_volume", "sum"),
                province=("province", "first")
            ).reset_index().sort_values("revenue", ascending=False).head(10)

            st.plotly_chart(horizontal_bar_chart(TopDealerData.sort_values("revenue", ascending=True), "revenue", "dealer_name", ""), use_container_width=True)

            PreviousDealerRevenue = PreviousFilteredData.groupby("dealer_id")["sales_revenue"].sum().reset_index().rename(columns={"sales_revenue": "revenue"})
            TopDealerData = TopDealerData.merge(PreviousDealerRevenue, on="dealer_id", how="left", suffixes=("", "_prev"))
            TopDealerData["growth"] = ((TopDealerData["revenue"] - TopDealerData["revenue_prev"]) / TopDealerData["revenue_prev"] * 100).fillna(0)
            TopDealerData["Tăng trưởng"] = TopDealerData["growth"].map(lambda x: f"{x:+.1f}%")
            TopDealerData["Hạng"] = range(1, len(TopDealerData) + 1)

            TopDealerDisplayTable = TopDealerData[["Hạng", "dealer_name", "province", "revenue", "volume", "Tăng trưởng"]].copy()
            TopDealerDisplayTable.columns = ["Hạng", "Tên đối tác", "Tỉnh", "Doanh số (VND)", "Số lượng", "Tăng trưởng"]
            st.dataframe(
                TopDealerDisplayTable, 
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Doanh số (VND)": st.column_config.NumberColumn(format="%,d"),
                    "Số lượng": st.column_config.NumberColumn(format="%,d")
                }
            )

    with tab_staff:
        with st.container(border=True):
            st.subheader("Hiệu suất Nhân viên")
            StaffCurrentStats = FilteredData.groupby("salesperson").agg(
                revenue=("sales_revenue", "sum"),
                volume=("sales_volume", "sum"),
                dealers=("dealer_id", "nunique")
            ).reset_index()

            StaffPreviousRevenue = PreviousFilteredData.groupby("salesperson")["sales_revenue"].sum().reset_index().rename(columns={"sales_revenue": "revenue"})
            StaffComparisonData = StaffCurrentStats.merge(StaffPreviousRevenue, on="salesperson", how="left", suffixes=("", "_prev"))

            StaffComparisonData["growth"] = ((StaffComparisonData["revenue"] - StaffComparisonData["revenue_prev"]) / StaffComparisonData["revenue_prev"] * 100).fillna(0)
            StaffComparisonData["Tăng trưởng"] = StaffComparisonData["growth"].map(lambda x: f"{x:+.1f}%")

            st.plotly_chart(horizontal_bar_chart(StaffCurrentStats.sort_values("revenue", ascending=True), "revenue", "salesperson", ""), use_container_width=True)
            
            StaffDisplayTable = StaffComparisonData.sort_values("revenue", ascending=False)
            StaffDisplayTable = StaffDisplayTable[["salesperson", "revenue", "volume", "dealers", "Tăng trưởng"]]
            StaffDisplayTable.columns = ["Nhân viên", "Doanh số (VND)", "Số lượng", "Số đối tác", "Tăng trưởng"]
            st.dataframe(
                StaffDisplayTable, 
                use_container_width=True, 
                hide_index=True,
                column_config={
                    "Doanh số (VND)": st.column_config.NumberColumn(format="%,d"),
                    "Số lượng": st.column_config.NumberColumn(format="%,d"),
                    "Số đối tác": st.column_config.NumberColumn(format="%,d")
                }
            )

    with tab_profit:
        if CurrentUser["role"] not in ["Admin", "Manager"]:
            st.warning("Bạn không có quyền truy cập dữ liệu Hiệu quả Kinh doanh (Yêu cầu quyền Admin hoặc Manager).")
        else:
            with st.container(border=True):
                st.subheader("Hiệu quả Kinh doanh (Lợi nhuận & Biên lợi nhuận)")
                profit, margin = calc_gross_profit(FilteredData)

                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Biên lợi nhuận gộp", f"{margin:.1f}%")
                c2.metric("Lợi nhuận gộp", f"₫{profit:,.0f}")
                c3.metric("Tổng doanh thu", f"₫{FilteredData['sales_revenue'].sum():,.0f}")
                c4.metric("Tổng chi phí", f"₫{FilteredData['cost_of_goods'].sum():,.0f}")

                st.divider()

                if "category" in FilteredData.columns:
                    col1, col2 = st.columns(2)

                    by_cat = FilteredData.groupby("category").agg(
                        revenue=("sales_revenue", "sum"),
                        cost=("cost_of_goods", "sum"),
                    ).reset_index()
                    by_cat["profit"] = by_cat["revenue"] - by_cat["cost"]
                    # Prevent division by zero
                    by_cat["margin_pct"] = by_cat.apply(lambda row: (row["profit"] / row["revenue"] * 100) if row["revenue"] > 0 else 0, axis=1).round(1)

                    with col1:
                        st.plotly_chart(bar_chart(by_cat, "category", "profit", "Lợi nhuận theo Danh mục"), use_container_width=True)

                    with col2:
                        # Pie chart doesn't accept negative values well, so filter out negative profit for pie chart if necessary, or just render it. Plotly handles it okay-ish, but let's be safe.
                        pie_data = by_cat[by_cat["profit"] > 0]
                        if not pie_data.empty:
                            st.plotly_chart(pie_chart(pie_data, "category", "profit", "Phân bổ Lợi nhuận theo Danh mục"), use_container_width=True)
                        else:
                            st.info("Không có dữ liệu lợi nhuận dương để vẽ biểu đồ tròn.")

                    st.markdown("**Bảng chi tiết Lợi nhuận**")
                    display_df = by_cat[["category","revenue","cost","profit","margin_pct"]].sort_values("profit", ascending=False).copy()
                    display_df.columns = ["Danh mục","Doanh thu","Chi phí","Lợi nhuận","Biên lợi nhuận (%)"]
                    st.dataframe(
                        display_df, 
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "Doanh thu": st.column_config.NumberColumn(format="₫%,d"),
                            "Chi phí": st.column_config.NumberColumn(format="₫%,d"),
                            "Lợi nhuận": st.column_config.NumberColumn(format="₫%,d"),
                            "Biên lợi nhuận (%)": st.column_config.NumberColumn(format="%.1f%%")
                        }
                    )

    st.divider()

    # Raw data transaction log
    with st.expander("Xem dữ liệu gốc"):
        RawColumnSelection = ["order_id", "date_transfer", "dealer_id", "dealer_name", "salesperson",
                    "channel_name", "product_group", "sales_volume", "sales_revenue"]
        RawTransactionLog = FilteredData[RawColumnSelection].copy()
        RawTransactionLog.columns = ["Mã đơn hàng", "Ngày chuyển", "Mã đối tác", "Tên đối tác",
                          "Nhân viên", "Kênh", "Nhóm sản phẩm", "Số lượng", "Doanh số"]
        st.dataframe(
            RawTransactionLog.reset_index(drop=True), 
            use_container_width=True,
            column_config={
                "Doanh số": st.column_config.NumberColumn(format="%,d"),
                "Số lượng": st.column_config.NumberColumn(format="%,d")
            }
        )

    if st.button("Cập nhật dữ liệu"):
        st.rerun()

    st.caption(f"Dữ liệu cập nhật lúc: {pd.Timestamp.now().strftime('%d/%m/%Y %H:%M:%S')}")

finally:
    # Hide the centered loader once rendering is complete
    PageLoader.empty()
