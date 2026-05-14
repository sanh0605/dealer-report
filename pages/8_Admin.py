import streamlit as st
import pandas as pd
import bcrypt
from database.session import get_db
from database.models import User, SalesTarget
from auth.service import require_role
from services.upload_service import load_file, validate_columns, upsert_dataframe

st.set_page_config(page_title="Quản trị", layout="wide")
if "user" not in st.session_state:
    st.error("Vui lòng đăng nhập từ trang chủ.")
    st.stop()

user = st.session_state["user"]
try:
    require_role(type("U", (), user)(), ["Admin"])
except PermissionError:
    st.error("Chỉ Admin mới có quyền truy cập trang này.")
    st.stop()

st.title("⚙️ Bảng điều khiển Quản trị")

tab_users, tab_targets = st.tabs(["Quản lý Người dùng", "Mục tiêu Bán hàng"])

with tab_users:
    db = get_db()
    try:
        users = db.query(User).all()
    finally:
        db.close()

    user_data = [{"username": u.username, "role": u.role, "display_name": u.display_name} for u in users]
    st.dataframe(pd.DataFrame(user_data), use_container_width=True)

    st.subheader("Đổi Mật khẩu")
    with st.form("change_password_form"):
        target_user = st.selectbox("Người dùng", [u.username for u in users])
        new_password = st.text_input("Mật khẩu mới", type="password")
        confirm_pw   = st.text_input("Xác nhận Mật khẩu", type="password")
        submitted = st.form_submit_button("Cập nhật Mật khẩu")
    if submitted:
        if new_password != confirm_pw:
            st.error("Mật khẩu không khớp.")
        elif len(new_password) < 8:
            st.error("Mật khẩu phải có ít nhất 8 ký tự.")
        else:
            db = get_db()
            try:
                u = db.query(User).filter_by(username=target_user).first()
                u.password_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
                db.commit()
                st.success(f"Đã cập nhật mật khẩu cho {target_user}.")
            finally:
                db.close()

with tab_targets:
    st.subheader("Tải lên Mục tiêu Bán hàng (CSV/Excel)")
    st.caption("Các cột bắt buộc: month_year, sub_region, target_revenue")
    uploaded = st.file_uploader("Tệp Mục tiêu", type=["csv","xlsx","xls"], key="targets_upload")
    if uploaded:
        df = load_file(uploaded.read(), uploaded.name)
        missing = validate_columns(df, "sales_targets")
        if missing:
            st.error(f"Cột thiếu: {', '.join(missing)}")
        else:
            st.dataframe(df.head(), use_container_width=True)
            if st.button("Tải lên Mục tiêu"):
                db = get_db()
                try:
                    count = upsert_dataframe(db, df, "sales_targets")
                    st.success(f"Đã tải lên {count} hàng mục tiêu.")
                except Exception as e:
                    st.error(f"Tải lên thất bại: {e}")
                finally:
                    db.close()
