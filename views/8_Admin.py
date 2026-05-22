from components.ui_utils import show_centered_loader
PageLoader = show_centered_loader()
import streamlit as st
import pandas as pd
from database.gsheets_db import read_sheet
from services.identity import (
    require_role, create_user, update_user, delete_user, get_audit_logs
)

try:
    if "user" not in st.session_state:
        st.error("Vui lòng đăng nhập.")
        st.stop()
        
    user_state = st.session_state["user"]
    try:
        require_role(user_state, ["Admin"])
    except PermissionError:
        st.error("Chỉ Admin mới có quyền truy cập trang này.")
        PageLoader.empty()
        st.stop()

    st.title("⚙️ Bảng điều khiển Quản trị")

    tab_users, tab_audit = st.tabs(["Quản lý Người dùng", "Nhật ký Hệ thống (Audit)"])

    # Load users from Google Sheets
    users_df = read_sheet("users", ttl=0)
    
    with tab_users:
        if not users_df.empty:
            display_users = users_df[["username", "role", "display_name"]].copy()
            display_users.columns = ["Tên đăng nhập", "Vai trò", "Tên hiển thị"]
            st.dataframe(display_users, use_container_width=True, hide_index=True)
        else:
            st.info("Chưa có người dùng nào.")

        op_create, op_edit, op_delete = st.tabs(["➕ Tạo người dùng mới", "✏️ Sửa người dùng", "🗑️ Xóa người dùng"])
        
        with op_create:
            with st.form("create_user_form"):
                new_username = st.text_input("Tên đăng nhập")
                new_password = st.text_input("Mật khẩu", type="password")
                new_role = st.selectbox("Vai trò", ["Admin", "Manager", "Sales Staff"])
                new_display_name = st.text_input("Tên hiển thị")
                submitted_create = st.form_submit_button("Tạo mới", use_container_width=True)
            if submitted_create:
                if len(new_password) < 8:
                    st.error("Mật khẩu phải có ít nhất 8 ký tự.")
                elif not users_df.empty and new_username in users_df['username'].values:
                    st.error("Tên đăng nhập đã tồn tại.")
                elif not new_username or not new_display_name:
                    st.error("Vui lòng điền đầy đủ thông tin.")
                else:
                    create_user(None, new_username, new_password, new_role, new_display_name, user_state["username"])
                    st.success("Tạo người dùng thành công!")
                    st.rerun()

        with op_edit:
            if not users_df.empty:
                with st.form("edit_user_form"):
                    edit_target = st.selectbox("Chọn người dùng", users_df["username"].tolist())
                    edit_role = st.selectbox("Vai trò mới", ["Admin", "Manager", "Sales Staff"])
                    edit_display_name = st.text_input("Tên hiển thị mới")
                    submitted_edit = st.form_submit_button("Cập nhật", use_container_width=True)
                if submitted_edit:
                    if not edit_display_name:
                        st.error("Tên hiển thị không được để trống.")
                    else:
                        target_row = users_df[users_df["username"] == edit_target].iloc[0]
                        update_user(None, str(target_row["id"]), edit_role, edit_display_name, user_state["username"])
                        st.success("Cập nhật thành công!")
                        st.rerun()
            else:
                st.info("Không có người dùng để sửa.")

        with op_delete:
            if not users_df.empty:
                with st.form("delete_user_form"):
                    delete_target = st.selectbox("Người dùng cần xóa", users_df["username"].tolist())
                    st.warning("⚠️ Hành động này không thể hoàn tác.")
                    submitted_delete = st.form_submit_button("Xóa", type="primary", use_container_width=True)
                if submitted_delete:
                    if delete_target == user_state["username"]:
                        st.error("Bạn không thể tự xóa tài khoản của chính mình.")
                    else:
                        target_row = users_df[users_df["username"] == delete_target].iloc[0]
                        delete_user(None, str(target_row["id"]), user_state["username"])
                        st.success("Đã xóa người dùng!")
                        st.rerun()
            else:
                st.info("Không có người dùng để xóa.")

    with tab_audit:
        st.subheader("Nhật ký hoạt động (100 bản ghi gần nhất)")
        logs = get_audit_logs(None, limit=100)
        if logs:
            log_data = [{
                "Thời gian": l.timestamp.strftime("%Y-%m-%d %H:%M:%S") if l.timestamp else "",
                "Người thực hiện": l.username,
                "Hành động": l.action_type,
                "Chi tiết": l.details
            } for l in logs]
            st.dataframe(pd.DataFrame(log_data), use_container_width=True, hide_index=True)
        else:
            st.info("Chưa có bản ghi nhật ký nào.")

finally:
    PageLoader.empty()
