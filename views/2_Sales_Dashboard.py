import streamlit as st
import pandas as pd
from database.gsheets_db import read_sheet
from services.analytics import calc_total_revenue, calc_gross_profit, calc_target_completion
from services.export_ppt import generate_ppt_bytes
from components.kpi_cards import render_kpi_row
from components.charts import bar_chart, pie_chart, line_chart, horizontal_bar_chart, stacked_bar_chart
from components.ui_utils import show_centered_loader

# Display centered loading animation during initial render
PageLoader = show_centered_loader()

try:
    CurrentUser = st.session_state["user"]
    st.caption("Doanh số > Tổng quan")
    ColTitle, ColExportBtn = st.columns([8, 1], vertical_alignment="center")
    with ColTitle:
        st.title("Doanh số")
    with ColExportBtn:
        ExportBtnContainer = st.container()

    # Load data from Google Sheets
    MainDataFrame = read_sheet("sale_records")
    DealerDataFrame = read_sheet("dealer_master")
    ProductDataFrame = read_sheet("product_master")
    TargetDataFrame = read_sheet("sales_targets")

    if MainDataFrame.empty:
        st.info("Không có dữ liệu bán hàng. Vui lòng tải dữ liệu lên qua trang Upload.")
        PageLoader.empty()
        st.stop()

    # Pre-process MainDataFrame
    MainDataFrame["date_transfer"] = pd.to_datetime(MainDataFrame["date_transfer"], format="mixed", errors="coerce")
    MainDataFrame["month_year"] = MainDataFrame["date_transfer"].dt.strftime("%m/%Y")
    numeric_cols = ["sales_revenue", "cost_of_goods", "sales_volume", "total_price_standard"]
    for col in numeric_cols:
        if col in MainDataFrame.columns:
            MainDataFrame[col] = pd.to_numeric(MainDataFrame[col], errors="coerce").fillna(0)

    # Join with Dealer Master to retrieve geographic region
    if not DealerDataFrame.empty:
        DealerDataFrame["dealer_id"] = DealerDataFrame["dealer_id"].astype(str).str.strip()
        MainDataFrame["dealer_id"] = MainDataFrame["dealer_id"].astype(str).str.strip()
        
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
        # Merge, but avoid duplicate columns if already present
        cols_to_use = [c for c in ["dealer_id", "dealer_name", "region", "province", "sub_region"] if c in DealerDataFrame.columns]
        MainDataFrame = MainDataFrame.merge(DealerDataFrame[cols_to_use], on="dealer_id", how="left", suffixes=("", "_dealer"))
        # If dealer_name was already in MainDataFrame, fill NaNs
        if "dealer_name_dealer" in MainDataFrame.columns:
            MainDataFrame["dealer_name"] = MainDataFrame["dealer_name"].fillna(MainDataFrame["dealer_name_dealer"])
            MainDataFrame = MainDataFrame.drop(columns=["dealer_name_dealer"])
    else:
        for col in ["dealer_name", "region", "province", "sub_region"]:
            if col not in MainDataFrame.columns:
                MainDataFrame[col] = ""

    def AssignRegionGroup(row):
        """Apply custom business rules for region grouping based on channel and sub_region"""
        sub_region = str(row.get("sub_region", "")).strip().upper()
        if sub_region in ["MB1", "MB2"]: return "MB1+MB2"
        if sub_region in ["MB3", "MB4"]: return "MB3+MB4"
        if sub_region in ["MN1", "MN3"]: return "MN1+MN3"
        if sub_region == "MN2": return "MN2"
        if sub_region in ["MN4", "MN5", "MN6"]: return "MN4+MN5+MN6"
        return sub_region if sub_region and sub_region != "UNKNOWN" else row.get("region", "Unknown")
    
    MainDataFrame["region_group"] = MainDataFrame.apply(AssignRegionGroup, axis=1)
    
    # Siêu thị is same level as Region
    MainDataFrame.loc[MainDataFrame["channel_name"].str.upper().str.contains("SIÊU THỊ", na=False), "region"] = "Siêu thị"

    # Join with Product Master to retrieve brand grouping
    if not ProductDataFrame.empty:
        ProductDataFrame["item_id"] = ProductDataFrame["item_id"].astype(str).str.strip()
        MainDataFrame["item_id"] = MainDataFrame["item_id"].astype(str).str.strip()

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
        cols_to_use = [c for c in ["item_id", "product_group", "brand", "category", "subcategory", "model", "color", "size", "item_name"] if c in ProductDataFrame.columns]
        MainDataFrame = MainDataFrame.merge(ProductDataFrame[cols_to_use], on="item_id", how="left", suffixes=("", "_prod"))
        
        # Fill NaN for product detail columns to prevent empty UI cells
        for col in ["brand", "category", "subcategory", "model", "color", "size", "item_name"]:
            if col + "_prod" in MainDataFrame.columns:
                MainDataFrame[col] = MainDataFrame[col].fillna(MainDataFrame[col + "_prod"])
                MainDataFrame = MainDataFrame.drop(columns=[col + "_prod"])
            elif col in MainDataFrame.columns:
                MainDataFrame[col] = MainDataFrame[col].fillna("")
    else:
        for col in ["product_group", "brand", "category", "subcategory", "model", "color", "size", "item_name"]:
            if col not in MainDataFrame.columns:
                MainDataFrame[col] = "others" if col == "product_group" else ""

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

    # Date references for filters
    Today = pd.Timestamp.now()
    DataMaxDate = MainDataFrame["date_transfer"].max()
    ReferenceDate = DataMaxDate if pd.notna(DataMaxDate) else Today

    st.sidebar.header("Bộ lọc")

    # Handle both experimental and stable fragment decorators for Streamlit compatibility
    st_fragment = getattr(st, "fragment", getattr(st, "experimental_fragment", lambda f: f))

    # Initialize session state for applied filters
    if "applied_time_option" not in st.session_state:
        st.session_state.applied_time_option = "Tháng này"
    if "custom_date_range" not in st.session_state:
        st.session_state.custom_date_range = []
    if "custom_date_applied" not in st.session_state:
        st.session_state.custom_date_applied = False

    @st_fragment
    def render_date_filter_fragment():
        TimeOptionsInternal = {
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
        
        # Determine the current index for the selectbox based on applied state
        option_list = list(TimeOptionsInternal.keys())
        default_val = st.session_state.applied_time_option
        default_index = option_list.index(default_val) if default_val in option_list else 2
        
        # Use st.selectbox instead of st.sidebar.selectbox inside fragment
        SelectedTimeUI = st.selectbox("Khoảng thời gian", option_list, index=default_index)

        if SelectedTimeUI == "Tùy chỉnh":
            # Removed st.form because it batches state and prevents dynamic button enabling
            initial_val = st.session_state.custom_date_range if st.session_state.custom_date_range else []
            # Pass an empty tuple instead of a list if empty to strictly enforce range mode in Streamlit
            DateInput = st.date_input("Chọn khoảng thời gian", value=initial_val if initial_val else (), format="DD/MM/YYYY")

            if DateInput and len(DateInput) == 1:
                st.info("Vui lòng chọn ngày kết thúc để hoàn tất bộ lọc.")

            apply_enabled = DateInput and len(DateInput) == 2
            submitted = st.button(
                "Áp dụng khoảng thời gian",
                disabled=not apply_enabled,
                type="primary"
            )

            if submitted:
                st.session_state.custom_date_applied = True
                st.session_state.custom_date_range = list(DateInput)
                st.session_state.applied_time_option = "Tùy chỉnh"
                st.rerun()
        else:
            # For predefined options, apply immediately if changed
            if SelectedTimeUI != st.session_state.applied_time_option:
                st.session_state.applied_time_option = SelectedTimeUI
                st.session_state.custom_date_applied = False
                st.session_state.custom_date_range = []
                st.rerun()

    # Render the fragment inside the sidebar context
    with st.sidebar:
        render_date_filter_fragment()

    # Map applied state to variables used by the rest of the script
    SelectedTime = st.session_state.applied_time_option
    DateRangeInput = st.session_state.custom_date_range

    RegionList = sorted(MainDataFrame["region"].dropna().unique().tolist())
    SelectedRegion = st.sidebar.multiselect("Vùng miền", RegionList)

    ProductGroupList = sorted(MainDataFrame["product_group"].dropna().unique().tolist())
    SelectedBrand = st.sidebar.multiselect("Nhóm sản phẩm", ProductGroupList)

    SalespersonList = sorted(MainDataFrame["salesperson"].dropna().unique().tolist())
    SelectedSalesperson = st.sidebar.multiselect("Nhân viên bán hàng", SalespersonList)

    ChannelList = sorted(MainDataFrame["channel_name"].dropna().unique().tolist())
    SelectedChannel = st.sidebar.multiselect("Kênh", ChannelList)

    Today = pd.Timestamp.now()
    # Use the most recent date in data as reference for relative filters if today has no data
    DataMaxDate = MainDataFrame["date_transfer"].max()
    ReferenceDate = DataMaxDate if pd.notna(DataMaxDate) else Today
    
    FilteredData = MainDataFrame.copy()
    PreviousFilteredData = MainDataFrame.copy()

    if SelectedTime == "Hôm nay":
        FilteredData = FilteredData[FilteredData["date_transfer"].dt.date == ReferenceDate.date()]
        PreviousFilteredData = PreviousFilteredData[PreviousFilteredData["date_transfer"].dt.date == ReferenceDate.date() - pd.Timedelta(days=1)]
    elif SelectedTime == "Tuần này":
        WeekStart = ReferenceDate - pd.Timedelta(days=ReferenceDate.weekday())
        FilteredData = FilteredData[FilteredData["date_transfer"] >= WeekStart]
        PreviousFilteredData = PreviousFilteredData[(PreviousFilteredData["date_transfer"] >= WeekStart - pd.Timedelta(days=7)) & (PreviousFilteredData["date_transfer"] < WeekStart)]
    elif SelectedTime == "Tháng này":
        FilteredData = FilteredData[(FilteredData["date_transfer"].dt.month == ReferenceDate.month) & (FilteredData["date_transfer"].dt.year == ReferenceDate.year)]
        PreviousMonth = ReferenceDate - pd.DateOffset(months=1)
        PreviousFilteredData = PreviousFilteredData[(PreviousFilteredData["date_transfer"].dt.month == PreviousMonth.month) & 
                            (PreviousFilteredData["date_transfer"].dt.year == PreviousMonth.year) &
                            (PreviousFilteredData["date_transfer"].dt.date <= PreviousMonth.date())]
    elif SelectedTime == "Tháng trước":
        LastMonth = ReferenceDate - pd.DateOffset(months=1)
        FilteredData = FilteredData[(FilteredData["date_transfer"].dt.month == LastMonth.month) & (FilteredData["date_transfer"].dt.year == LastMonth.year)]
        PreviousToLastMonth = LastMonth - pd.DateOffset(months=1)
        PreviousFilteredData = PreviousFilteredData[(PreviousFilteredData["date_transfer"].dt.month == PreviousToLastMonth.month) & (PreviousFilteredData["date_transfer"].dt.year == PreviousToLastMonth.year)]
    elif SelectedTime == "Quý":
        Quarter = (ReferenceDate.month - 1) // 3 + 1
        FilteredData = FilteredData[(FilteredData["date_transfer"].dt.quarter == Quarter) & (FilteredData["date_transfer"].dt.year == ReferenceDate.year)]
        PreviousQuarterDate = ReferenceDate - pd.DateOffset(months=3)
        PreviousQuarter = (PreviousQuarterDate.month - 1) // 3 + 1
        PreviousFilteredData = PreviousFilteredData[(PreviousFilteredData["date_transfer"].dt.quarter == PreviousQuarter) & 
                            (PreviousFilteredData["date_transfer"].dt.year == PreviousQuarterDate.year) &
                            (PreviousFilteredData["date_transfer"].dt.date <= PreviousQuarterDate.date())]
    elif SelectedTime == "Quý trước":
        LastQuarterDate = ReferenceDate - pd.DateOffset(months=3)
        LastQuarter = (LastQuarterDate.month - 1) // 3 + 1
        FilteredData = FilteredData[(FilteredData["date_transfer"].dt.quarter == LastQuarter) & (FilteredData["date_transfer"].dt.year == LastQuarterDate.year)]
        PrevToLastQuarterDate = LastQuarterDate - pd.DateOffset(months=3)
        PrevToLastQuarter = (PrevToLastQuarterDate.month - 1) // 3 + 1
        PreviousFilteredData = PreviousFilteredData[(PreviousFilteredData["date_transfer"].dt.quarter == PrevToLastQuarter) & (PreviousFilteredData["date_transfer"].dt.year == PrevToLastQuarterDate.year)]
    elif SelectedTime == "Năm":
        FilteredData = FilteredData[FilteredData["date_transfer"].dt.year == ReferenceDate.year]
        PreviousYear = ReferenceDate - pd.DateOffset(years=1)
        PreviousFilteredData = PreviousFilteredData[(PreviousFilteredData["date_transfer"].dt.year == PreviousYear.year) &
                            (PreviousFilteredData["date_transfer"].dt.date <= PreviousYear.date())]
    elif SelectedTime == "Năm trước":
        LastYear = ReferenceDate.year - 1
        FilteredData = FilteredData[FilteredData["date_transfer"].dt.year == LastYear]
        PrevToLastYear = ReferenceDate.year - 2
        PreviousFilteredData = PreviousFilteredData[PreviousFilteredData["date_transfer"].dt.year == PrevToLastYear]
    elif SelectedTime == "Tùy chỉnh":
        if DateRangeInput and len(DateRangeInput) == 2:
            Start, End = DateRangeInput
            FilteredData = FilteredData[(FilteredData["date_transfer"].dt.date >= Start) & (FilteredData["date_transfer"].dt.date <= End)]
            
            RangeDelta = End - Start + pd.Timedelta(days=1)
            PreviousStart = Start - RangeDelta
            PreviousEnd = Start - pd.Timedelta(days=1)
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

    # Targets logic
    if not SelectedRegion:
        RelevantTargets = TargetDataFrame
    else:
        RegionCodeMap = {"Miền Nam": "MN", "Miền Bắc": "MB", "Miền Trung": "MT"}
        SelectedRegionCodes = [RegionCodeMap.get(r) for r in SelectedRegion if r in RegionCodeMap]
        if SelectedRegionCodes and not TargetDataFrame.empty:
            RelevantTargets = TargetDataFrame[TargetDataFrame["sub_region"].str.startswith(tuple(SelectedRegionCodes), na=False)]
        else:
            RelevantTargets = TargetDataFrame

    TargetRevenue = RelevantTargets["target_revenue"].apply(pd.to_numeric, errors="coerce").sum() if not RelevantTargets.empty else 0
    CompletionRate = calc_target_completion(CurrentTotalRevenue, TargetRevenue)

    render_kpi_row([
        {"label": "Doanh số tổng", "value": f"{CurrentTotalRevenue:,.0f}", "delta": RevenueDelta},
        {"label": "Tổng số đơn", "value": f"{CurrentTotalOrders:,}", "delta": OrderDelta},
        {"label": "Tổng số lượng", "value": f"{CurrentTotalVolume:,}", "delta": VolumeDelta},
        {"label": "Giá trị đơn hàng", "value": f"{CurrentAvgOrderValue:,.0f}", "delta": AvgOrderDelta},
        {"label": "Hoàn thành mục tiêu", "value": f"{CompletionRate:.1f}%", "delta": f"Mục tiêu: {TargetRevenue:,.0f}"},
    ])

    # Export popover (rendered into title row placeholder)
    from services.export_excel import generate_dashboard_excel
    with ExportBtnContainer:
        with st.popover("Xuất dữ liệu"):
            # Cache export data per filter combination, generate on demand
            _export_key = f"{SelectedTime}_{SelectedRegion}_{SelectedBrand}_{ReferenceDate.date()}"
            if st.session_state.get("_export_key") != _export_key:
                st.session_state["_export_key"] = _export_key
                st.session_state.pop("_export_ppt", None)
                st.session_state.pop("_export_xlsx", None)

            if st.button("Tạo báo cáo PPT", use_container_width=True):
                with st.spinner("Đang tạo PowerPoint..."):
                    st.session_state["_export_ppt"] = generate_ppt_bytes(FilteredData, PreviousFilteredData, MainDataFrame, ReferenceDate)

            if "_export_ppt" in st.session_state:
                st.download_button("Tải PowerPoint", data=st.session_state["_export_ppt"],
                                   file_name="bao_cao_dealer_report.pptx",
                                   mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                                   use_container_width=True)

            if st.button("Tạo báo cáo Excel", use_container_width=True):
                with st.spinner("Đang tạo Excel..."):
                    st.session_state["_export_xlsx"] = generate_dashboard_excel(FilteredData, PreviousFilteredData, MainDataFrame, ReferenceDate)

            if "_export_xlsx" in st.session_state:
                st.download_button("Tải Excel", data=st.session_state["_export_xlsx"],
                                   file_name="bao_cao_tong_hop.xlsx",
                                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                   use_container_width=True)

            CsvDataContent = FilteredData.to_csv(index=False).encode("utf-8-sig")
            st.download_button("Tải CSV (Raw Data)", data=CsvDataContent, file_name="du_lieu_ban_hang.csv", mime="text/csv", use_container_width=True)

    st.divider()

    # --- TABS FOR MERGED VIEW ---
    tab_overview, tab_products, tab_dealers, tab_staff, tab_profit = st.tabs([
        "📊 Tổng quan", "📦 Phân tích Sản phẩm", "🏢 Đối tác", "👤 Nhân viên", "💰 Hiệu quả KD"
    ])

    with tab_overview:
        with st.container(border=True):
            st.subheader("Bảng tóm tắt")
            
            # --- 2026 TARGETS ---
            TARGETS = {
                "rev_daily": 79251000000, "rev_sieuthi": 9280000000,
                "bikes_daily": 35000, "bikes_sieuthi": 3000,
                "points_daily": 380, "points_sieuthi": 61
            }
            TARGETS["rev_total"] = TARGETS["rev_daily"] + TARGETS["rev_sieuthi"]
            TARGETS["bikes_total"] = TARGETS["bikes_daily"] + TARGETS["bikes_sieuthi"]
            TARGETS["points_total"] = TARGETS["points_daily"] + TARGETS["points_sieuthi"]

            # Calculate Revenue splits
            total_rev = FilteredData["sales_revenue"].sum()
            sieuthi_rev = FilteredData[FilteredData["region"] == "Siêu thị"]["sales_revenue"].sum()
            daily_rev = total_rev - sieuthi_rev
            
            # Calculate Bikes splits
            bikes_df = FilteredData[FilteredData["category"] == "BIKES"]
            total_bikes = int(bikes_df["sales_volume"].sum())
            sieuthi_bikes = int(bikes_df[bikes_df["region"] == "Siêu thị"]["sales_volume"].sum())
            daily_bikes = total_bikes - sieuthi_bikes

            # Calculate Selling Points splits
            total_dealers = FilteredData["dealer_id"].nunique()
            sieuthi_dealers = FilteredData[FilteredData["region"] == "Siêu thị"]["dealer_id"].nunique()
            daily_dealers = total_dealers - sieuthi_dealers

            def calc_comp(act, tgt):
                return (act / tgt * 100) if tgt > 0 else 0
            
            summary_df = pd.DataFrame([
                {"Chỉ tiêu": "1. Doanh số (VND)", "Thực tế": total_rev, "Mục tiêu 2026": TARGETS["rev_total"]},
                {"Chỉ tiêu": "   - Đại lý", "Thực tế": daily_rev, "Mục tiêu 2026": TARGETS["rev_daily"]},
                {"Chỉ tiêu": "   - Siêu thị", "Thực tế": sieuthi_rev, "Mục tiêu 2026": TARGETS["rev_sieuthi"]},
                {"Chỉ tiêu": "2. Số lượng xe (chiếc)", "Thực tế": total_bikes, "Mục tiêu 2026": TARGETS["bikes_total"]},
                {"Chỉ tiêu": "   - Đại lý", "Thực tế": daily_bikes, "Mục tiêu 2026": TARGETS["bikes_daily"]},
                {"Chỉ tiêu": "   - Siêu thị", "Thực tế": sieuthi_bikes, "Mục tiêu 2026": TARGETS["bikes_sieuthi"]},
                {"Chỉ tiêu": "3. Số lượng điểm bán (điểm)", "Thực tế": total_dealers, "Mục tiêu 2026": TARGETS["points_total"]},
                {"Chỉ tiêu": "   - Đại lý", "Thực tế": daily_dealers, "Mục tiêu 2026": TARGETS["points_daily"]},
                {"Chỉ tiêu": "   - Siêu thị", "Thực tế": sieuthi_dealers, "Mục tiêu 2026": TARGETS["points_sieuthi"]}
            ])
            
            summary_df["% Hoàn thành"] = summary_df.apply(lambda r: calc_comp(r["Thực tế"], r["Mục tiêu 2026"]), axis=1)
            
            # Reorder columns
            summary_df = summary_df[["Chỉ tiêu", "Mục tiêu 2026", "Thực tế", "% Hoàn thành"]]

            st.dataframe(
                summary_df.style.set_properties(**{'text-align': 'right'}),
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Thực tế": st.column_config.NumberColumn(format="%,d"),
                    "Mục tiêu 2026": st.column_config.NumberColumn(format="%,d"),
                    "% Hoàn thành": st.column_config.NumberColumn(format="%.1f%%")
                }
            )

        c1, c2 = st.columns(2)
        with c1:
            with st.container(border=True):
                st.subheader("Xu hướng doanh thu")
                
                # To calculate accurate MoM Growth, we need historical data before the time filter was applied
                # but with other filters (Region, Brand, etc.) intact.
                TrendBaseData = MainDataFrame.copy()
                if SelectedRegion: TrendBaseData = TrendBaseData[TrendBaseData["region"].isin(SelectedRegion)]
                if SelectedBrand: TrendBaseData = TrendBaseData[TrendBaseData["product_group"].isin(SelectedBrand)]
                if SelectedSalesperson: TrendBaseData = TrendBaseData[TrendBaseData["salesperson"].isin(SelectedSalesperson)]
                if SelectedChannel: TrendBaseData = TrendBaseData[TrendBaseData["channel_name"].isin(SelectedChannel)]
                
                TrendBaseData["sort_key"] = TrendBaseData["date_transfer"].dt.to_period("M").dt.to_timestamp()
                AllTrendStats = TrendBaseData.groupby("sort_key")["sales_revenue"].sum().reset_index().sort_values("sort_key")
                AllTrendStats["MoM Growth"] = (AllTrendStats["sales_revenue"].pct_change() * 100).replace([float('inf'), -float('inf')], 0).fillna(0)

                # Now get the trend for the filtered period for plotting/display
                MonthlyRevenueTrend = FilteredData.copy()
                MonthlyRevenueTrend["sort_key"] = MonthlyRevenueTrend["date_transfer"].dt.to_period("M").dt.to_timestamp()
                TrendStats = MonthlyRevenueTrend.groupby("sort_key")["sales_revenue"].sum().reset_index().sort_values("sort_key")
                
                # Merge the correct historical MoM Growth into the current display table
                TrendStats = TrendStats.merge(AllTrendStats[["sort_key", "MoM Growth"]], on="sort_key", how="left").fillna(0)
                TrendStats["month_year"] = TrendStats["sort_key"].dt.strftime("%m/%Y")
                
                st.plotly_chart(line_chart(TrendStats, "month_year", "sales_revenue", ""), use_container_width=True)
                
                # Render the data table
                TrendDisplay = TrendStats[["month_year", "sales_revenue", "MoM Growth"]].copy()
                TrendDisplay.columns = ["Tháng/Năm", "Doanh số (VND)", "Tăng trưởng MoM"]
                
                st.dataframe(
                    TrendDisplay.sort_values("Tháng/Năm", ascending=False).style.set_properties(**{'text-align': 'right'}), # Show newest first in table
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Doanh số (VND)": st.column_config.NumberColumn(format="%,d"),
                        "Tăng trưởng MoM": st.column_config.NumberColumn(format="%.1f%%")
                    }
                )
                
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
                
                def render_regional_pivot_html(c_data, p_data):
                    if c_data.empty:
                        st.info("Không có dữ liệu Vùng.")
                        return

                    # Group by Region for Parent Summary
                    parent_summary = c_data.groupby("region").agg(
                        revenue=("sales_revenue", "sum"),
                        volume=("sales_volume", "sum"),
                        dealers=("dealer_id", "nunique")
                    ).reset_index()

                    # Get Previous Parent Summary for Growth
                    prev_parent_summary = p_data.groupby("region").agg(
                        rev_prev=("sales_revenue", "sum"),
                        vol_prev=("sales_volume", "sum")
                    ).reset_index()

                    # Merge and calculate parent growth
                    parent_summary = parent_summary.merge(prev_parent_summary, on="region", how="left").fillna(0)
                    parent_summary["rev_growth"] = ((parent_summary["revenue"] - parent_summary["rev_prev"]) / parent_summary["rev_prev"] * 100).replace([float('inf'), -float('inf')], 0).fillna(0)
                    parent_summary["vol_growth"] = ((parent_summary["volume"] - parent_summary["vol_prev"]) / parent_summary["vol_prev"] * 100).replace([float('inf'), -float('inf')], 0).fillna(0)
                    
                    parent_summary = parent_summary.sort_values("revenue", ascending=False)

                    html_parts = []
                    html_parts.append('''
                    <style>
                    .piv-table { display: flex; flex-direction: column; width: 100%; font-family: "Source Sans Pro", sans-serif; font-size: 14px; }
                    .piv-row { display: flex; border-bottom: 1px solid #f0f2f6; align-items: center; padding: 12px 0; transition: background-color 0.2s; }
                    .piv-row:hover { background-color: #f8f9fa; }
                    
                    .piv-header { position: sticky; top: 0; background-color: white; z-index: 10; font-weight: 600; color: #6c757d; text-transform: uppercase; font-size: 11px; border-bottom: 2px solid #e6e6e6; padding: 8px 0; margin-top: 0; }
                    .piv-child-header { font-weight: 600; color: #888; font-size: 10px; background-color: #fafafa; border-bottom: 1px solid #eee; padding: 6px 0; }
                    
                    .cr-name { flex: 3.5; text-align: left; padding-left: 10px; font-weight: 600; color: #333; }
                    .cr-group { flex: 3.5; text-align: left; padding-left: 40px; color: #555; font-size: 13px; }
                    
                    .cr-rev { flex: 2.0; text-align: right; }
                    .cr-rg { flex: 0.8; text-align: right; }
                    .cr-vol { flex: 1.0; text-align: right; }
                    .cr-vg { flex: 0.8; text-align: right; }
                    .cr-dlr { flex: 0.8; text-align: right; }
                    .cr-tog { flex: 0.5; display: flex; justify-content: flex-end; padding-right: 10px; }

                    .tgl-btn { display: none; }
                    .tgl-lbl { cursor: pointer; border: 1px solid #ccc; border-radius: 4px; width: 22px; height: 22px; display: flex; align-items: center; justify-content: center; font-weight: bold; color: #555; background-color: white; transition: all 0.2s; margin-left: auto; }
                    .tgl-lbl:hover { border-color: #1f77b4; color: #1f77b4; }
                    .tgl-lbl::after { content: "＋"; }
                    .tgl-btn:checked ~ .piv-row .tgl-lbl::after { content: "−"; }

                    .piv-child-cont { display: none; flex-direction: column; background-color: #fafafa; border-bottom: 1px solid #f0f2f6; }
                    .tgl-btn:checked ~ .piv-child-cont { display: flex; }

                    .piv-child-row { display: flex; align-items: center; padding: 8px 0; border-top: 1px dashed #eee; }
                    
                    .gr-pos { color: #28a745; font-weight: 500; }
                    .gr-neg { color: #dc3545; font-weight: 500; }
                    
                    .scr-cont::-webkit-scrollbar { width: 6px; }
                    .scr-cont::-webkit-scrollbar-track { background: #f1f1f1; border-radius: 4px; }
                    .scr-cont::-webkit-scrollbar-thumb { background: #ccc; border-radius: 4px; }
                    </style>
                    <div class="scr-cont" style="max-height: 400px; overflow-y: auto; border: 1px solid #e6e6e6; border-radius: 4px;">
                        <div class="piv-table">
                            <div class="piv-row piv-header">
                                <div class="cr-name">Vùng (Region / Group)</div>
                                <div class="cr-rev">Doanh số</div>
                                <div class="cr-rg">∆ DS</div>
                                <div class="cr-vol">Số lượng</div>
                                <div class="cr-vg">∆ SL</div>
                                <div class="cr-dlr">Số ĐT</div>
                                <div class="cr-tog"></div>
                            </div>
                    ''')

                    for i, row in parent_summary.iterrows():
                        region = row['region']
                        row_key = f"reg_tgl_{i}"
                        
                        rg = row['rev_growth']
                        color_rg = "gr-pos" if rg >= 0 else "gr-neg"
                        sign_rg = "+" if rg > 0 else ""
                        
                        vg = row['vol_growth']
                        color_vg = "gr-pos" if vg >= 0 else "gr-neg"
                        sign_vg = "+" if vg > 0 else ""

                        html_parts.append(f'''
                        <div>
                            <input type="checkbox" id="{row_key}" class="tgl-btn">
                            <div class="piv-row">
                                <div class="cr-name">{region}</div>
                                <div class="c-rev" style="font-weight: 500;">{row['revenue']:,.0f}</div>
                                <div class="cr-rg {color_rg}">{sign_rg}{rg:.1f}%</div>
                                <div class="cr-vol" style="font-weight: 500;">{row['volume']:,}</div>
                                <div class="cr-vg {color_vg}">{sign_vg}{vg:.1f}%</div>
                                <div class="cr-dlr">{row['dealers']:,}</div>
                                <div class="cr-tog">
                                    <label for="{row_key}" class="tgl-lbl"></label>
                                </div>
                            </div>
                            <div class="piv-child-cont">
                                <div class="piv-row piv-child-header">
                                    <div class="cr-group">Nhóm Vùng (Region Group)</div>
                                    <div class="cr-rev">Doanh số</div>
                                    <div class="cr-rg">∆ DS</div>
                                    <div class="cr-vol">Số lượng</div>
                                    <div class="cr-vg">∆ SL</div>
                                    <div class="cr-dlr">Số ĐT</div>
                                    <div class="cr-tog"></div>
                                </div>
                        ''')

                        # --- CHILD ROWS: Region Groups ---
                        child_data = c_data[c_data["region"] == region].copy()
                        child_stats = child_data.groupby("region_group").agg(
                            revenue=("sales_revenue", "sum"),
                            volume=("sales_volume", "sum"),
                            dealers=("dealer_id", "nunique")
                        ).reset_index()

                        prev_child_data = p_data[p_data["region"] == region]
                        prev_child_stats = prev_child_data.groupby("region_group").agg(
                            rev_prev=("sales_revenue", "sum"),
                            vol_prev=("sales_volume", "sum")
                        ).reset_index()

                        merged_child = child_stats.merge(prev_child_stats, on="region_group", how="left").fillna(0)
                        merged_child["rev_growth"] = ((merged_child["revenue"] - merged_child["rev_prev"]) / merged_child["rev_prev"] * 100).replace([float('inf'), -float('inf')], 0).fillna(0)
                        merged_child["vol_growth"] = ((merged_child["volume"] - merged_child["vol_prev"]) / merged_child["vol_prev"] * 100).replace([float('inf'), -float('inf')], 0).fillna(0)
                        merged_child = merged_child.sort_values("region_group", ascending=True)

                        for _, c_row in merged_child.iterrows():
                            crg = c_row['rev_growth']
                            color_crg = "gr-pos" if crg >= 0 else "gr-neg"
                            sign_crg = "+" if crg > 0 else ""
                            
                            cvg = c_row['vol_growth']
                            color_cvg = "gr-pos" if cvg >= 0 else "gr-neg"
                            sign_cvg = "+" if cvg > 0 else ""

                            html_parts.append(f'''
                                <div class="piv-child-row">
                                    <div class="cr-group">{c_row['region_group']}</div>
                                    <div class="cr-rev">{c_row['revenue']:,.0f}</div>
                                    <div class="cr-rg {color_crg}">{sign_crg}{crg:.1f}%</div>
                                    <div class="cr-vol">{c_row['volume']:,}</div>
                                    <div class="cr-vg {color_cvg}">{sign_cvg}{cvg:.1f}%</div>
                                    <div class="cr-dlr">{c_row['dealers']:,}</div>
                                    <div class="cr-tog"></div>
                                </div>
                            ''')
                        
                        html_parts.append('''
                            </div>
                        </div>
                        ''')

                    html_parts.append('</div>')
                    html_parts.append('</div>')
                    
                    final_html = "\n".join([line.strip() for line in "".join(html_parts).split("\n")])
                    st.markdown(final_html, unsafe_allow_html=True)

                # Call the regional pivot function
                render_regional_pivot_html(FilteredData, PreviousFilteredData)

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
                BrandComparisonData["Tăng trưởng"] = BrandComparisonData["growth"]

                st.plotly_chart(bar_chart(BrandCurrentStats.sort_values("revenue", ascending=False), "product_group", "revenue", ""), use_container_width=True)
                
                BrandDisplayTable = BrandComparisonData.sort_values("revenue", ascending=False)
                BrandDisplayTable = BrandDisplayTable[["product_group", "revenue", "volume", "Tăng trưởng"]]
                BrandDisplayTable.columns = ["Nhóm sản phẩm", "Doanh số (VND)", "Số lượng", "Tăng trưởng"]
                st.dataframe(
                    BrandDisplayTable.style.set_properties(**{'text-align': 'right'}), 
                    use_container_width=True, 
                    hide_index=True,
                    column_config={
                        "Doanh số (VND)": st.column_config.NumberColumn(format="%,d"),
                        "Số lượng": st.column_config.NumberColumn(format="%,d"),
                        "Tăng trưởng": st.column_config.NumberColumn(format="%+.1f%%")
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
                CategoryComparisonData["Tăng trưởng"] = CategoryComparisonData["growth"]

                st.plotly_chart(bar_chart(CategoryCurrentStats, "category", "revenue", ""), use_container_width=True)
                
                CategoryDisplayTable = CategoryComparisonData[["category", "revenue", "volume", "Tăng trưởng"]].copy()
                CategoryDisplayTable.columns = ["Danh mục", "Doanh số (VND)", "Số lượng", "Tăng trưởng"]
                st.dataframe(
                    CategoryDisplayTable.sort_values("Doanh số (VND)", ascending=False).style.set_properties(**{'text-align': 'right'}), 
                    use_container_width=True, 
                    hide_index=True,
                    column_config={
                        "Doanh số (VND)": st.column_config.NumberColumn(format="%,d"),
                        "Số lượng": st.column_config.NumberColumn(format="%,d"),
                        "Tăng trưởng": st.column_config.NumberColumn(format="%+.1f%%")
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
                            <div class="c-rev" style="font-weight: 500;">{row['revenue']:,.0f}</div>                            <div class="c-rg {color_rg}">{sign_rg}{rg:.1f}%</div>
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
                                <div class="cr-rev">{c_row['revenue']:,.0f}</div>
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
            st.markdown("**Bảng tổng hợp Phụ kiện (GEARS)**")
            
            gears_data = FilteredData[FilteredData["category"] == "GEARS"].copy()
            prev_gears_data = PreviousFilteredData[PreviousFilteredData["category"] == "GEARS"].copy()
            
            if gears_data.empty:
                st.info("Không có dữ liệu Phụ kiện.")
            else:
                gears_summary = gears_data.groupby(["item_id", "item_name", "brand"]).agg(
                    revenue=("sales_revenue", "sum"),
                    volume=("sales_volume", "sum")
                ).reset_index()

                prev_gears_summary = prev_gears_data.groupby(["item_id", "item_name", "brand"]).agg(
                    rev_prev=("sales_revenue", "sum"),
                    vol_prev=("sales_volume", "sum")
                ).reset_index()

                gears_summary = gears_summary.merge(prev_gears_summary, on=["item_id", "item_name", "brand"], how="left").fillna(0)
                gears_summary["rev_growth"] = ((gears_summary["revenue"] - gears_summary["rev_prev"]) / gears_summary["rev_prev"] * 100).replace([float('inf'), -float('inf')], 0).fillna(0)
                gears_summary["vol_growth"] = ((gears_summary["volume"] - gears_summary["vol_prev"]) / gears_summary["vol_prev"] * 100).replace([float('inf'), -float('inf')], 0).fillna(0)
                
                gears_summary = gears_summary.sort_values("volume", ascending=False)
                
                gears_display = gears_summary[["item_id", "item_name", "brand", "revenue", "rev_growth", "volume", "vol_growth"]].copy()
                gears_display.columns = ["Mã SKU", "Tên sản phẩm", "Thương hiệu", "Doanh số (VND)", "∆ DS", "Số lượng", "∆ SL"]
                
                st.dataframe(
                    gears_display.style.set_properties(**{'text-align': 'right'}), 
                    use_container_width=True,
                    hide_index=True,
                    height=400,
                    column_config={
                        "Doanh số (VND)": st.column_config.NumberColumn(format="%,d"),
                        "Số lượng": st.column_config.NumberColumn(format="%,d"),
                        "∆ DS": st.column_config.NumberColumn(format="%+.1f%%"),
                        "∆ SL": st.column_config.NumberColumn(format="%+.1f%%")
                    }
                )

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
            TopDealerData["Tăng trưởng"] = TopDealerData["growth"]
            TopDealerData["Hạng"] = range(1, len(TopDealerData) + 1)

            TopDealerDisplayTable = TopDealerData[["Hạng", "dealer_name", "province", "revenue", "volume", "Tăng trưởng"]].copy()
            TopDealerDisplayTable.columns = ["Hạng", "Tên đối tác", "Tỉnh", "Doanh số (VND)", "Số lượng", "Tăng trưởng"]
            with st.expander("Xem bảng Top Đối tác chi tiết", expanded=False):
                st.dataframe(
                    TopDealerDisplayTable.style.set_properties(**{'text-align': 'right'}), 
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Doanh số (VND)": st.column_config.NumberColumn(format="%,d"),
                        "Số lượng": st.column_config.NumberColumn(format="%,d"),
                        "Tăng trưởng": st.column_config.NumberColumn(format="%+.1f%%")
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
            StaffComparisonData["Tăng trưởng"] = StaffComparisonData["growth"]

            st.plotly_chart(horizontal_bar_chart(StaffCurrentStats.sort_values("revenue", ascending=True), "revenue", "salesperson", ""), use_container_width=True)
            
            StaffDisplayTable = StaffComparisonData.sort_values("revenue", ascending=False)
            StaffDisplayTable = StaffDisplayTable[["salesperson", "revenue", "volume", "dealers", "Tăng trưởng"]]
            StaffDisplayTable.columns = ["Nhân viên", "Doanh số (VND)", "Số lượng", "Số đối tác", "Tăng trưởng"]
            st.dataframe(
                StaffDisplayTable.style.set_properties(**{'text-align': 'right'}), 
                use_container_width=True, 
                hide_index=True,
                column_config={
                    "Doanh số (VND)": st.column_config.NumberColumn(format="%,d"),
                    "Số lượng": st.column_config.NumberColumn(format="%,d"),
                    "Số đối tác": st.column_config.NumberColumn(format="%,d"),
                    "Tăng trưởng": st.column_config.NumberColumn(format="%+.1f%%")
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
                c2.metric("Lợi nhuận gộp", f"{profit:,.0f}")
                c3.metric("Tổng doanh thu", f"{FilteredData['sales_revenue'].sum():,.0f}")
                c4.metric("Tổng chi phí", f"{FilteredData['cost_of_goods'].sum():,.0f}")

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
                        display_df.style.set_properties(**{'text-align': 'right'}), 
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "Doanh thu": st.column_config.NumberColumn(format="%,d"),
                            "Chi phí": st.column_config.NumberColumn(format="%,d"),
                            "Lợi nhuận": st.column_config.NumberColumn(format="%,d"),
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
            RawTransactionLog.reset_index(drop=True).style.set_properties(**{'text-align': 'right'}), 
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
