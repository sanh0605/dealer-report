from components.ui_utils import show_centered_loader
PageLoader = show_centered_loader()
import streamlit as st
import pandas as pd
import uuid
from datetime import date, timedelta
from database.gsheets_db import read_sheet, append_row

try:
    if "user" not in st.session_state:
        st.error("Vui lòng đăng nhập.")
        st.stop()
        
    user = st.session_state["user"]
    st.title("❌ Bán mất")

    tab_entry, tab_summary = st.tabs(["Ghi nhận Bán mất", "Tóm tắt"])

    # Load data from Google Sheets
    dealer_df = read_sheet("dealer_master")
    product_df = read_sheet("product_master")
    sale_df = read_sheet("sale_records")
    ls_df = read_sheet("lost_sales")

    def _calculate_avg_unit_price(dealer_id: str, item_id: str) -> float:
        if sale_df.empty:
            return 0.0

        # Create copy for calculations
        sdf = sale_df.copy()
        if "order_date" in sdf.columns:
            sdf["order_date"] = pd.to_datetime(sdf["order_date"], format="mixed", errors="coerce")
        elif "date_transfer" in sdf.columns:
            sdf["order_date"] = pd.to_datetime(sdf["date_transfer"], format="mixed", errors="coerce")
        else:
            return 0.0
            
        three_months_ago = pd.Timestamp(date.today() - timedelta(days=90))
        recent_sales = sdf[sdf["order_date"] >= three_months_ago].copy()
        
        if recent_sales.empty:
            return 0.0

        # Clean numeric columns
        for col in ["sales_volume", "sales_revenue"]:
            if col in recent_sales.columns:
                recent_sales[col] = pd.to_numeric(recent_sales[col], errors="coerce").fillna(0)

        dealer_item_sales = recent_sales[
            (recent_sales["dealer_id"].astype(str) == str(dealer_id)) &
            (recent_sales["item_id"].astype(str) == str(item_id)) &
            (recent_sales["sales_volume"] > 0)
        ]
        if not dealer_item_sales.empty:
            return (dealer_item_sales["sales_revenue"].sum() /
                    dealer_item_sales["sales_volume"].sum())

        item_sales = recent_sales[
            (recent_sales["item_id"].astype(str) == str(item_id)) &
            (recent_sales["sales_volume"] > 0)
        ]
        if not item_sales.empty:
            return (item_sales["sales_revenue"].sum() /
                    item_sales["sales_volume"].sum())

        return 0.0

    with tab_entry:
        dealer_opts = []
        if not dealer_df.empty:
            dealer_opts = (dealer_df["dealer_id"].astype(str) + " — " + dealer_df["dealer_name"].astype(str)).tolist()
            
        product_opts = []
        if not product_df.empty:
            product_opts = (product_df["item_id"].astype(str) + " — " + product_df["item_name"].astype(str)).tolist()

        if not dealer_opts or not product_opts:
            st.warning("Hãy tải dữ liệu dealer_master và product_master trước khi ghi nhận bán mất.")
        else:
            with st.form("lost_sales_form"):
                dealer_sel = st.selectbox("Đối tác", dealer_opts)
                item_sel = st.selectbox("Sản phẩm (SKU)", product_opts)
                lost_volume = st.number_input("Số lượng bán mất (đơn vị)", min_value=1, step=1)
                submitted = st.form_submit_button("Gửi")

            if submitted:
                dealer_id = dealer_sel.split(" — ")[0]
                item_id = item_sel.split(" — ")[0]
                avg_unit_price = _calculate_avg_unit_price(dealer_id, item_id)

                if avg_unit_price == 0.0:
                    st.error("Không thể tính doanh thu bán mất: không có lịch sử bán hàng cho sản phẩm này trong 3 tháng qua.")
                else:
                    lost_revenue = lost_volume * avg_unit_price
                    try:
                        new_ls = {
                            "id": str(uuid.uuid4()),
                            "date": date.today().strftime("%Y-%m-%d"),
                            "staff_name": user["display_name"],
                            "dealer_id": dealer_id,
                            "item_id": item_id,
                            "lost_volume": int(lost_volume),
                            "lost_revenue": lost_revenue,
                        }
                        append_row("lost_sales", new_ls)
                        st.success(f"Đã ghi nhận: {lost_volume} đơn vị × {avg_unit_price:,.2f} = {lost_revenue:,.2f} doanh thu bị mất.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Lỗi: {e}")

    with tab_summary:
        if ls_df.empty:
            st.info("Chưa có ghi nhận bán mất.")
        else:
            ls_df["lost_volume"] = pd.to_numeric(ls_df["lost_volume"], errors="coerce").fillna(0)
            ls_df["lost_revenue"] = pd.to_numeric(ls_df["lost_revenue"], errors="coerce").fillna(0)
            
            c1, c2 = st.columns(2)
            c1.metric("Tổng Doanh thu bị mất", f"{ls_df['lost_revenue'].sum():,.0f}")
            c2.metric("Tổng Số lượng bị mất", f"{int(ls_df['lost_volume'].sum()):,} đơn vị")
            
            st.dataframe(
                ls_df.sort_values("date", ascending=False).reset_index(drop=True), 
                use_container_width=True,
                column_config={
                    "lost_revenue": st.column_config.NumberColumn(format="%,.0f")
                }
            )

finally:
    PageLoader.empty()
