import streamlit as st
from passlib.context import CryptContext
import typing
import os
import uuid
import requests
from urllib.parse import urlencode

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _rerun():
    """Safely request a rerun across Streamlit versions by nudging a query param.

    We avoid raising internal exceptions directly; instead set a unique
    query param and stop, which forces the client to reload the app state.
    """
    try:
        rerun = getattr(st, "experimental_rerun", None)
        if callable(rerun):
            return rerun()
    except Exception:
        pass

    try:
        st.experimental_set_query_params(_reload=str(uuid.uuid4()))
    except Exception:
        try:
            st.experimental_set_query_params()
        except Exception:
            pass
    st.stop()


# Default auth mode
DEFAULT_AUTH_MODE = "local"  # options: simple, local, oauth


def get_auth_mode() -> str:
    try:
        if "AUTH_MODE" in st.secrets:
            return str(st.secrets["AUTH_MODE"]).lower()
    except Exception:
        pass
    return os.getenv("AUTH_MODE", DEFAULT_AUTH_MODE).lower()


def get_app_password() -> typing.Optional[str]:
    try:
        if "APP_PASSWORD" in st.secrets:
            return st.secrets["APP_PASSWORD"]
    except Exception:
        pass
    return os.getenv("APP_PASSWORD")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def _get_users() -> dict:
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
    """Render the login controls in the sidebar. Hidden when authenticated."""
    _ensure_session()

    # Simple mode doesn't use per-user login form; show OAuth link if present
    if get_auth_mode() == "simple":
        oauth_client = _get_oauth_config()
        if oauth_client and oauth_client.get("client_id"):
            auth_url = build_google_auth_url(oauth_client)
            st.sidebar.markdown(f"[Sign in with Google]({auth_url})")
        return

    # Sidebar per-user login
    with st.sidebar.form("login_form"):
        st.sidebar.write("Please sign in to continue")
        username = st.sidebar.text_input("Username")
        password = st.sidebar.text_input("Password", type="password")
        submitted = st.sidebar.form_submit_button("Login")
        if submitted:
            if verify_credentials(username, password):
                st.session_state["authenticated"] = True
                st.session_state["username"] = username
                st.sidebar.success("Logged in")
                return
            else:
                st.sidebar.error("Invalid username or password")

    oauth_client = _get_oauth_config()
    if oauth_client and oauth_client.get("client_id"):
        auth_url = build_google_auth_url(oauth_client)
        st.sidebar.markdown(f"[Sign in with Google]({auth_url})")


def logout():
    st.session_state["authenticated"] = False
    st.session_state["username"] = None
    _rerun()


def require_login():
    """Enforce authentication. When not authenticated, show sidebar login and stop."""
    _ensure_session()
    mode = get_auth_mode()

    if mode == "simple":
        if not st.session_state.get("authenticated"):
            st.sidebar.write("Enter application password to continue")
            pwd = st.sidebar.text_input("Password", type="password", key="_simple_pwd")
            if st.sidebar.button("Enter", key="_simple_enter"):
                app_pwd = get_app_password()
                if not app_pwd:
                    st.sidebar.error("APP_PASSWORD is not configured in secrets or environment.")
                elif pwd == app_pwd:
                    st.session_state["authenticated"] = True
                    st.session_state["username"] = "app_user"
                    st.sidebar.success("Authenticated")
                    return
                else:
                    st.sidebar.error("Invalid password")
            st.stop()

    # Default/local mode: show sidebar login (or OAuth) and stop
    if not st.session_state.get("authenticated"):
        login_form()
        st.stop()


def get_current_user() -> typing.Optional[str]:
    return st.session_state.get("username")


def _get_oauth_config():
    try:
        if "oauth" in st.secrets:
            cfg = st.secrets["oauth"]
            return {
                "client_id": cfg.get("client_id"),
                "client_secret": cfg.get("client_secret"),
                "redirect_uri": cfg.get("redirect_uri"),
            }
    except Exception:
        pass

    return {
        "client_id": os.getenv("GOOGLE_OAUTH_CLIENT_ID"),
        "client_secret": os.getenv("GOOGLE_OAUTH_CLIENT_SECRET"),
        "redirect_uri": os.getenv("OAUTH_REDIRECT_URI"),
    }


def build_google_auth_url(cfg: dict) -> str:
    state = str(uuid.uuid4())
    st.session_state["oauth_state"] = state
    params = {
        "client_id": cfg.get("client_id"),
        "response_type": "code",
        "scope": "openid email profile",
        "redirect_uri": cfg.get("redirect_uri"),
        "state": state,
        "access_type": "offline",
        "prompt": "select_account consent",
    }
    return f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"


def handle_oauth_callback():
    params = {}
    try:
        params = st.experimental_get_query_params()
    except Exception:
        return

    if "code" not in params:
        return

    code = params.get("code")[0]
    state = params.get("state", [None])[0]
    if not state or state != st.session_state.get("oauth_state"):
        st.error("OAuth state mismatch")
        return

    cfg = _get_oauth_config()
    token_endpoint = "https://oauth2.googleapis.com/token"
    data = {
        "code": code,
        "client_id": cfg.get("client_id"),
        "client_secret": cfg.get("client_secret"),
        "redirect_uri": cfg.get("redirect_uri"),
        "grant_type": "authorization_code",
    }

    try:
        resp = requests.post(token_endpoint, data=data, timeout=10)
        resp.raise_for_status()
        token_data = resp.json()
        access_token = token_data.get("access_token")
        if not access_token:
            st.error("Failed to obtain access token from provider")
            return

        userinfo = requests.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
        ).json()

        email = userinfo.get("email")
        name = userinfo.get("name") or email

        st.session_state["authenticated"] = True
        st.session_state["username"] = email or name

        try:
            st.experimental_set_query_params()
        except Exception:
            pass
        _rerun()

    except Exception as e:
        st.error(f"OAuth callback error: {e}")
        return
