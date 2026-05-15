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
        st.stop()

    MainDataFrame = pd.DataFrame([r.__dict__ for r in SalesRows]).drop(columns=["_sa_instance_state"], errors="ignore")
    MainDataFrame["date_transfer"] = pd.to_datetime(MainDataFrame["date_transfer"], dayfirst=True, errors="coerce")
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
        
        def FixBrandGroup(row):
            """Apply custom business rules for brand categorization"""
            Category = str(row.get("category", "")).strip().lower()
            BrandName = str(row.get("brand", "")).strip().lower()
            SubCategory = str(row.get("subcategory", "")).strip().lower()
            
            if Category == "gears": return "gears"
            if Category == "bikes":
                if any(x in SubCategory for x in ["e-bikes", "e-scooters"]): return "others"
                if any(x in BrandName for x in ["jeep", "hitasa"]): return "others"
                if any(x in BrandName for x in ["giant", "liv", "momentum"]): return "giant bikes"
                if "java" in BrandName: return "java bikes"
                return "oem bikes"
            return "others"
        
        ProductDataFrame["brand_group"] = ProductDataFrame.apply(FixBrandGroup, axis=1)
        MainDataFrame = MainDataFrame.merge(ProductDataFrame[["item_id", "brand_group", "brand", "category"]], on="item_id", how="left")
    else:
        MainDataFrame["brand_group"] = "others"
        MainDataFrame["brand"] = ""
        MainDataFrame["category"] = ""

    MainDataFrame["region"] = MainDataFrame["region"].fillna("Unknown")
    MainDataFrame["brand_group"] = MainDataFrame["brand_group"].fillna("others")

    BrandLabelMap = {
        "gears": "Phụ kiện",
        "giant bikes": "Xe Giant",
        "java bikes": "Xe Java",
        "oem bikes": "Xe OEM",
        "others": "Khác"
    }
    MainDataFrame["brand_group"] = MainDataFrame["brand_group"].map(BrandLabelMap).fillna("Khác")

    st.sidebar.header("Bộ lọc")

    # Initialize filter state if not exists
    if "filter_region" not in st.session_state: st.session_state.filter_region = []
    if "filter_brand" not in st.session_state: st.session_state.filter_brand = []
    if "filter_staff" not in st.session_state: st.session_state.filter_staff = []
    if "filter_channel" not in st.session_state: st.session_state.filter_channel = []
    if "filter_dealer" not in st.session_state: st.session_state.filter_dealer = []

    if st.sidebar.button("Xóa tất cả bộ lọc", use_container_width=True):
        st.session_state.filter_region = []
        st.session_state.filter_brand = []
        st.session_state.filter_staff = []
        st.session_state.filter_channel = []
        st.session_state.filter_dealer = []
        st.rerun()

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
    st.session_state.filter_region = st.sidebar.multiselect("Vùng miền", RegionList, default=st.session_state.filter_region)
    SelectedRegion = st.session_state.filter_region

    BrandGroupList = sorted(MainDataFrame["brand_group"].dropna().unique().tolist())
    st.session_state.filter_brand = st.sidebar.multiselect("Nhóm thương hiệu", BrandGroupList, default=st.session_state.filter_brand)
    SelectedBrand = st.session_state.filter_brand

    SalespersonList = sorted(MainDataFrame["salesperson"].dropna().unique().tolist())
    st.session_state.filter_staff = st.sidebar.multiselect("Nhân viên bán hàng", SalespersonList, default=st.session_state.filter_staff)
    SelectedSalesperson = st.session_state.filter_staff

    ChannelList = sorted(MainDataFrame["channel_name"].dropna().unique().tolist())
    st.session_state.filter_channel = st.sidebar.multiselect("Kênh", ChannelList, default=st.session_state.filter_channel)
    SelectedChannel = st.session_state.filter_channel

    DealerList = sorted(MainDataFrame["dealer_name"].dropna().unique().tolist())
    st.session_state.filter_dealer = st.sidebar.multiselect("Đối tác", DealerList, default=st.session_state.filter_dealer)
    SelectedDealer = st.session_state.filter_dealer

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
        FilteredData = FilteredData[FilteredData["brand_group"].isin(SelectedBrand)]
        PreviousFilteredData = PreviousFilteredData[PreviousFilteredData["brand_group"].isin(SelectedBrand)]
    if SelectedSalesperson:
        FilteredData = FilteredData[FilteredData["salesperson"].isin(SelectedSalesperson)]
        PreviousFilteredData = PreviousFilteredData[PreviousFilteredData["salesperson"].isin(SelectedSalesperson)]
    if SelectedChannel:
        FilteredData = FilteredData[FilteredData["channel_name"].isin(SelectedChannel)]
        PreviousFilteredData = PreviousFilteredData[PreviousFilteredData["channel_name"].isin(SelectedChannel)]
    if SelectedDealer:
        FilteredData = FilteredData[FilteredData["dealer_name"].isin(SelectedDealer)]
        PreviousFilteredData = PreviousFilteredData[PreviousFilteredData["dealer_name"].isin(SelectedDealer)]

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

    ChartCol1, ChartCol2 = st.columns(2)

    # Revenue trends visualization
    MonthlyRevenueTrend = FilteredData.groupby("month_year")["sales_revenue"].sum().reset_index().sort_values("month_year")
    ChartCol1.plotly_chart(
        line_chart(MonthlyRevenueTrend, "month_year", "sales_revenue", "Xu hướng doanh thu"),
        use_container_width=True
    )

    # Geographic breakdown visualization
    RegionalCurrentStats = FilteredData.groupby("region").agg(
        revenue=("sales_revenue", "sum"),
        volume=("sales_volume", "sum"),
        dealers=("dealer_id", "nunique")
    ).reset_index()

    RegionalPreviousRevenue = PreviousFilteredData.groupby("region")["sales_revenue"].sum().reset_index().rename(columns={"sales_revenue": "revenue"})
    RegionalComparisonData = RegionalCurrentStats.merge(RegionalPreviousRevenue, on="region", how="left", suffixes=("", "_prev"))

    RegionalComparisonData["growth"] = ((RegionalComparisonData["revenue"] - RegionalComparisonData["revenue_prev"]) / RegionalComparisonData["revenue_prev"] * 100).fillna(0)
    RegionalComparisonData["Tăng trưởng"] = RegionalComparisonData["growth"].map(lambda x: f"{x:+.1f}%")

    RegChartRes = ChartCol2.plotly_chart(
        bar_chart(RegionalCurrentStats, "region", "revenue", "Phân vùng kinh doanh"),
        use_container_width=True,
        on_select="rerun"
    )
    if RegChartRes.get("selection", {}).get("points"):
        st.session_state.filter_region = [p["x"] for p in RegChartRes["selection"]["points"]]
        st.rerun()

    with ChartCol2:
        RegionalDisplayTable = RegionalComparisonData[["region", "revenue", "volume", "dealers", "Tăng trưởng"]].copy()
        RegionalDisplayTable.columns = ["Vùng", "Doanh số (VND)", "Số lượng", "Số đối tác", "Tăng trưởng"]
        RegTableRes = st.dataframe(
            RegionalDisplayTable.sort_values("Doanh số (VND)", ascending=False), 
            use_container_width=True, 
            hide_index=True,
            on_select="rerun",
            selection_mode="multi-row",
            column_config={
                "Doanh số (VND)": st.column_config.NumberColumn(format="%,d"),
                "Số lượng": st.column_config.NumberColumn(format="%,d"),
                "Số đối tác": st.column_config.NumberColumn(format="%,d")
            }
        )
        if RegTableRes.get("selection", {}).get("rows"):
            SelectedTableRegions = RegionalDisplayTable.sort_values("Doanh số (VND)", ascending=False).iloc[RegTableRes["selection"]["rows"]]["Vùng"].tolist()
            st.session_state.filter_region = SelectedTableRegions
            st.rerun()

    ChartCol3, ChartCol4 = st.columns(2)

    # Brand performance visualization
    BrandCurrentStats = FilteredData.groupby("brand_group").agg(
        revenue=("sales_revenue", "sum"),
        volume=("sales_volume", "sum")
    ).reset_index()

    BrandPreviousRevenue = PreviousFilteredData.groupby("brand_group")["sales_revenue"].sum().reset_index().rename(columns={"sales_revenue": "revenue"})
    BrandComparisonData = BrandCurrentStats.merge(BrandPreviousRevenue, on="brand_group", how="left", suffixes=("", "_prev"))

    BrandComparisonData["growth"] = ((BrandComparisonData["revenue"] - BrandComparisonData["revenue_prev"]) / BrandComparisonData["revenue_prev"] * 100).fillna(0)
    BrandComparisonData["Tăng trưởng"] = BrandComparisonData["growth"].map(lambda x: f"{x:+.1f}%")

    BrandChartRes = ChartCol3.plotly_chart(
        bar_chart(BrandCurrentStats.sort_values("revenue", ascending=False), "brand_group", "revenue", "Hiệu suất thương hiệu"),
        use_container_width=True,
        on_select="rerun"
    )
    if BrandChartRes.get("selection", {}).get("points"):
        st.session_state.filter_brand = [p["x"] for p in BrandChartRes["selection"]["points"]]
        st.rerun()

    with ChartCol3:
        BrandDisplayTable = BrandComparisonData.sort_values("revenue", ascending=False)
        BrandDisplayTable = BrandDisplayTable[["brand_group", "revenue", "volume", "Tăng trưởng"]]
        BrandDisplayTable.columns = ["Nhóm thương hiệu", "Doanh số (VND)", "Số lượng", "Tăng trưởng"]
        BrandTableRes = st.dataframe(
            BrandDisplayTable, 
            use_container_width=True, 
            hide_index=True,
            on_select="rerun",
            selection_mode="multi-row",
            column_config={
                "Doanh số (VND)": st.column_config.NumberColumn(format="%,d"),
                "Số lượng": st.column_config.NumberColumn(format="%,d")
            }
        )
        if BrandTableRes.get("selection", {}).get("rows"):
            st.session_state.filter_brand = BrandDisplayTable.iloc[BrandTableRes["selection"]["rows"]]["Nhóm thương hiệu"].tolist()
            st.rerun()

    # Sales staff performance visualization
    StaffCurrentStats = FilteredData.groupby("salesperson").agg(
        revenue=("sales_revenue", "sum"),
        volume=("sales_volume", "sum"),
        dealers=("dealer_id", "nunique")
    ).reset_index()

    StaffPreviousRevenue = PreviousFilteredData.groupby("salesperson")["sales_revenue"].sum().reset_index().rename(columns={"sales_revenue": "revenue"})
    StaffComparisonData = StaffCurrentStats.merge(StaffPreviousRevenue, on="salesperson", how="left", suffixes=("", "_prev"))

    StaffComparisonData["growth"] = ((StaffComparisonData["revenue"] - StaffComparisonData["revenue_prev"]) / StaffComparisonData["revenue_prev"] * 100).fillna(0)
    StaffComparisonData["Tăng trưởng"] = StaffComparisonData["growth"].map(lambda x: f"{x:+.1f}%")

    StaffChartRes = ChartCol4.plotly_chart(
        horizontal_bar_chart(StaffCurrentStats.sort_values("revenue", ascending=True), "revenue", "salesperson", "Hiệu suất nhân viên bán hàng"),
        use_container_width=True,
        on_select="rerun"
    )
    if StaffChartRes.get("selection", {}).get("points"):
        st.session_state.filter_staff = [p["y"] for p in StaffChartRes["selection"]["points"]]
        st.rerun()

    with ChartCol4:
        StaffDisplayTable = StaffComparisonData.sort_values("revenue", ascending=False)
        StaffDisplayTable = StaffDisplayTable[["salesperson", "revenue", "volume", "dealers", "Tăng trưởng"]]
        StaffDisplayTable.columns = ["Nhân viên", "Doanh số (VND)", "Số lượng", "Số đối tác", "Tăng trưởng"]
        StaffTableRes = st.dataframe(
            StaffDisplayTable, 
            use_container_width=True, 
            hide_index=True,
            on_select="rerun",
            selection_mode="multi-row",
            column_config={
                "Doanh số (VND)": st.column_config.NumberColumn(format="%,d"),
                "Số lượng": st.column_config.NumberColumn(format="%,d"),
                "Số đối tác": st.column_config.NumberColumn(format="%,d")
            }
        )
        if StaffTableRes.get("selection", {}).get("rows"):
            st.session_state.filter_staff = StaffDisplayTable.iloc[StaffTableRes["selection"]["rows"]]["Nhân viên"].tolist()
            st.rerun()

    st.divider()

    # Dealer ranking details
    TopDealerData = FilteredData.groupby(["dealer_id", "dealer_name"]).agg(
        revenue=("sales_revenue", "sum"),
        volume=("sales_volume", "sum"),
        province=("province", "first")
    ).reset_index().sort_values("revenue", ascending=False).head(10)

    st.subheader("Top 10 Đối tác theo Doanh số")
    TopDealerChartRes = st.plotly_chart(
        horizontal_bar_chart(TopDealerData.sort_values("revenue", ascending=True), "revenue", "dealer_name", "Biểu đồ Top 10 Đối tác"),
        use_container_width=True,
        on_select="rerun"
    )
    if TopDealerChartRes.get("selection", {}).get("points"):
        st.session_state.filter_dealer = [p["y"] for p in TopDealerChartRes["selection"]["points"]]
        st.rerun()

    PreviousDealerRevenue = PreviousFilteredData.groupby("dealer_id")["sales_revenue"].sum().reset_index().rename(columns={"sales_revenue": "revenue"})
    TopDealerData = TopDealerData.merge(PreviousDealerRevenue, on="dealer_id", how="left", suffixes=("", "_prev"))
    TopDealerData["growth"] = ((TopDealerData["revenue"] - TopDealerData["revenue_prev"]) / TopDealerData["revenue_prev"] * 100).fillna(0)
    TopDealerData["Tăng trưởng"] = TopDealerData["growth"].map(lambda x: f"{x:+.1f}%")
    TopDealerData["Hạng"] = range(1, len(TopDealerData) + 1)

    TopDealerDisplayTable = TopDealerData[["Hạng", "dealer_name", "province", "revenue", "volume", "Tăng trưởng"]].copy()
    TopDealerDisplayTable.columns = ["Hạng", "Tên đối tác", "Tỉnh", "Doanh số (VND)", "Số lượng", "Tăng trưởng"]
    TopDealerTableRes = st.dataframe(
        TopDealerDisplayTable, 
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="multi-row",
        column_config={
            "Doanh số (VND)": st.column_config.NumberColumn(format="%,d"),
            "Số lượng": st.column_config.NumberColumn(format="%,d")
        }
    )
    if TopDealerTableRes.get("selection", {}).get("rows"):
        st.session_state.filter_dealer = TopDealerDisplayTable.iloc[TopDealerTableRes["selection"]["rows"]]["Tên đối tác"].tolist()
        st.rerun()
    st.divider()

    # Raw data transaction log
    with st.expander("Xem dữ liệu gốc"):
        RawColumnSelection = ["order_id", "date_transfer", "dealer_id", "dealer_name", "salesperson",
                    "channel_name", "brand_group", "sales_volume", "sales_revenue"]
        RawTransactionLog = FilteredData[RawColumnSelection].copy()
        RawTransactionLog.columns = ["Mã đơn hàng", "Ngày chuyển", "Mã đối tác", "Tên đối tác",
                          "Nhân viên", "Kênh", "Nhóm thương hiệu", "Số lượng", "Doanh số"]
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
