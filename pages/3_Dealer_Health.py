import streamlit as st
import pandas as pd
from database.session import get_db
from database.models import AccountsReceivableLedger, DealerMaster, SaleRecord
from services.analytics import calc_ar_outstanding

st.set_page_config(page_title="Sức khỏe Đối tác", layout="wide")
if "user" not in st.session_state:
    st.error("Vui lòng đăng nhập từ trang chủ.")
    st.stop()

st.title("🏪 Sức khỏe Đối tác")

db = get_db()
try:
    ar_rows   = db.query(AccountsReceivableLedger).all()
    dlr_rows  = db.query(DealerMaster).all()
    sale_rows = db.query(SaleRecord).all()
finally:
    db.close()

if not ar_rows:
    st.info("Không tìm thấy dữ liệu công nợ. Hãy tải dữ liệu accounts_receivable_ledger trước.")
    st.stop()

ar_df   = pd.DataFrame([r.__dict__ for r in ar_rows]).drop(columns=["_sa_instance_state"], errors="ignore")
dlr_df  = pd.DataFrame([r.__dict__ for r in dlr_rows]).drop(columns=["_sa_instance_state"], errors="ignore")
sale_df = pd.DataFrame([r.__dict__ for r in sale_rows]).drop(columns=["_sa_instance_state"], errors="ignore")

for col in ["total_order_value","paid_amount","refund_amount","deduction_amount"]:
    ar_df[col] = pd.to_numeric(ar_df[col], errors="coerce").fillna(0)

per_order = ar_df.groupby("order_id").agg(
    total=("total_order_value","max"),
    paid=("paid_amount","sum"),
    refund=("refund_amount","sum"),
    deduction=("deduction_amount","sum"),
).reset_index()
per_order["outstanding"] = (per_order["total"] - per_order["paid"] - per_order["refund"] - per_order["deduction"]).clip(lower=0)

if not sale_df.empty and "dealer_id" in sale_df.columns:
    order_dealer = sale_df[["order_id","dealer_id"]].drop_duplicates("order_id")
    per_order = per_order.merge(order_dealer, on="order_id", how="left")
    by_dealer = per_order.groupby("dealer_id")["outstanding"].sum().reset_index()
    if not dlr_df.empty:
        by_dealer = by_dealer.merge(dlr_df[["dealer_id","dealer_name","business_name","region"]], on="dealer_id", how="left")
    by_dealer = by_dealer.sort_values("outstanding", ascending=False).reset_index(drop=True)
    st.subheader("Công nợ theo Đối tác")
    st.dataframe(by_dealer, use_container_width=True)
    total_outstanding = calc_ar_outstanding(ar_df)
    st.metric("Tổng Công nợ (Tất cả Đối tác)", f"฿{total_outstanding:,.0f}")
else:
    st.dataframe(per_order, use_container_width=True)
