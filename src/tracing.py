"""Optional LangSmith tracing helpers with Streamlit Cloud secret support."""
import os

# LangSmith reads configuration from environment variables. Streamlit Cloud
# exposes configured values through st.secrets, so bridge them before importing
# the LangSmith decorator. Local .env loading remains handled by src.llm.
try:
    import streamlit as st

    for _key in (
        "LANGSMITH_TRACING",
        "LANGSMITH_TRACING_V2",
        "LANGSMITH_API_KEY",
        "LANGSMITH_PROJECT",
        "LANGSMITH_HIDE_INPUTS",
        "LANGSMITH_HIDE_OUTPUTS",
    ):
        _value = st.secrets.get(_key)
        if _value is not None and str(_value).strip():
            os.environ.setdefault(_key, str(_value))
except Exception:
    # Secrets are optional; tracing must never prevent the app from starting.
    pass

try:
    from langsmith import traceable
except ImportError:
    traceable = None


def traced(name=None):
    def decorator(func):
        if traceable is None:
            return func
        return traceable(name=name or func.__name__)(func)
    return decorator
