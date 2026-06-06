import streamlit as st
from passlib.context import CryptContext
import typing

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a plaintext password for storage (use offline to create secrets)."""
    return pwd_context.hash(password)


def _get_users() -> dict:
    """Read user credentials from Streamlit secrets under `credentials.users`.

    Expected structure in `st.secrets`:
    credentials:
      users:
        alice:
          name: "Alice"
          password: "$2b$..."
    """
    try:
        if "credentials" in st.secrets and "users" in st.secrets["credentials"]:
            return st.secrets["credentials"]["users"]
    except Exception:
        pass
    return {}


def verify_credentials(username: str, password: str) -> bool:
    users = _get_users()
    user = users.get(username)
    if not user:
        return False
    stored = user.get("password")
    if not stored:
        return False
    try:
        return pwd_context.verify(password, stored)
    except Exception:
        return False


def _ensure_session():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
        st.session_state["username"] = None


def login_form():
    _ensure_session()

    with st.form("login_form"):
        st.write("Please sign in to continue")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        if submitted:
            if verify_credentials(username, password):
                st.session_state["authenticated"] = True
                st.session_state["username"] = username
                st.success("Logged in")
                st.experimental_rerun()
            else:
                st.error("Invalid username or password")


def logout():
    st.session_state["authenticated"] = False
    st.session_state["username"] = None
    st.experimental_rerun()


def require_login():
    _ensure_session()
    if not st.session_state.get("authenticated"):
        login_form()
        st.stop()


def get_current_user() -> typing.Optional[str]:
    return st.session_state.get("username")
