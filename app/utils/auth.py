import streamlit as st
from passlib.context import CryptContext
import typing
import os
import uuid
import requests
from urllib.parse import urlencode

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Default auth mode: 'local' uses per-user credentials, 'simple' uses APP_PASSWORD,
# 'oauth' can be used when OAuth config is present. Environment/secrets override.
DEFAULT_AUTH_MODE = "local"


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

    # If simple mode is active, skip the per-user login form
    if get_auth_mode() == "simple":
        return

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

    # Offer Google OAuth if configured
    oauth_client = _get_oauth_config()
    if oauth_client and oauth_client.get("client_id"):
        auth_url = build_google_auth_url(oauth_client)
        st.markdown(f"[Sign in with Google]({auth_url})")


def logout():
    st.session_state["authenticated"] = False
    st.session_state["username"] = None
    st.experimental_rerun()


def require_login():
    _ensure_session()
    mode = get_auth_mode()

    # Simple app password mode
    if mode == "simple":
        if not st.session_state.get("authenticated"):
            with st.form("simple_login_form"):
                st.write("Enter application password to continue")
                pwd = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Enter")
                if submitted:
                    app_pwd = get_app_password()
                    if not app_pwd:
                        st.error("APP_PASSWORD is not configured in secrets or environment.")
                    elif pwd == app_pwd:
                        st.session_state["authenticated"] = True
                        st.session_state["username"] = "app_user"
                        st.success("Authenticated")
                        st.experimental_rerun()
                    else:
                        st.error("Invalid password")
            st.stop()

    # Default/local mode: show login form (and OAuth if configured)
    if not st.session_state.get("authenticated"):
        login_form()
        st.stop()


def get_current_user() -> typing.Optional[str]:
    return st.session_state.get("username")


def _get_oauth_config():
    """Return OAuth client config from Streamlit secrets or environment."""
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
    """Check current URL for OAuth callback params and perform token exchange.

    Call this early in your app (before require_login) so the callback can finish
    the sign-in flow and set `st.session_state['authenticated']`.
    """
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

        # Fetch user info
        userinfo = requests.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
        ).json()

        email = userinfo.get("email")
        name = userinfo.get("name") or email

        st.session_state["authenticated"] = True
        st.session_state["username"] = email or name

        # Clear query params to avoid re-running callback
        st.experimental_set_query_params()
        st.experimental_rerun()

    except Exception as e:
        st.error(f"OAuth callback error: {e}")
        return

