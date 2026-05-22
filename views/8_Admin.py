from components.ui_utils import show_centered_loader
PageLoader = show_centered_loader()
import streamlit as st
import pandas as pd
from database.session import get_db
from database.models import User
from services.identity import (
    require_role, create_user, update_user, delete_user, get_audit_logs
)
from services.upload_service import load_file, validate_columns, upsert_dataframe

try:
    user_state = st.session_state["user"]
    try:
        require_role(type("U", (), user_state)(), ["Admin"])
    except PermissionError:
        st.error("Chỉ Admin mới có quyền truy cập trang này.")
        PageLoader.empty()
        st.stop()

    st.title("⚙️ Bảng điều khiển Quản trị")

    tab_users, tab_audit = st.tabs(["Quản lý Người dùng", "Nhật ký Hệ thống (Audit)"])

    db = get_db()
    try:
        with tab_users:
            users = db.query(User).all()
            user_data = [{"id": u.id, "Tên đăng nhập": u.username, "Vai trò": u.role, "Tên hiển thị": u.display_name} for u in users]
            st.dataframe(pd.DataFrame(user_data).drop(columns=["id"]), use_container_width=True)

            # Nested tabs for user operations improve focus on mobile and desktop
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
                    elif any(u.username == new_username for u in users):
                        st.error("Tên đăng nhập đã tồn tại.")
                    elif not new_username or not new_display_name:
                        st.error("Vui lòng điền đầy đủ thông tin.")
                    else:
                        create_user(db, new_username, new_password, new_role, new_display_name, user_state["username"])
                        st.success("Tạo người dùng thành công! Vui lòng tải lại trang.")

            with op_edit:
                with st.form("edit_user_form"):
                    edit_target = st.selectbox("Chọn người dùng", [u.username for u in users])
                    edit_role = st.selectbox("Vai trò mới", ["Admin", "Manager", "Sales Staff"])
                    edit_display_name = st.text_input("Tên hiển thị mới")
                    submitted_edit = st.form_submit_button("Cập nhật", use_container_width=True)
                if submitted_edit:
                    if not edit_display_name:
                        st.error("Tên hiển thị không được để trống.")
                    else:
                        target_u = next(u for u in users if u.username == edit_target)
                        update_user(db, target_u.id, edit_role, edit_display_name, user_state["username"])
                        st.success("Cập nhật thành công! Vui lòng tải lại trang.")

            with op_delete:
                with st.form("delete_user_form"):
                    delete_target = st.selectbox("Người dùng cần xóa", [u.username for u in users])
                    st.warning("⚠️ Hành động này không thể hoàn tác.")
                    submitted_delete = st.form_submit_button("Xóa", type="primary", use_container_width=True)
                if submitted_delete:
                    if delete_target == user_state["username"]:
                        st.error("Bạn không thể tự xóa tài khoản của chính mình.")
                    else:
                        target_u = next(u for u in users if u.username == delete_target)
                        delete_user(db, target_u.id, user_state["username"])
                        st.success("Đã xóa người dùng! Vui lòng tải lại trang.")

        with tab_audit:
            st.subheader("Nhật ký hoạt động (100 bản ghi gần nhất)")
            logs = get_audit_logs(db)
            if logs:
                log_data = [{
                    "Thời gian": l.timestamp.strftime("%Y-%m-%d %H:%M:%S") if l.timestamp else "",
                    "Người thực hiện": l.username,
                    "Hành động": l.action_type,
                    "Chi tiết": l.details
                } for l in logs]
                st.dataframe(pd.DataFrame(log_data), use_container_width=True)
            else:
                st.info("Chưa có bản ghi nhật ký nào.")

    finally:
        db.close()

finally:
    PageLoader.empty()

