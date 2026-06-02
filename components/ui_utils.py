import streamlit as st

def get_loader_html() -> str:
    """Returns the HTML/CSS for a centered loading spinner."""
    return """
        <style>
        .centered-loader-wrapper {
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background-color: rgba(255, 255, 255, 0.7);
            z-index: 9999;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            pointer-events: all;
        }
        .spinner {
            width: 50px;
            height: 50px;
            border: 5px solid #f3f3f3;
            border-top: 5px solid #2563EB;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        </style>
        <div class="centered-loader-wrapper">
            <div class="spinner"></div>
            <p style="margin-top: 10px; font-family: sans-serif; color: #666; font-weight: bold;">Đang tải...</p>
        </div>
    """

def show_centered_loader() -> st.empty:
    """
    Initializes a centered loader and returns the placeholder object.
    Usage:
        loader = show_centered_loader()
        ... page code ...
        loader.empty()
    """
    placeholder = st.empty()
    placeholder.markdown(get_loader_html(), unsafe_allow_html=True)
    return placeholder

import base64
import streamlit.components.v1 as components

def auto_download_file(file_bytes: bytes, file_name: str, mime_type: str):
    """
    Forces an immediate download of a file in the user's browser without requiring a second click.
    Useful for heavy files generated inside a st.button() callback.
    """
    b64 = base64.b64encode(file_bytes).decode()
    href = f'<a id="auto_dl" href="data:{mime_type};base64,{b64}" download="{file_name}">DL</a>'
    js = f"{href}<script>document.getElementById('auto_dl').click();</script>"
    components.html(js, height=0)
