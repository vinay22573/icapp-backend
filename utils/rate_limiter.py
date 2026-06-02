import time
import threading
from collections import deque
from functools import wraps
from flask import request, jsonify

# In-memory store: key -> deque[timestamps]
_RATE_STORE = {}
_RATE_LOCK = threading.Lock()

def _now():
    return time.time()

def is_rate_limited(key: str, limit: int, period: float) -> bool:
    """Sliding window: return True if key has reached limit within period."""
    now = _now()
    with _RATE_LOCK:
        dq = _RATE_STORE.get(key)
        if dq is None:
            dq = deque()
            _RATE_STORE[key] = dq
        # Remove old timestamps
        while dq and dq[0] <= now - period:
            dq.popleft()
        if len(dq) >= limit:
            return True
        dq.append(now)
        return False

def rate_limit(limit: int = 60, period: float = 60.0, key_func=None):
    """
    Decorator to rate-limit requests.
    - `limit`: max requests
    - `period`: seconds window
    - `key_func`: optional callable that returns a string key (e.g. token); default falls back to Authorization token then IP.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                key = None
                if key_func:
                    key = key_func()
                if not key:
                    auth = request.headers.get("Authorization", "")
                    parts = auth.split()
                    if len(parts) == 2 and parts[0].lower() == "bearer":
                        key = parts[1]
                    else:
                        key = request.remote_addr or "unknown"
                if is_rate_limited(key, limit, period):
                    return jsonify({
                        "error": "rate_limited",
                        "message": f"Rate limit exceeded ({limit} requests per {period} seconds)."
                    }), 429
            except Exception:
                # On any internal error, do not block the request; log in production.
                pass
            return func(*args, **kwargs)
        return wrapper
    return decorator