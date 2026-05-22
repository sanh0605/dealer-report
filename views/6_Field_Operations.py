from components.ui_utils import show_centered_loader
PageLoader = show_centered_loader()
import streamlit as st
import pandas as pd
from datetime import date
from database.session import get_db
from database.models import FieldVisitPlan, VisitLog, DealerMaster
from services.analytics import calc_visit_adherence

try:
    user = st.session_state["user"]
    st.title("🗓️ Kế hoạch đi thị trường")

    tab_metrics, tab_log, tab_history = st.tabs(["Chỉ số Thăm", "Checkin", "Lịch sử Checkin"])

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

    # Handle both experimental and stable fragment decorators for Streamlit compatibility
    st_fragment = getattr(st, "fragment", getattr(st, "experimental_fragment", lambda f: f))

    @st_fragment
    def render_metrics_fragment(plan_df, log_df, dealer_df):
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

            # 2x2 Grid for better mobile readability
            r1_c1, r1_c2 = st.columns(2)
            r1_c1.metric("Tỷ lệ Hoàn thành", f"{adherence:.1f}%")
            r1_c2.metric("Đã thăm / Kế hoạch", f"{visited_count} / {planned_count}")
            
            r2_c1, r2_c2 = st.columns(2)
            r2_c1.metric("Thăm Ngoài kế hoạch", len(opportunistic))
            r2_c2.metric("Ngày làm việc", days_on_road)

            if missed:
                st.subheader("Đối tác chưa thăm")
                missed_info = pd.DataFrame({"dealer_id": missed})
                if not dealer_df.empty:
                    missed_info = missed_info.merge(dealer_df[["dealer_id","dealer_name","province"]], on="dealer_id", how="left")
                st.dataframe(missed_info, use_container_width=True)

    @st_fragment
    def render_checkin_fragment(plan_df, dealer_df, user):
        st.subheader("Checkin")
        
        # Create a display mapping: dealer_id -> "Name — Address"
        dealer_map = {}
        if not dealer_df.empty:
            for _, row in dealer_df.iterrows():
                name = str(row.get("dealer_name", "")).strip()
                addr = str(row.get("address", "")).strip()
                if not addr or addr == "nan":
                    addr = str(row.get("province", "")).strip()
                dealer_map[row["dealer_id"]] = f"{name} — {addr}"
        
        dealer_opts = [""] + list(dealer_map.keys())
        dealer_sel = st.selectbox(
            "Đối tác (Tên — Địa chỉ)", 
            dealer_opts,
            format_func=lambda x: dealer_map.get(x, "Chọn đối tác...") if x else "Chọn đối tác...",
            key="checkin_dealer"
        )

        # Logic to default the Purpose based on visit plan
        purpose_options = ["Khảo sát", "Chào hàng", "Tặng quà"]
        default_purpose_idx = 0

        if dealer_sel:
            current_month = date.today().strftime("%m/%Y")
            # Look for a plan for this user, this month, and this dealer
            if not plan_df.empty:
                plan_match = plan_df[
                    (plan_df["month_year"] == current_month) & 
                    (plan_df["staff_name"] == user["display_name"]) & 
                    (plan_df["dealer_id"] == dealer_sel)
                ]
                if not plan_match.empty:
                    planned_purpose = str(plan_match.iloc[0].get("purpose", "")).strip()
                    if planned_purpose in purpose_options:
                        default_purpose_idx = purpose_options.index(planned_purpose)

        purpose_sel = st.selectbox("Mục đích", purpose_options, index=default_purpose_idx, key="checkin_purpose")
        visit_result = st.text_area("Kết quả thăm / Ghi chú", key="checkin_result")

        def handle_checkin_submission():
            # Get current values from session state
            d_id = st.session_state.get("checkin_dealer")
            p_val = st.session_state.get("checkin_purpose")
            r_val = st.session_state.get("checkin_result", "").strip()

            if not d_id or not r_val:
                st.toast("⚠️ Vui lòng chọn đối tác và nhập ghi chú thăm.", icon="❌")
                return

            db = get_db()
            try:
                db.add(VisitLog(
                    date=date.today(),
                    staff_name=user["display_name"],
                    dealer_id=d_id,
                    visit_result=r_val,
                    purpose=p_val
                ))
                db.commit()
                st.toast("Đã lưu ghi nhận Checkin thành công.", icon="✅")
                
                # Safely reset session state values in the callback
                st.session_state["checkin_dealer"] = ""
                st.session_state["checkin_purpose"] = "Khảo sát"
                st.session_state["checkin_result"] = ""
                st.session_state["force_full_rerun"] = True
            except Exception as e:
                st.toast(f"❌ Lỗi: {str(e)}")
            finally:
                db.close()

        st.button("Lưu ghi nhận", type="primary", on_click=handle_checkin_submission)

        # If the callback requested a full rerun to update the history tab
        if st.session_state.get("force_full_rerun"):
            del st.session_state["force_full_rerun"]
            st.rerun()

    @st_fragment
    def render_history_fragment(log_df, dealer_df, user):
        st.subheader("Lịch sử Checkin")
        
        if log_df.empty:
            st.info("Chưa có lịch sử Checkin nào.")
            return

        # Role-based filtering
        display_df = log_df.copy()
        if user["role"] not in ["Admin", "Manager"]:
            display_df = display_df[display_df["staff_name"] == user["display_name"]]
        
        if display_df.empty:
            st.info("Bạn chưa có lịch sử Checkin nào.")
            return

        # Merge with dealer_df for better display
        if not dealer_df.empty:
            display_df = display_df.merge(
                dealer_df[["dealer_id", "dealer_name", "province", "address"]], 
                on="dealer_id", 
                how="left"
            )
        
        display_df = display_df.sort_values("date", ascending=False)
        
        # Pagination settings
        rows_per_page = 10
        total_rows = len(display_df)
        total_pages = (total_rows - 1) // rows_per_page + 1
        
        if "history_page" not in st.session_state:
            st.session_state.history_page = 1
        
        # Reset page if out of bounds (after deletion)
        if st.session_state.history_page > total_pages:
            st.session_state.history_page = max(1, total_pages)
            
        current_page = st.session_state.history_page
        start_idx = (current_page - 1) * rows_per_page
        end_idx = start_idx + rows_per_page
        page_df = display_df.iloc[start_idx:end_idx]

        # Prepare variables needed for edit mode
        dealer_map = {}
        if not dealer_df.empty:
            for _, d_row in dealer_df.iterrows():
                d_name = str(d_row.get("dealer_name", "")).strip()
                d_addr = str(d_row.get("address", "")).strip()
                if not d_addr or d_addr == "nan":
                    d_addr = str(d_row.get("province", "")).strip()
                dealer_map[d_row["dealer_id"]] = f"{d_name} — {d_addr}"
        dealer_opts_list = sorted(list(dealer_map.keys()))
        purpose_options = ["Khảo sát", "Chào hàng", "Tặng quà"]
        edit_id = st.session_state.get("history_edit_id")

        # Use a hybrid card layout instead of a wide table for responsiveness
        for _, row in page_df.iterrows():
            log_id = row["log_id"]
            
            with st.container(border=True):
                # c1 for info/inputs, c2 for action buttons
                # This 3:1 ratio looks good on desktop and stacks on mobile (<576px)
                c1, c2 = st.columns([3, 1])
                
                if edit_id == log_id:
                    # --- EDIT MODE (Vertical Stack) ---
                    c1.markdown("### Chỉnh sửa Checkin")
                    
                    new_dealer = c1.selectbox(
                        "Đối tác", dealer_opts_list, 
                        index=dealer_opts_list.index(row["dealer_id"]) if row["dealer_id"] in dealer_opts_list else 0,
                        format_func=lambda x: dealer_map.get(x, x),
                        key=f"edit_dealer_{log_id}"
                    )
                    
                    new_purpose = c1.selectbox(
                        "Mục đích", purpose_options,
                        index=purpose_options.index(row["purpose"]) if row["purpose"] in purpose_options else 0,
                        key=f"edit_purpose_{log_id}"
                    )
                    
                    new_result = c1.text_area(
                        "Kết quả / Ghi chú", value=row["visit_result"], 
                        key=f"edit_result_{log_id}"
                    )
                    
                    # Actions for Edit mode
                    b1, b2 = c2.columns(2)
                    if b1.button("Lưu", key=f"save_{log_id}", type="primary", use_container_width=True):
                        db = get_db()
                        try:
                            log_record = db.query(VisitLog).filter(VisitLog.log_id == log_id).first()
                            if log_record:
                                log_record.dealer_id = new_dealer
                                log_record.purpose = new_purpose
                                log_record.visit_result = new_result
                                db.commit()
                                st.toast("Cập nhật thành công!", icon="✅")
                                st.session_state.history_edit_id = None
                                st.rerun()
                        finally:
                            db.close()
                    if b2.button("Huỷ", key=f"cancel_{log_id}", use_container_width=True):
                        st.session_state.history_edit_id = None
                        st.rerun()
                else:
                    # --- VIEW MODE (Rich Card) ---
                    date_str = row["date"].strftime("%d/%m/%Y") if pd.notnull(row["date"]) else "N/A"
                    
                    c1.markdown(f"**{row['dealer_name']}**")
                    c1.caption(f"🗓️ {date_str} | 👤 {row['staff_name']} | 📍 {row['province']}")
                    c1.markdown(f"🎯 **{row['purpose']}**: {row['visit_result']}")
                    
                    # Popover for actions
                    with c2.popover("Hành động", use_container_width=True):
                        if st.button("Cập nhật", key=f"btn_edit_{log_id}", use_container_width=True):
                            st.session_state.history_edit_id = log_id
                            st.rerun()
                        if st.button("Xoá", key=f"btn_del_{log_id}", use_container_width=True):
                            db = get_db()
                            try:
                                log_record = db.query(VisitLog).filter(VisitLog.log_id == log_id).first()
                                if log_record:
                                    db.delete(log_record)
                                    db.commit()
                                    st.toast("Đã xoá bản ghi.", icon="🗑️")
                                    st.rerun()
                            finally:
                                db.close()
            st.divider()

        # Pagination Controls
        if total_pages > 1:
            st.write("") # spacing
            p_cols = st.columns([1, 1, 1])
            if current_page > 1:
                if p_cols[0].button("← Trang trước", use_container_width=True):
                    st.session_state.history_page -= 1
                    st.rerun()
            p_cols[1].markdown(f"<p style='text-align: center;'>Trang {current_page} / {total_pages}</p>", unsafe_allow_html=True)
            if current_page < total_pages:
                if p_cols[2].button("Trang sau →", use_container_width=True):
                    st.session_state.history_page += 1
                    st.rerun()

    with tab_metrics:
        render_metrics_fragment(plan_df, log_df, dealer_df)

    with tab_log:
        render_checkin_fragment(plan_df, dealer_df, user)

    with tab_history:
        render_history_fragment(log_df, dealer_df, user)

finally:
    PageLoader.empty()

