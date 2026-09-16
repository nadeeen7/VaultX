"""
In-memory sliding-window rate limiter for authentication endpoints.

Scope (deliberate):
- Protects only the sensitive auth endpoints (login, register, google,
  forgot/reset password). The rest of the app is NOT rate-limited, so
  legitimate banking traffic is unaffected.
- Storage is per-process memory. With gunicorn's 2 workers each worker has its
  own window, so effective limits are (limit x workers). This is acceptable for
  brute-force dampening; a Redis-backed limiter can replace this later without
  changing call sites.

Not keyed on spoofable headers: the client IP comes from get_client_ip(), which
only honors X-Forwarded-For when TRUST_PROXY=true is configured.
"""
import time
import threading
from collections import defaultdict, deque
from functools import wraps
from flask import request, jsonify
from app.auth import get_client_ip
from app.logging.security_logger import log_security_event


class _SlidingWindow:
    """Fixed-size deque of timestamps with thread-safe count + prune."""

    __slots__ = ("hits", "lock")

    def __init__(self):
        self.hits = deque()
        self.lock = threading.Lock()

    def prune(self, window_start: float):
        while self.hits and self.hits[0] <= window_start:
            self.hits.popleft()

    def append(self, ts: float):
        self.hits.append(ts)


_windows = defaultdict(_SlidingWindow)
_lock = threading.Lock()


def _key(scope: str) -> str:
    """Composite key: scope + client IP (+ email/username from body when available)."""
    parts = [scope, get_client_ip()]
    if request.is_json:
        data = request.get_json(silent=True)
        if isinstance(data, dict):
            ident = data.get("email") or data.get("username")
            if isinstance(ident, str) and ident:
                parts.append(ident.strip().lower()[:120])
    return "|".join(parts)


def check_rate_limit(scope: str, max_requests: int, window_seconds: int) -> bool:
    """
    Check (and record) a request against the sliding window for `scope`.

    Returns True if allowed, False if the limit is exceeded.
    """
    now = time.monotonic()
    key = _key(scope)
    with _lock:
        win = _windows[key]
        with win.lock:
            win.prune(now - window_seconds)
            if len(win.hits) >= max_requests:
                return False
            win.append(now)
    return True


def rate_limit(scope: str, max_requests: int, window_seconds: int,
               event_type: str = "RATE_LIMIT_EXCEEDED", target: str = "LOGIN"):
    """
    Decorator factory for auth endpoints. Returns 429 + safe message when the
    limit is exceeded, and logs a security event (no secrets, no credentials).
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if not check_rate_limit(scope, max_requests, window_seconds):
                log_security_event(
                    event_type=event_type,
                    status="BLOCKED",
                    source_ip=get_client_ip(),
                    endpoint=request.path,
                    http_method=request.method,
                    metadata={"scope": scope},
                    target=target,
                    severity="MEDIUM",
                )
                return jsonify({
                    "error": "Too many requests. Please wait a moment and try again."
                }), 429
            return f(*args, **kwargs)
        return wrapper
    return decorator
