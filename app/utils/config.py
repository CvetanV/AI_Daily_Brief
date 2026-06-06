import os
from dotenv import load_dotenv

# Try to load local .env file
load_dotenv()

def get_database_url() -> str:
    # First try Streamlit secrets, then local environment variable
    try:
        import streamlit as st
        if "DATABASE_URL" in st.secrets:
            return st.secrets["DATABASE_URL"]
    except ImportError:
        pass
    except FileNotFoundError:
        pass

    return os.getenv("DATABASE_URL")

def get_gemini_api_key() -> str:
    # First try Streamlit secrets, then local environment variable
    try:
        import streamlit as st
        if "GOOGLE_API_KEY" in st.secrets:
            return st.secrets["GOOGLE_API_KEY"]
    except ImportError:
        pass
    except FileNotFoundError:
        pass

    return os.getenv("GOOGLE_API_KEY")

def get_gemini_model() -> str:
    # First try Streamlit secrets, then local environment variable
    try:
        import streamlit as st
        if "GEMINI_MODEL" in st.secrets:
            return st.secrets["GEMINI_MODEL"]
    except ImportError:
        pass
    except FileNotFoundError:
        pass

    # Default to gemini-2.5-flash if not specified
    return os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

DATABASE_URL = get_database_url()
GOOGLE_API_KEY = get_gemini_api_key()
GEMINI_MODEL = get_gemini_model()
