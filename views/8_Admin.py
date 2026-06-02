from components.ui_utils import show_centered_loader
PageLoader = show_centered_loader()
import streamlit as st
import pandas as pd
from database.gsheets_db import read_sheet
from services.identity import (
    require_role, create_user, update_user, delete_user, get_audit_logs, change_password
)

@st.dialog("Tạo người dùng mới")
def show_create_user_dialog(manageable_roles, current_username):
    with st.form("create_user_form", clear_on_submit=True):
        new_username = st.text_input("Tên đăng nhập")
        new_password = st.text_input("Mật khẩu", type="password")
        new_role = st.selectbox("Vai trò", manageable_roles)
        new_display_name = st.text_input("Tên hiển thị")
        submitted_create = st.form_submit_button("Tạo mới", use_container_width=True)
        
    if submitted_create:
        if len(new_password) < 8:
            st.error("Mật khẩu phải có ít nhất 8 ký tự.")
        elif not new_username or not new_display_name:
            st.error("Vui lòng điền đầy đủ thông tin.")
        else:
            try:
                # Check for duplicate locally before calling service
                users_df = read_sheet("users", ttl=0)
                if not users_df.empty and new_username in users_df['username'].values:
                    st.error("Tên đăng nhập đã tồn tại.")
                else:
                    create_user(None, new_username, new_password, new_role, new_display_name, current_username)
                    st.success("Tạo người dùng thành công!")
                    st.session_state.admin_editor_key += 1
                    st.rerun()
            except Exception as e:
                st.error(f"Lỗi: {e}")

@st.dialog("Xác nhận Xóa")
def confirm_delete_dialog(users_to_delete, edits_to_apply):
    st.warning(f"Bạn có chắc chắn muốn xóa {len(users_to_delete)} người dùng này không?")
    for u in users_to_delete:
        st.write(f"- {u['username']}")
    
    if st.button("Xác nhận Xóa & Lưu Thay Đổi", type="primary"):
        try:
            # execute deletions
            for u in users_to_delete:
                delete_user(None, u['id'], st.session_state["user"]["username"])
            # execute edits
            for e in edits_to_apply:
                update_user(None, e['id'], e['role'], e['display_name'], st.session_state["user"]["username"])
                
            st.success("Thao tác thành công!")
            st.session_state.admin_editor_key += 1
            st.rerun()
        except Exception as err:
            st.error(f"Lỗi khi lưu thay đổi: {err}")

@st.dialog("Đổi mật khẩu")
def reset_password_dialog(manageable_users):
    user_options = {u['username']: u['id'] for _, u in manageable_users.iterrows()}
    if not user_options:
        st.info("Không có người dùng nào.")
        return
        
    selected_username = st.selectbox("Chọn người dùng", list(user_options.keys()))
    new_password = st.text_input("Mật khẩu mới", type="password")
    
    if st.button("Cập nhật mật khẩu", type="primary"):
        if len(new_password) < 8:
            st.error("Mật khẩu phải có ít nhất 8 ký tự.")
        else:
            try:
                change_password(None, user_options[selected_username], new_password, st.session_state["user"]["username"])
                st.success(f"Đã cập nhật mật khẩu cho {selected_username}.")
            except Exception as e:
                st.error(f"Lỗi: {e}")

try:
    if "user" not in st.session_state:
        st.error("Vui lòng đăng nhập.")
        st.stop()
        
    user_state = st.session_state["user"]
    try:
        # Allow both Admin and Manager access
        require_role(user_state, ["Admin", "Manager"])
    except PermissionError:
        st.error("Bạn không có quyền truy cập trang này.")
        PageLoader.empty()
        st.stop()

    if "admin_editor_key" not in st.session_state:
        st.session_state.admin_editor_key = 0

    st.title("⚙️ Bảng điều khiển Quản trị")

    tab_users, tab_audit = st.tabs(["Quản lý Người dùng", "Nhật ký Hệ thống (Audit)"])

    # Load users from Google Sheets
    users_df = read_sheet("users", ttl=0)
    
    # Determine manageable roles and users
    if user_state["role"] == "Admin":
        manageable_roles = ["Admin", "Manager", "Sales Staff"]
        manageable_users_df = users_df.copy() if not users_df.empty else pd.DataFrame()
    else: # Manager
        manageable_roles = ["Sales Staff"]
        if not users_df.empty:
            manageable_users_df = users_df[users_df["role"].isin(manageable_roles)].copy()
        else:
            manageable_users_df = pd.DataFrame()
    
    with tab_users:
        # Header Row with global Actions (Outside form)
        col_create, col_pw, col_spacer = st.columns([1, 1.2, 2.3])
        
        with col_create:
            if st.button("➕ Tạo người dùng", type="secondary", use_container_width=True):
                show_create_user_dialog(manageable_roles, user_state["username"])
                
        with col_pw:
            if st.button("🔑 Đổi mật khẩu", type="secondary", use_container_width=True):
                reset_password_dialog(manageable_users_df)
        
        st.write("") # Spacer

        # Data Editor Setup
        if not manageable_users_df.empty:
            df_edit = manageable_users_df[["id", "username", "role", "display_name"]].copy()
            df_edit["is_deleted"] = False # Checkbox for deletion
            
            # Reorder columns to put delete checkbox last
            cols = ["username", "role", "display_name", "is_deleted", "id"]
            df_edit = df_edit[cols]
            
            editor_key = f"user_editor_{st.session_state.admin_editor_key}"
            
            with st.form(f"form_{editor_key}", border=False):
                edited_df = st.data_editor(
                    df_edit,
                    key=editor_key,
                    num_rows="fixed", # Disallow adding rows
                    height=400, # Approx 10 rows scrollable
                    use_container_width=True,
                    column_config={
                        "id": None, # Hide internal ID
                        "is_deleted": st.column_config.CheckboxColumn("Xoá?", default=False),
                        "username": st.column_config.TextColumn("Tên đăng nhập", disabled=True),
                        "role": st.column_config.SelectboxColumn("Vai trò", options=manageable_roles, required=True),
                        "display_name": st.column_config.TextColumn("Tên hiển thị", required=True)
                    }
                )

                st.write("") # Spacer
                # Actions inside form (at the bottom)
                col_f_space, col_confirm, col_cancel = st.columns([4, 1, 1])
                with col_confirm:
                    btn_confirm = st.form_submit_button("Xác nhận", type="primary", use_container_width=True)
                with col_cancel:
                    btn_cancel = st.form_submit_button("Huỷ", use_container_width=True)
            
            if btn_cancel:
                st.session_state.admin_editor_key += 1
                st.rerun()

            # Logic for Confirm button
            if btn_confirm:
                users_to_delete = []
                edits_to_apply = []
                
                for _, row in edited_df.iterrows():
                    user_id = str(row["id"])
                    username = row["username"]
                    
                    if row["is_deleted"]:
                        if username == user_state["username"]:
                            st.error(f"Không thể xoá tài khoản đang đăng nhập ({username}).")
                        else:
                            users_to_delete.append({"id": user_id, "username": username})
                        continue
                        
                    # Reliable lookup using ID instead of index
                    orig_row_matches = df_edit[df_edit["id"] == user_id]
                    if orig_row_matches.empty:
                        continue
                    orig_row = orig_row_matches.iloc[0]
                    
                    # Check for Edits
                    if row["role"] != orig_row["role"] or row["display_name"] != orig_row["display_name"]:
                        edits_to_apply.append({
                            "id": user_id,
                            "role": row["role"],
                            "display_name": row["display_name"]
                        })
                
                if users_to_delete:
                    confirm_delete_dialog(users_to_delete, edits_to_apply)
                elif edits_to_apply:
                    try:
                        for e in edits_to_apply:
                            update_user(None, e["id"], e["role"], e["display_name"], user_state["username"])
                        st.success("Đã cập nhật thay đổi thành công!")
                        st.session_state.admin_editor_key += 1
                        st.rerun()
                    except Exception as e:
                        st.error(f"Lỗi: {e}")
                else:
                    st.info("Không có thay đổi nào để lưu.")
        else:
            st.info("Không có người dùng nào trong phạm vi quản lý của bạn.")

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
