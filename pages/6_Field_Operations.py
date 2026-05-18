from components.ui_utils import show_centered_loader
PageLoader = show_centered_loader()
import streamlit as st
import pandas as pd
from datetime import date
from database.session import get_db
from database.models import FieldVisitPlan, VisitLog, DealerMaster
from services.analytics import calc_visit_adherence

st.set_page_config(page_title="Vận động trường", layout="wide")

try:
    if "user" not in st.session_state:
        st.error("Vui lòng đăng nhập từ trang chủ.")
        PageLoader.empty()
        st.stop()

    user = st.session_state["user"]
    st.title("🗓️ Vận động trường")

    tab_metrics, tab_log = st.tabs(["Chỉ số Thăm", "Ghi nhận Thăm"])

    db = get_db()
    try:
        plan_rows   = db.query(FieldVisitPlan).all()
        log_rows    = db.query(VisitLog).all()
        dealer_rows = db.query(DealerMaster).all()
    finally:
        db.close()

    plan_df   = pd.DataFrame([r.__dict__ for r in plan_rows]).drop(columns=["_sa_instance_state"], errors="ignore") if plan_rows else pd.DataFrame()
    log_df    = pd.DataFrame([r.__dict__ for r in log_rows]).drop(columns=["_sa_instance_state"], errors="ignore") if log_rows else pd.DataFrame()
    dealer_df = pd.DataFrame([r.__dict__ for r in dealer_rows]).drop(columns=["_sa_instance_state"], errors="ignore") if dealer_rows else pd.DataFrame()

    with tab_metrics:
        if plan_df.empty:
            st.info("Không tìm thấy kế hoạch thăm. Hãy tải dữ liệu field_visit_plans trước.")
        else:
            months = sorted(plan_df["month_year"].dropna().unique().tolist(), reverse=True)
            sel_month = st.selectbox("Tháng", months)
            sel_staff = st.selectbox("Nhân viên", ["Tất cả"] + sorted(plan_df["staff_name"].dropna().unique().tolist()))

            mp = plan_df[plan_df["month_year"] == sel_month]
            if sel_staff != "Tất cả":
                mp = mp[mp["staff_name"] == sel_staff]
            ml = log_df.copy()
            if not ml.empty and "date" in ml.columns:
                ml["date"] = pd.to_datetime(ml["date"], errors="coerce")
                ml = ml[ml["date"].dt.strftime("%m/%Y") == sel_month]
            if sel_staff != "Tất cả" and not ml.empty:
                ml = ml[ml["staff_name"] == sel_staff]

            adherence, missed = calc_visit_adherence(mp, ml)
            planned_count = len(mp)
            visited_count = planned_count - len(missed)
            opportunistic = (set(ml["dealer_id"].unique()) - set(mp["dealer_id"].unique())) if not ml.empty else set()
            days_on_road = ml["date"].dt.date.nunique() if not ml.empty else 0

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Tỷ lệ Hoàn thành", f"{adherence:.1f}%")
            c2.metric("Đã thăm / Kế hoạch", f"{visited_count} / {planned_count}")
            c3.metric("Thăm Ngoài kế hoạch", len(opportunistic))
            c4.metric("Ngày làm việc", days_on_road)

            if missed:
                st.subheader("Đối tác chưa thăm")
                missed_info = pd.DataFrame({"dealer_id": missed})
                if not dealer_df.empty:
                    missed_info = missed_info.merge(dealer_df[["dealer_id","dealer_name","province"]], on="dealer_id", how="left")
                st.dataframe(missed_info, use_container_width=True)

    with tab_log:
        st.subheader("Ghi nhận Thăm")
        with st.form("visit_log_form"):
            visit_date   = st.date_input("Ngày thăm", value=date.today())
            dealer_opts  = [""] + (dealer_df["dealer_id"] + " — " + dealer_df["dealer_name"]).tolist() if not dealer_df.empty else [""]
            dealer_sel   = st.selectbox("Đối tác (ID — Tên)", dealer_opts)
            visit_result = st.text_area("Kết quả thăm / Ghi chú")
            submitted    = st.form_submit_button("Lưu ghi nhận")

        if submitted:
            if not dealer_sel or not visit_result.strip():
                st.error("Vui lòng chọn đối tác và nhập ghi chú thăm.")
            else:
                dealer_id = dealer_sel.split(" — ")[0]
                db = get_db()
                try:
                    db.add(VisitLog(
                        date=visit_date,
                        staff_name=user["display_name"],
                        dealer_id=dealer_id,
                        visit_result=visit_result.strip(),
                    ))
                    db.commit()
                    st.success("Đã lưu ghi nhận thăm thành công.")
                finally:
                    db.close()

finally:
    PageLoader.empty()

