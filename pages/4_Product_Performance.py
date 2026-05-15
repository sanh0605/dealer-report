from components.ui_utils import show_centered_loader
PageLoader = show_centered_loader()
import streamlit as st
import pandas as pd
from database.session import get_db
from database.models import SaleRecord, ProductMaster
from components.charts import bar_chart, treemap_chart

st.set_page_config(page_title="Hiệu suất Sản phẩm", layout="wide")
if "user" not in st.session_state:
    st.error("Vui lòng đăng nhập từ trang chủ.")
    st.stop()

st.title("📦 Hiệu suất Sản phẩm")

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

for col in ["sales_revenue","sales_volume","cost_of_goods"]:
    sale_df[col] = pd.to_numeric(sale_df[col], errors="coerce").fillna(0)

if not prod_df.empty:
    merged = sale_df.merge(prod_df[["item_id","brand_group","brand","category","subcategory","model"]], on="item_id", how="left")
else:
    merged = sale_df

tab1, tab2, tab3 = st.tabs(["Theo Thương hiệu", "Theo Danh mục", "Theo SKU"])

with tab1:
    if "brand_group" in merged.columns:
        by_bg = merged.groupby("brand_group")["sales_revenue"].sum().reset_index()
        st.plotly_chart(bar_chart(by_bg, "brand_group", "sales_revenue", "Doanh thu theo Nhóm Thương hiệu"), use_container_width=True)

with tab2:
    if "category" in merged.columns:
        by_cat = merged.groupby("category")[["sales_revenue","sales_volume"]].sum().reset_index()
        st.plotly_chart(bar_chart(by_cat, "category", "sales_revenue", "Doanh thu theo Danh mục"), use_container_width=True)
        if "subcategory" in merged.columns:
            treemap_data = merged.groupby(["category","subcategory"])["sales_revenue"].sum().reset_index()
            st.plotly_chart(treemap_chart(treemap_data, ["category","subcategory"], "sales_revenue", "Biểu đồ Treemap Doanh thu"), use_container_width=True)

with tab3:
    top_skus = merged.groupby("item_id")[["sales_revenue","sales_volume"]].sum().reset_index().sort_values("sales_revenue", ascending=False).head(20)
    st.dataframe(top_skus, use_container_width=True)

PageLoader.empty()

