import streamlit as st
import pandas as pd
from database.session import get_db
from database.models import SaleRecord, DealerMaster, ProductMaster, SalesTarget
from services.analytics import calc_total_revenue, calc_gross_profit, calc_target_completion
from components.kpi_cards import render_kpi_row
from components.charts import bar_chart, pie_chart, line_chart

st.set_page_config(page_title="Sales & Revenue Dashboard", layout="wide")

if "user" not in st.session_state:
    st.error("Vui long dang nhap tu trang chu.")
    st.stop()

user = st.session_state["user"]
st.title("💰 Doanh so & Doanh thu")

db = get_db()
try:
    sales_rows = db.query(SaleRecord).all()
    dealer_rows = db.query(DealerMaster).all()
    product_rows = db.query(ProductMaster).all()
    target_rows = db.query(SalesTarget).all()
finally:
    db.close()

if not sales_rows:
    st.info("Khong co du lieu ban hang. Vui long tai du lieu len qua trang Upload.")
    st.stop()

df = pd.DataFrame([r.__dict__ for r in sales_rows]).drop(columns=["_sa_instance_state"], errors="ignore")
df["date_transfer"] = pd.to_datetime(df["date_transfer"], dayfirst=True, errors="coerce")
df["month"] = df["date_transfer"].dt.to_period("M").astype(str)
df["month_year"] = df["date_transfer"].dt.strftime("%m/%Y")
df[["sales_revenue", "cost_of_goods", "sales_volume", "total_price_standard"]] = (
    df[["sales_revenue", "cost_of_goods", "sales_volume", "total_price_standard"]].apply(pd.to_numeric, errors="coerce")
)

# Join with dealer_master to get region
if dealer_rows:
    dealer_df = pd.DataFrame([r.__dict__ for r in dealer_rows]).drop(columns=["_sa_instance_state"], errors="ignore")
    df = df.merge(dealer_df[["dealer_id", "region", "province"]], on="dealer_id", how="left")
else:
    df["region"] = ""
    df["province"] = ""

# Join with product_master to get brand_group
if product_rows:
    product_df = pd.DataFrame([r.__dict__ for r in product_rows]).drop(columns=["_sa_instance_state"], errors="ignore")
    df = df.merge(product_df[["item_id", "brand_group", "brand", "category"]], on="item_id", how="left")
else:
    df["brand_group"] = ""
    df["brand"] = ""
    df["category"] = ""

# Sidebar filters
st.sidebar.header("Bo loc")

# Time period filter
time_options = {
    "Hom nay": "D",
    "Tuan nay": "W",
    "Thang nay": "M",
    "Thang truoc": "LM",
    "Quy": "Q",
    "Nam": "Y",
    "Tuy chinh": "Custom"
}
sel_time = st.sidebar.selectbox("Khoang thoi gian", list(time_options.keys()))

# Region filter
regions = ["Tat ca"] + sorted(df["region"].dropna().unique().tolist())
sel_region = st.sidebar.selectbox("Vung mien", regions)

# Brand Group filter
brand_groups = ["Tat Ca"] + sorted(df["brand_group"].dropna().unique().tolist())
sel_brand = st.sidebar.selectbox("Nhom thuong hieu", brand_groups)

# Salesperson filter
salespeople = ["Tat Ca"] + sorted(df["salesperson"].dropna().unique().tolist())
sel_salesperson = st.sidebar.selectbox("Nhan vien ban hang", salespeople)

# Channel filter
channels = ["Tat Ca"] + sorted(df["channel_name"].dropna().unique().tolist())
sel_channel = st.sidebar.selectbox("Kenh", channels)

# Apply time filter
today = pd.Timestamp.now()
fdf = df.copy()

if sel_time == "Hom nay":
    fdf = fdf[fdf["date_transfer"].dt.date == today.date()]
elif sel_time == "Tuan nay":
    week_start = today - pd.Timedelta(days=today.weekday())
    fdf = fdf[fdf["date_transfer"] >= week_start]
elif sel_time == "Thang nay":
    fdf = fdf[(fdf["date_transfer"].dt.month == today.month) & (fdf["date_transfer"].dt.year == today.year)]
elif sel_time == "Thang truoc":
    last_month = today - pd.DateOffset(months=1)
    fdf = fdf[(fdf["date_transfer"].dt.month == last_month.month) & (fdf["date_transfer"].dt.year == last_month.year)]
elif sel_time == "Quy":
    quarter = (today.month - 1) // 3 + 1
    fdf = fdf[(fdf["date_transfer"].dt.quarter == quarter) & (fdf["date_transfer"].dt.year == today.year)]
elif sel_time == "Nam":
    fdf = fdf[fdf["date_transfer"].dt.year == today.year]
elif sel_time == "Tuy chinh":
    date_range = st.sidebar.date_input("Chon khoang thoi gian", [today - pd.Timedelta(days=30), today])
    if len(date_range) == 2:
        fdf = fdf[(fdf["date_transfer"].dt.date >= date_range[0]) & (fdf["date_transfer"].dt.date <= date_range[1])]

# Apply other filters
if sel_region != "Tat Ca":
    fdf = fdf[fdf["region"] == sel_region]
if sel_brand != "Tat Ca":
    fdf = fdf[fdf["brand_group"] == sel_brand]
if sel_salesperson != "Tat Ca":
    fdf = fdf[fdf["salesperson"] == sel_salesperson]
if sel_channel != "Tat Ca":
    fdf = fdf[fdf["channel_name"] == sel_channel]

if fdf.empty:
    st.warning("Khong co du lieu phu hop voi bo loc da chon.")
    st.stop()

# Calculate KPIs
total_rev = calc_total_revenue(fdf)
profit, margin = calc_gross_profit(fdf)
total_vol = int(fdf["sales_volume"].sum())

# Calculate growth rate (compare with previous period)
prev_fdf = df[df["date_transfer"] < fdf["date_transfer"].min()]
if not prev_fdf.empty:
    prev_rev = calc_total_revenue(prev_fdf)
    growth_rate = ((total_rev - prev_rev) / prev_rev * 100) if prev_rev > 0 else 0.0
    growth_delta = f"{growth_rate:+.1f}%"
    growth_color = "normal" if growth_rate >= 0 else "inverse"
else:
    growth_rate = 0.0
    growth_delta = "N/A"
    growth_color = "normal"

# Calculate AR ratio (outstanding / revenue)
# This is a simplified calculation - in production, you'd need AR data
ar_ratio = 0.0
ar_delta = "N/A"

# Calculate average order value
total_orders = fdf["order_id"].nunique()
avg_order_value = total_rev / total_orders if total_orders > 0 else 0.0

# Calculate target completion
target_rev = sum(t.target_revenue or 0 for t in target_rows)
completion = calc_target_completion(total_rev, target_rev)

# Render KPI cards
render_kpi_row([
    {"label": "Doanh thu tong", "value": f"{total_rev:,.0f} VND"},
    {"label": "Tong so luong", "value": f"{total_vol:,} don vi"},
    {"label": "Toc do tang truong", "value": f"{growth_rate:.1f}%", "delta": growth_delta, "delta_color": growth_color},
    {"label": "Ty le cong no", "value": f"{ar_ratio:.1f}%", "delta": ar_delta},
    {"label": "Gia tri don hang TB", "value": f"{avg_order_value:,.0f} VND"},
])

st.divider()

# Charts section
col1, col2 = st.columns(2)

# Revenue trend by month
by_month = fdf.groupby("month_year")["sales_revenue"].sum().reset_index().sort_values("month_year")
col1.plotly_chart(
    line_chart(by_month, "month_year", "sales_revenue", "Xu huong doanh thu"),
    use_container_width=True
)

# Regional breakdown
by_region = fdf.groupby("region")["sales_revenue"].sum().reset_index().sort_values("sales_revenue", ascending=False)
col2.plotly_chart(
    bar_chart(by_region, "region", "sales_revenue", "Phan vung kinh doanh"),
    use_container_width=True
)

col3, col4 = st.columns(2)

# Brand performance pie chart
by_brand = fdf.groupby("brand_group")["sales_revenue"].sum().reset_index().sort_values("sales_revenue", ascending=False)
col3.plotly_chart(
    pie_chart(by_brand, "brand_group", "sales_revenue", "Hieu suat thuong hieu"),
    use_container_width=True
)

# Salesperson performance
by_salesperson = fdf.groupby("salesperson").agg(
    revenue=("sales_revenue", "sum"),
    volume=("sales_volume", "sum"),
    dealers=("dealer_id", "nunique")
).reset_index().sort_values("revenue", ascending=False)

col4.plotly_chart(
    bar_chart(by_salesperson, "salesperson", "revenue", "Hieu suat nhan vien ban hang"),
    use_container_width=True
)

st.divider()

# Top 10 dealers
by_dealer = fdf.groupby(["dealer_id", "dealer_name"]).agg(
    revenue=("sales_revenue", "sum"),
    volume=("sales_volume", "sum"),
    province=("province", "first")
).reset_index().sort_values("revenue", ascending=False).head(10)

st.subheader("Top 10 Doi tac theo Doanh thu")
by_dealer_display = by_dealer[["dealer_name", "province", "revenue", "volume"]].copy()
by_dealer_display.columns = ["Ten doi tac", "Tinh", "Doanh thu (VND)", "So luong"]
st.dataframe(by_dealer_display, use_container_width=True)

# Detailed tables
st.divider()

col5, col6 = st.columns(2)

# Regional performance table
with col5:
    st.subheader("Hieu suat theo Vung")
    regional_perf = fdf.groupby("region").agg(
        revenue=("sales_revenue", "sum"),
        volume=("sales_volume", "sum"),
        dealers=("dealer_id", "nunique")
    ).reset_index()
    regional_perf.columns = ["Vung", "Doanh thu (VND)", "So luong", "So doi tac"]
    st.dataframe(regional_perf, use_container_width=True)

# Salesperson performance table
with col6:
    st.subheader("Hieu suat Nhan vien")
    salesperson_perf = fdf.groupby("salesperson").agg(
        revenue=("sales_revenue", "sum"),
        volume=("sales_volume", "sum"),
        dealers=("dealer_id", "nunique")
    ).reset_index().sort_values("revenue", ascending=False)
    salesperson_perf.columns = ["Nhan vien", "Doanh thu (VND)", "So luong", "So doi tac"]
    st.dataframe(salesperson_perf, use_container_width=True)

# Raw data table (expandable)
with st.expander("Xem du lieu goc"):
    raw_cols = ["order_id", "date_transfer", "dealer_id", "dealer_name", "salesperson",
                "channel_name", "brand_group", "sales_volume", "sales_revenue"]
    raw_data = fdf[raw_cols].copy()
    raw_data.columns = ["Ma don hang", "Ngay chuyen", "Ma doi tac", "Ten doi tac",
                      "Nhan vien", "Kenh", "Nhom thuong hieu", "So luong", "Doanh thu"]
    st.dataframe(raw_data.reset_index(drop=True), use_container_width=True)

# Add refresh button
if st.button("Cap nhat du lieu"):
    st.rerun()

st.caption(f"Du lieu cap nhat luc: {pd.Timestamp.now().strftime('%d/%m/%Y %H:%M:%S')}")
