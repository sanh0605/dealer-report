import streamlit as st
from database.session import init_db, get_db
from services.identity import login
from database.models import User

st.set_page_config(
    page_title="Dealer Report",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_db()

def _render_login():
    """Render login page when user is not authenticated"""
    st.title("Dealer Report System")
    st.subheader("Sign In")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign In")
    if submitted:
        db = get_db()
        try:
            user = login(db, username, password)
        finally:
            db.close()
        if user:
            st.session_state["user"] = {
                "username": user.username,
                "role": user.role,
                "display_name": user.display_name,
            }
            st.rerun()
        else:
            st.error("Invalid username or password.")

if "user" not in st.session_state:
    _render_login()
else:
    user = st.session_state["user"]
    st.sidebar.success(f"Signed in as **{user['display_name']}** ({user['role']})")
    if st.sidebar.button("Sign Out"):
        del st.session_state["user"]
        st.rerun()
    st.title("📊 Dealer Report — Dashboard")
    st.info("Use → sidebar to navigate to a module.")
