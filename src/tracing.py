"""Optional LangSmith tracing helpers."""
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
