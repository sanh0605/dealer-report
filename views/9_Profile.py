from components.ui_utils import show_centered_loader
PageLoader = show_centered_loader()
import streamlit as st
import bcrypt
from database.gsheets_db import read_sheet
from services.identity import change_password

try:
    if "user" not in st.session_state:
        st.error("Vui lòng đăng nhập.")
        st.stop()
        
    user_state = st.session_state["user"]
    username = user_state["username"]

    st.title("👤 Hồ sơ cá nhân")

    # Load user data from Google Sheets to verify current password
    users_df = read_sheet("users", ttl=0)
    
    if users_df.empty:
        st.error("Lỗi: Không tìm thấy dữ liệu người dùng.")
        st.stop()
        
    user_row = users_df[users_df["username"] == username]
    if user_row.empty:
        st.error("Không tìm thấy thông tin tài khoản.")
        st.stop()
        
    user_data = user_row.iloc[0]
    
    st.subheader("Thông tin người dùng")
    st.write(f"**Tên đăng nhập:** {user_data['username']}")
    st.write(f"**Vai trò:** {user_data['role']}")
    st.write(f"**Tên hiển thị:** {user_data['display_name']}")

    st.divider()

    st.subheader("Đổi Mật khẩu")
    with st.form("self_service_password_form"):
        current_password = st.text_input("Mật khẩu hiện tại", type="password")
        new_password = st.text_input("Mật khẩu mới", type="password")
        confirm_pw   = st.text_input("Xác nhận Mật khẩu mới", type="password")
        submitted = st.form_submit_button("Cập nhật Mật khẩu")
        
    if submitted:
        # Check current password hash
        if not bcrypt.checkpw(current_password.encode(), str(user_data['password_hash']).encode()):
            st.error("Mật khẩu hiện tại không đúng.")
        elif new_password != confirm_pw:
            st.error("Mật khẩu xác nhận không khớp.")
        elif len(new_password) < 8:
            st.error("Mật khẩu phải có ít nhất 8 ký tự.")
        else:
            success = change_password(None, str(user_data['id']), new_password, action_by=username)
            if success:
                st.success("Đổi mật khẩu thành công.")
            else:
                st.error("Đã xảy ra lỗi khi đổi mật khẩu.")

finally:
    PageLoader.empty()
