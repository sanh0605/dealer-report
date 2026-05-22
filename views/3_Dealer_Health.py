import streamlit as st
import pandas as pd
from database.session import get_db
from database.models import AccountsReceivableLedger, DealerMaster, SaleRecord
from services.analytics import calc_dealer_health_stats, calc_ar_aging
from components.kpi_cards import render_kpi_row
from components.charts import pie_chart, bar_chart, scatter_chart, histogram_chart
from components.ui_utils import show_centered_loader

# Display centered loading animation during initial render
PageLoader = show_centered_loader()

try:
    st.title("Sức khỏe Đối tác")

    with st.expander("ℹ️ Tiêu chí phân loại Sức khỏe Đối tác"):
        st.markdown("""
        Hệ thống tự động phân loại đối tác dựa trên 3 tiêu chí chính: **Hoạt động**, **Tuổi nợ** và **Hiệu suất thanh toán**.
        
        *   🟢 **Tốt (Good):** 
            *   Có phát sinh đơn hàng trong vòng 90 ngày gần nhất.
            *   Không có nợ quá hạn (> 50,000đ) quá 30 ngày.
            *   Tỉ lệ thu hồi đạt trên 90%.
        *   🟡 **Cảnh báo (Warning):**
            *   Có phát sinh đơn hàng trong vòng 90 ngày gần nhất.
            *   Có nợ quá hạn từ 30 - 60 ngày **HOẶC** tỉ lệ thu hồi từ 70% - 90%.
        *   🔴 **Nguy hiểm (Critical):**
            *   Có nợ quá hạn trên 60 ngày.
            *   **HOẶC** Tỉ lệ thu hồi dưới 70%.
            *   **HOẶC** Không phát sinh đơn hàng trong vòng 90 ngày (Ngừng hoạt động).
        
        *Lưu ý: Các khoản nợ nhỏ dưới 50,000đ được coi là đã thanh toán xong và không tính vào tuổi nợ.*
        """)

    DatabaseSession = get_db()
    try:
        ArRows = DatabaseSession.query(AccountsReceivableLedger).all()
        DealerRows = DatabaseSession.query(DealerMaster).all()
        SaleRows = DatabaseSession.query(SaleRecord).all()
    finally:
        DatabaseSession.close()

    if not ArRows and not SaleRows:
        st.info("Không tìm thấy dữ liệu. Hãy tải dữ liệu lên trước.")
        st.stop()

    ArDataFrame = pd.DataFrame([r.__dict__ for r in ArRows]).drop(columns=["_sa_instance_state"], errors="ignore")
    DealerDataFrame = pd.DataFrame([r.__dict__ for r in DealerRows]).drop(columns=["_sa_instance_state"], errors="ignore")
    SaleDataFrame = pd.DataFrame([r.__dict__ for r in SaleRows]).drop(columns=["_sa_instance_state"], errors="ignore")

    # Pre-process dates
    if not SaleDataFrame.empty:
        SaleDataFrame["date_transfer"] = pd.to_datetime(SaleDataFrame["date_transfer"], format="mixed", errors="coerce")
    if not ArDataFrame.empty:
        ArDataFrame["due_date"] = pd.to_datetime(ArDataFrame["due_date"], dayfirst=True, errors="coerce")
        for Col in ["total_order_value", "paid_amount", "refund_amount", "deduction_amount"]:
            ArDataFrame[Col] = pd.to_numeric(ArDataFrame[Col], errors="coerce").fillna(0)

    # Sidebar filters
    st.sidebar.header("Bộ lọc")
    
    StatusOptions = ["Tất cả", "Tốt", "Cảnh báo", "Nguy hiểm"]
    SelectedStatus = st.sidebar.selectbox("Trạng thái Sức khỏe", StatusOptions)
    
    RegionOptions = ["Tất cả", "Miền Nam", "Miền Bắc", "Miền Trung"]
    SelectedRegion = st.sidebar.selectbox("Vùng miền", RegionOptions)
    
    AgingOptions = ["Tất cả", "<30", "30-60", ">60"]
    SelectedAging = st.sidebar.selectbox("Tuổi nợ (Ngày)", AgingOptions)

    # Calculate global stats for cards (unfiltered by status/aging, but maybe by region)
    # Actually, spec says overview cards for all.
    Stats = calc_dealer_health_stats(ArDataFrame, DealerDataFrame, SaleDataFrame)
    HealthDataFrame = Stats["health_df"]
    
    # Merge with DealerMaster for region if not already there
    if not DealerDataFrame.empty:
        # calc_dealer_health_stats already merges dealer_id and dealer_name
        # We need region and province for filtering and tables
        HealthDataFrame = HealthDataFrame.merge(
            DealerDataFrame[["dealer_id", "region", "province"]], 
            on="dealer_id", 
            how="left"
        )

    # Apply Region Filter
    if SelectedRegion != "Tất cả":
        HealthDataFrame = HealthDataFrame[HealthDataFrame["region"] == SelectedRegion]
        # Re-calculate stats for the filtered region
        Stats = {
            "total_dealers": len(HealthDataFrame),
            "healthy_dealers": len(HealthDataFrame[HealthDataFrame["status"] == "Tốt"]),
            "at_risk_dealers": len(HealthDataFrame[HealthDataFrame["status"].isin(["Cảnh báo", "Nguy hiểm"])]),
            "new_dealers": int(HealthDataFrame["is_new"].sum()),
            "inactive_dealers": int((~HealthDataFrame["is_active"]).sum()),
            "counts": HealthDataFrame["status"].value_counts().to_dict(),
            "health_df": HealthDataFrame
        }

    # Render KPI Cards
    render_kpi_row([
        {"label": "Tổng đối tác", "value": f"{Stats['total_dealers']:,}"},
        {"label": "Đối tác tốt", "value": f"{Stats['healthy_dealers']:,}"},
        {"label": "Đối tác rủi ro", "value": f"{Stats['at_risk_dealers']:,}"},
        {"label": "Đối tác mới", "value": f"{Stats['new_dealers']:,}"},
        {"label": "Đối tác không hoạt động", "value": f"{Stats['inactive_dealers']:,}"},
    ])

    st.divider()

    # Apply Status and Aging filters for the rest of the dashboard
    FilteredHealth = HealthDataFrame.copy()
    if SelectedStatus != "Tất cả":
        FilteredHealth = FilteredHealth[FilteredHealth["status"] == SelectedStatus]
    
    if SelectedAging != "Tất cả":
        if SelectedAging == "<30":
            FilteredHealth = FilteredHealth[FilteredHealth["days_overdue"] < 30]
        elif SelectedAging == "30-60":
            FilteredHealth = FilteredHealth[(FilteredHealth["days_overdue"] >= 30) & (FilteredHealth["days_overdue"] <= 60)]
        elif SelectedAging == ">60":
            FilteredHealth = FilteredHealth[FilteredHealth["days_overdue"] > 60]

    # Charts Row 1
    Col1, Col2 = st.columns(2)
    
    # Donut chart: Health distribution
    HealthCounts = pd.DataFrame([
        {"Trạng thái": k, "Số lượng": v} for k, v in Stats["counts"].items()
    ])
    Col1.plotly_chart(
        pie_chart(HealthCounts, "Trạng thái", "Số lượng", "Phân phối sức khỏe"),
        use_container_width=True
    )
    
    # AR Aging by Dealer (using all filtered data or top dealers?)
    # Spec says "Công nợ theo đối tác" - Stacked bar chart
    # We'll use the buckets for the whole filtered group
    AgingBuckets = calc_ar_aging(ArDataFrame[ArDataFrame["dealer_id"].isin(FilteredHealth["dealer_id"])])
    AgingData = pd.DataFrame([{"Tuổi nợ": k, "Số tiền": v} for k, v in AgingBuckets.items()])
    Col2.plotly_chart(
        bar_chart(AgingData, "Tuổi nợ", "Số tiền", "Cơ cấu tuổi nợ (Công nợ tổng)"),
        use_container_width=True
    )

    # Charts Row 2 removed as requested

    st.divider()

    # Detailed Tables
    Tab1, Tab2, Tab3 = st.tabs(["Tóm tắt Sức khỏe", "Cảnh báo Rủi ro", "Đối tác Mới"])
    
    with Tab1:
        # Dealer | Province | Health Status | Revenue | AR Days | Payment Score
        # Revenue needs to be joined from sales
        SummaryTable = FilteredHealth.copy()
        if not SaleDataFrame.empty:
            DealerRevenue = SaleDataFrame.groupby("dealer_id")["sales_revenue"].sum().reset_index()
            SummaryTable = SummaryTable.merge(DealerRevenue, on="dealer_id", how="left")
            SummaryTable["sales_revenue"] = SummaryTable["sales_revenue"].fillna(0)
        else:
            SummaryTable["sales_revenue"] = 0
            
        with st.expander("Xem bảng chi tiết", expanded=False):
            st.dataframe(
                SummaryTable[["dealer_name", "province", "status", "sales_revenue", "days_overdue", "payment_score"]],
                use_container_width=True,
                column_config={
                    "dealer_name": "Đối tác",
                    "province": "Tỉnh",
                    "status": "Trạng thái",
                    "sales_revenue": st.column_config.NumberColumn("Doanh số", format="%,d"),
                    "days_overdue": st.column_config.NumberColumn("Tuổi nợ (Ngày)", format="%d"),
                    "payment_score": st.column_config.NumberColumn("Tỉ lệ thu hồi (%)", format="%.1f%%")
                }
            )
        
    with Tab2:
        # Dealer | Province | Risk Level | AR Amount | Days Overdue
        RiskTable = FilteredHealth[FilteredHealth["status"].isin(["Cảnh báo", "Nguy hiểm"])].copy()
        with st.expander("Xem bảng chi tiết", expanded=False):
            st.dataframe(
                RiskTable[["dealer_name", "province", "status", "outstanding", "days_overdue"]],
                use_container_width=True,
                column_config={
                    "dealer_name": "Đối tác",
                    "province": "Tỉnh",
                    "status": "Mức độ rủi ro",
                    "outstanding": st.column_config.NumberColumn("Công nợ", format="%,d"),
                    "days_overdue": st.column_config.NumberColumn("Quá hạn (Ngày)", format="%d")
                }
            )
        
    with Tab3:
        # Dealer | Province | Start Date | First Order | Revenue
        NewTable = FilteredHealth[FilteredHealth["is_new"]].copy()
        if not SaleDataFrame.empty:
            # First order ID
            FirstOrders = SaleDataFrame.sort_values("date_transfer").groupby("dealer_id").first().reset_index()
            NewTable = NewTable.merge(FirstOrders[["dealer_id", "order_id", "sales_revenue"]], on="dealer_id", how="left", suffixes=("", "_first"))
        
        with st.expander("Xem bảng chi tiết", expanded=False):
            st.dataframe(
                NewTable[["dealer_name", "province", "first_sale_date", "order_id", "outstanding"]],
                use_container_width=True,
                column_config={
                    "dealer_name": "Đối tác",
                    "province": "Tỉnh",
                    "first_sale_date": "Ngày bắt đầu",
                    "order_id": "Đơn hàng đầu tiên",
                    "outstanding": st.column_config.NumberColumn("Công nợ hiện tại", format="%,d")
                }
            )

finally:
    # Ensure the loader is always hidden even on error
    PageLoader.empty()
