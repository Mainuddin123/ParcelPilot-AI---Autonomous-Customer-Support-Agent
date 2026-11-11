"""Optional LangSmith tracing helpers.

Tracing remains disabled unless LANGSMITH_TRACING=true and a valid
LANGSMITH_API_KEY is configured in the environment.
"""
from functools import wraps
import os

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
