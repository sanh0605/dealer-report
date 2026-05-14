import streamlit as st
import pandas as pd
from database.session import get_db
from database.models import SaleRecord, ProductMaster
from services.analytics import calc_gross_profit
from components.charts import bar_chart, pie_chart

st.set_page_config(page_title="Hiệu quả Kinh doanh", layout="wide")
if "user" not in st.session_state:
    st.error("Vui lòng đăng nhập từ trang chủ.")
    st.stop()

user = st.session_state["user"]
if user["role"] not in ["Admin", "Manager"]:
    st.error("Chỉ Admin và Manager mới có quyền truy cập trang này.")
    st.stop()

st.title("💹 Hiệu quả Kinh doanh")

db = get_db()
try:
    sale_rows    = db.query(SaleRecord).all()
    product_rows = db.query(ProductMaster).all()
finally:
    db.close()

if not sale_rows:
    st.info("Không tìm thấy dữ liệu bán hàng.")
    st.stop()

sale_df = pd.DataFrame([r.__dict__ for r in sale_rows]).drop(columns=["_sa_instance_state"], errors="ignore")
prod_df = pd.DataFrame([r.__dict__ for r in product_rows]).drop(columns=["_sa_instance_state"], errors="ignore")

for col in ["sales_revenue","cost_of_goods","sales_volume"]:
    sale_df[col] = pd.to_numeric(sale_df[col], errors="coerce").fillna(0)

if not prod_df.empty and "category" in prod_df.columns:
    merged = sale_df.merge(prod_df[["item_id","category","brand"]], on="item_id", how="left")
else:
    merged = sale_df

profit, margin = calc_gross_profit(merged)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Biên lợi nhuận gộp", f"{margin:.1f}%")
c2.metric("Lợi nhuận ròng", f"฿{profit:,.0f}")
c3.metric("Tổng doanh thu", f"฿{merged['sales_revenue'].sum():,.0f}")
c4.metric("Tổng chi phí", f"฿{merged['cost_of_goods'].sum():,.0f}")

st.divider()

if "category" in merged.columns:
    col1, col2 = st.columns(2)

    by_cat = merged.groupby("category").agg(
        revenue=("sales_revenue","sum"),
        cost=("cost_of_goods","sum"),
        profit=("sales_revenue","sum") - merged.groupby("category")["cost_of_goods"].sum(),
    ).reset_index()
    by_cat["margin_pct"] = (by_cat["profit"] / by_cat["revenue"] * 100).round(1)

    with col1:
        st.plotly_chart(bar_chart(by_cat, "category", "profit", "Lợi nhuận theo Danh mục"), use_container_width=True)

    with col2:
        st.plotly_chart(pie_chart(by_cat, "category", "profit", "Phân bổ Lợi nhuận theo Danh mục"), use_container_width=True)

    with st.expander("Bảng chi tiết Lợi nhuận"):
        display_df = by_cat[["category","revenue","cost","profit","margin_pct"]].copy()
        display_df.columns = ["Danh mục","Doanh thu","Chi phí","Lợi nhuận","Biên lợi nhuận (%)"]
        st.dataframe(display_df, use_container_width=True)
