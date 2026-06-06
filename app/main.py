import streamlit as st

st.set_page_config(
    page_title="AI Daily Brief",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed" # Better for mobile
)

# Custom CSS for better mobile responsiveness
st.markdown("""
<style>
    /* Make block containers responsive */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        padding-left: 1rem;
        padding-right: 1rem;
    }
    
    /* Adjust text sizes for smaller screens */
    @media (max-width: 768px) {
        h1 { font-size: 1.8rem !important; }
        h2 { font-size: 1.5rem !important; }
        h3 { font-size: 1.2rem !important; }
        .stMarkdown { font-size: 0.95rem; }
    }
</style>
""", unsafe_allow_html=True)

# Require authentication before showing navigation
try:
    # Prefer package import (works when running from project root)
    from app.utils import auth
except Exception:
    import sys, os
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from app.utils import auth

auth.require_login()

# App Navigation
pg = st.navigation([
    st.Page("dashboard/home.py", title="Home", icon="🏠"),
    st.Page("dashboard/news.py", title="News Explorer", icon="📰"),
    st.Page("dashboard/trends.py", title="Trends", icon="📈"),
    st.Page("dashboard/tools.py", title="Resources & Tools", icon="🛠️"),
])

pg.run()
