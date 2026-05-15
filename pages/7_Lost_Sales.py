from components.ui_utils import show_centered_loader
PageLoader = show_centered_loader()
import streamlit as st
import pandas as pd
from datetime import date, timedelta
from database.session import get_db
from database.models import LostSalesEntry, DealerMaster, ProductMaster, SaleRecord

st.set_page_config(page_title="Bán mất", layout="wide")

try:
    if "user" not in st.session_state:
        st.error("Vui lòng đăng nhập từ trang chủ.")
        st.stop()

    user = st.session_state["user"]
    st.title("❌ Bán mất")

    tab_entry, tab_summary = st.tabs(["Ghi nhận Bán mất", "Tóm tắt"])

    db = get_db()
    try:
        dealer_rows  = db.query(DealerMaster).all()
        product_rows = db.query(ProductMaster).all()
        sale_rows    = db.query(SaleRecord).all()
        ls_rows      = db.query(LostSalesEntry).all()
    finally:
        db.close()

    dealer_df  = pd.DataFrame([r.__dict__ for r in dealer_rows]).drop(columns=["_sa_instance_state"], errors="ignore") if dealer_rows else pd.DataFrame()
    product_df = pd.DataFrame([r.__dict__ for r in product_rows]).drop(columns=["_sa_instance_state"], errors="ignore") if product_rows else pd.DataFrame()
    sale_df    = pd.DataFrame([r.__dict__ for r in sale_rows]).drop(columns=["_sa_instance_state"], errors="ignore") if sale_rows else pd.DataFrame()
    ls_df      = pd.DataFrame([r.__dict__ for r in ls_rows]).drop(columns=["_sa_instance_state"], errors="ignore") if ls_rows else pd.DataFrame()

    def _calculate_avg_unit_price(dealer_id: str, item_id: str) -> float:
        if sale_df.empty:
            return 0.0

        sale_df["order_date"] = pd.to_datetime(sale_df["order_date"], dayfirst=True, errors="coerce")
        three_months_ago = date.today() - timedelta(days=90)
        recent_sales = sale_df[sale_df["order_date"] >= three_months_ago]

        dealer_item_sales = recent_sales[
            (recent_sales["dealer_id"] == dealer_id) &
            (recent_sales["item_id"] == item_id) &
            (recent_sales["sales_volume"] > 0)
        ]
        if not dealer_item_sales.empty:
            return (dealer_item_sales["sales_revenue"].sum() /
                    dealer_item_sales["sales_volume"].sum())

        item_sales = recent_sales[
            (recent_sales["item_id"] == item_id) &
            (recent_sales["sales_volume"] > 0)
        ]
        if not item_sales.empty:
            return (item_sales["sales_revenue"].sum() /
                    item_sales["sales_volume"].sum())

        return 0.0

    with tab_entry:
        dealer_opts  = (dealer_df["dealer_id"] + " — " + dealer_df["dealer_name"]).tolist() if not dealer_df.empty else []
        product_opts = (product_df["item_id"] + " — " + product_df["item_name"]).tolist() if not product_df.empty else []

        if not dealer_opts or not product_opts:
            st.warning("Hãy tải dữ liệu dealer_master và product_master trước khi ghi nhận bán mất.")
        else:
            with st.form("lost_sales_form"):
                dealer_sel  = st.selectbox("Đối tác", dealer_opts)
                item_sel    = st.selectbox("Sản phẩm (SKU)", product_opts)
                lost_volume = st.number_input("Số lượng bán mất (đơn vị)", min_value=1, step=1)
                submitted   = st.form_submit_button("Gửi")

            if submitted:
                dealer_id = dealer_sel.split(" — ")[0]
                item_id   = item_sel.split(" — ")[0]
                avg_unit_price = _calculate_avg_unit_price(dealer_id, item_id)

                if avg_unit_price == 0.0:
                    st.error("Không thể tính doanh thu bán mất: không có lịch sử bán hàng cho sản phẩm này trong 3 tháng qua.")
                    st.info("Sản phẩm mới chưa có lịch sử bán hàng nên nên được xử lý như đơn hàng đang chờ.")
                else:
                    lost_revenue = lost_volume * avg_unit_price
                    db = get_db()
                    try:
                        db.add(LostSalesEntry(
                            date=date.today(),
                            staff_name=user["display_name"],
                            dealer_id=dealer_id,
                            item_id=item_id,
                            lost_volume=int(lost_volume),
                            lost_revenue=lost_revenue,
                        ))
                        db.commit()
                        st.success(f"Đã ghi nhận: {lost_volume} đơn vị × ฿{avg_unit_price:,.2f} = ฿{lost_revenue:,.2f} doanh thu bị mất.")
                    finally:
                        db.close()

    with tab_summary:
        if ls_df.empty:
            st.info("Chưa có ghi nhận bán mất.")
        else:
            ls_df["lost_volume"]  = pd.to_numeric(ls_df["lost_volume"], errors="coerce").fillna(0)
            ls_df["lost_revenue"] = pd.to_numeric(ls_df["lost_revenue"], errors="coerce").fillna(0)
            st.metric("Tổng Doanh thu bị mất", f"฿{ls_df['lost_revenue'].sum():,.0f}")
            st.metric("Tổng Số lượng bị mất", f"{int(ls_df['lost_volume'].sum()):,} đơn vị")
            st.dataframe(ls_df.sort_values("date", ascending=False).reset_index(drop=True), use_container_width=True)

finally:
    PageLoader.empty()

