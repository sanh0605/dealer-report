from components.ui_utils import show_centered_loader
PageLoader = show_centered_loader()
import streamlit as st
from database.session import get_db
from database.models import User
from services.user_service import change_password
import bcrypt

st.set_page_config(page_title="Hồ sơ cá nhân", layout="wide")

if "user" not in st.session_state:
    st.error("Vui lòng đăng nhập từ trang chủ.")
    st.stop()

user_state = st.session_state["user"]
username = user_state["username"]

st.title("👤 Hồ sơ cá nhân")

db = get_db()
try:
    user = db.query(User).filter_by(username=username).first()
    
    st.subheader("Thông tin người dùng")
    st.write(f"**Tên đăng nhập:** {user.username}")
    st.write(f"**Vai trò:** {user.role}")
    st.write(f"**Tên hiển thị:** {user.display_name}")

    st.divider()

    st.subheader("Đổi Mật khẩu")
    with st.form("self_service_password_form"):
        current_password = st.text_input("Mật khẩu hiện tại", type="password")
        new_password = st.text_input("Mật khẩu mới", type="password")
        confirm_pw   = st.text_input("Xác nhận Mật khẩu mới", type="password")
        submitted = st.form_submit_button("Cập nhật Mật khẩu")
        
    if submitted:
        if not bcrypt.checkpw(current_password.encode(), user.password_hash.encode()):
            st.error("Mật khẩu hiện tại không đúng.")
        elif new_password != confirm_pw:
            st.error("Mật khẩu xác nhận không khớp.")
        elif len(new_password) < 8:
            st.error("Mật khẩu phải có ít nhất 8 ký tự.")
        else:
            success = change_password(db, user.id, new_password, action_by=user.username)
            if success:
                st.success("Đổi mật khẩu thành công.")
            else:
                st.error("Đã xảy ra lỗi khi đổi mật khẩu.")

finally:
    db.close()

PageLoader.empty()

