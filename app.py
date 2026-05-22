import streamlit as st
from database.gsheets_db import init_sheets
from services.identity import login

st.set_page_config(
    page_title="Dealer Report",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize Google Sheets structure if needed
init_sheets()

def render_login_page():
    """Render the login form as the main entry point"""
    st.title("Dealer Report System")
    st.subheader("Sign In")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign In")
    if submitted:
        # DB session is no longer needed as services handle connection
        user = login(None, username, password)
        if user:
            st.session_state["user"] = {
                "username": user.username,
                "role": user.role,
                "display_name": user.display_name,
            }
            st.success(f"Welcome, {user.display_name}!")
            st.rerun()
        else:
            st.error("Invalid username or password.")

def render_logout():
    """Render sign out button and info in sidebar"""
    user = st.session_state["user"]
    st.sidebar.markdown(f"**Signed in as:**  \n{user['display_name']} ({user['role']})")
    if st.sidebar.button("Sign Out"):
        del st.session_state["user"]
        st.rerun()

# --- PAGE DEFINITIONS ---
login_page = st.Page(render_login_page, title="Log In", icon=":material/login:", default=True)

# These pages are in the 'views/' directory
upload_page = st.Page("views/1_Upload.py", title="Upload dữ liệu", icon=":material/upload_file:")
sales_page = st.Page("views/2_Sales_Dashboard.py", title="Báo cáo Doanh số", icon=":material/query_stats:")
health_page = st.Page("views/3_Dealer_Health.py", title="Sức khỏe Đại lý", icon=":material/health_and_safety:")
field_page = st.Page("views/6_Field_Operations.py", title="Đi thị trường", icon=":material/location_on:")
lost_sales_page = st.Page("views/7_Lost_Sales.py", title="Cơ hội bị mất", icon=":material/trending_down:")
admin_page = st.Page("views/8_Admin.py", title="Quản trị hệ thống", icon=":material/admin_panel_settings:")
profile_page = st.Page("views/9_Profile.py", title="Thông tin cá nhân", icon=":material/person:")

# --- NAVIGATION LOGIC ---
if "user" not in st.session_state:
    # If not logged in, only show the login page
    pg = st.navigation([login_page], position="hidden") # Hide sidebar navigation when not logged in
else:
    # If logged in, show all functional pages
    render_logout()
    pg = st.navigation({
        "Báo cáo & Dashboard": [sales_page, health_page],
        "Dữ liệu & Vận hành": [upload_page, field_page, lost_sales_page],
        "Hệ thống": [profile_page, admin_page]
    })

# Run the selected page
pg.run()
