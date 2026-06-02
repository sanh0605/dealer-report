import streamlit as st
from database.gsheets_db import init_sheets
from services.identity import login

st.set_page_config(
    page_title="Dealer Report",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="auto",
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

# --- PAGE DEFINITIONS ---
login_page = st.Page(render_login_page, title="Log In", icon=":material/login:", default=("user" not in st.session_state))

# These pages are in the 'views/' directory
upload_page = st.Page("views/1_Upload.py", title="Upload dữ liệu", icon=":material/upload_file:")
sales_page = st.Page("views/2_Sales_Dashboard.py", title="Báo cáo Doanh số", icon=":material/query_stats:")
health_page = st.Page("views/3_Dealer_Health.py", title="Sức khỏe Đại lý", icon=":material/health_and_safety:")
field_page = st.Page("views/6_Field_Operations.py", title="Đi thị trường", icon=":material/location_on:")
lost_sales_page = st.Page("views/7_Lost_Sales.py", title="Cơ hội bị mất", icon=":material/trending_down:")
admin_page = st.Page("views/8_Admin.py", title="Quản trị hệ thống", icon=":material/admin_panel_settings:")
profile_page = st.Page("views/9_Profile.py", title="Thông tin cá nhân", icon=":material/person:", default=("user" in st.session_state))

# --- NAVIGATION LOGIC ---
if "user" not in st.session_state:
    # If not logged in, only show the login page
    pg = st.navigation([login_page], position="hidden") # Hide sidebar navigation when not logged in
else:
    # If logged in, show all functional pages
    pages_dict = {
        "Hệ thống": [profile_page, admin_page], # Required for routing, handled by popover menu
        "Báo cáo & Dashboard": [sales_page, health_page],
        "Dữ liệu & Vận hành": [upload_page, field_page, lost_sales_page]
    }

    # Custom sidebar navigation builder
    for section_name, pages in pages_dict.items():
        if section_name == "Hệ thống":
            continue # Skip rendering this section in the main sidebar loop
            
        st.sidebar.markdown(f"<p style='font-size: 14px; color: gray; margin-bottom: 4px; font-weight: bold;'>{section_name}</p>", unsafe_allow_html=True)
        for p in pages:
            st.sidebar.page_link(p, label=p.title, icon=p.icon)
        st.sidebar.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    user = st.session_state["user"]
    
    # Determine profile button width depending on whether the settings button is visible
    has_settings = user["role"] in ["Admin", "Manager"]
    profile_btn_width = "calc(100% - 3rem - 45px)" if has_settings else "calc(100% - 2rem)"
    
    # User Menu styling (Gemini-like side-by-side buttons anchored to absolute bottom)
    st.sidebar.markdown(
        f"""
        <style>
        /* Add padding to the scrollable content area to ensure nav items never overlap the absolute buttons */
        [data-testid="stSidebarUserContent"] {{
            padding-bottom: 6rem !important;
        }}
        
        /* Profile button container - Absolutely positioned to the bottom left */
        .st-key-user_profile_btn {{
            position: absolute !important;
            bottom: 1.5rem !important;
            left: 1rem !important;
            width: {profile_btn_width} !important;
            z-index: 100 !important;
        }}

        /* Profile button internal styling */
        .st-key-user_profile_btn button {{
            border: none !important;
            background-color: transparent !important;
            box-shadow: none !important;
            text-align: left !important;
            padding: 8px 10px 8px 5px !important;
            margin-bottom: 0 !important;
            width: 100% !important;
            display: flex !important;
            flex-direction: column !important;
            align-items: flex-start !important;
            height: auto !important;
        }}
        .st-key-user_profile_btn button:hover {{
            background-color: rgba(128, 128, 128, 0.1) !important;
            border-radius: 8px !important;
        }}
        .st-key-user_profile_btn button p {{
            font-weight: 600 !important;
            font-size: 15px !important;
            margin: 0 !important;
            padding: 0 !important;
            line-height: 1.2 !important;
        }}
        .st-key-user_profile_btn button p::after {{
            content: "{user['role']}";
            display: block !important;
            font-size: 12px !important;
            color: #888 !important;
            font-weight: 400 !important;
            margin-top: 4px !important;
        }}
        
        /* Settings button container - Absolutely positioned to the bottom right */
        .st-key-user_settings_btn {{
            position: absolute !important;
            bottom: 1.5rem !important;
            right: 1.5rem !important;
            width: 45px !important;
            z-index: 100 !important;
        }}

        /* Settings button internal styling */
        .st-key-user_settings_btn button {{
            border: none !important;
            background-color: transparent !important;
            box-shadow: none !important;
            padding: 8px !important;
            font-size: 18px !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            opacity: 0.7 !important;
            margin-bottom: 0 !important;
            height: auto !important;
        }}
        .st-key-user_settings_btn button:hover {{
            background-color: rgba(128, 128, 128, 0.1) !important;
            border-radius: 50% !important;
            opacity: 1 !important;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

    # User Menu buttons rendered directly into sidebar (styled with absolute positioning)
    if st.sidebar.button(f"{user['display_name']}", key="user_profile_btn", use_container_width=True):
        st.switch_page(profile_page)
        
    if user["role"] in ["Admin", "Manager"]:
        if st.sidebar.button("⚙️", key="user_settings_btn"):
            st.switch_page(admin_page)

    pg = st.navigation(pages_dict, position="hidden")

# Run the selected page
pg.run()
