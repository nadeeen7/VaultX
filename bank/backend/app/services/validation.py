"""
Input validation helpers shared by all routes.

The password policy is enforced ONLY when creating or changing a password:
registration, password reset, and profile change-password. Existing users are
never affected until they set a new password, so no account can be locked out
by policy changes.
"""
import re
from flask import request, jsonify

# Password policy (documented in VAULTX_PROJECT_DOCUMENTATION.md)
PASSWORD_MIN_LENGTH = 8
_RE_UPPER = re.compile(r"[A-Z]")
_RE_LOWER = re.compile(r"[a-z]")
_RE_DIGIT = re.compile(r"\d")

# Small denylist of extremely weak passwords (policy requires classes anyway,
# so these are belt-and-braces against policy-compliant junk like "Aa123456").
_WEAK_PASSWORDS = {
    "password1", "password!", "qwerty123", "letmein1", "welcome1",
    "iloveyou1", "admin123", "passw0rd", "p@ssw0rd", "abc12345",
    "aaaaaa1a", "111111a", "123456a", "dragon123", "master123",
    "aa123456", "abc123456", "a1234567", "1a2b3c4d",
}


def validate_password_policy(password: str):
    """
    Validate a NEW password against the policy.

    Returns (ok: bool, error_message: str). error_message is None when valid.
    """
    if not isinstance(password, str) or not password:
        return False, "Password is required"
    if len(password) < PASSWORD_MIN_LENGTH:
        return False, f"Password must be at least {PASSWORD_MIN_LENGTH} characters"
    if len(password) > 128:
        return False, "Password must be at most 128 characters"
    if not _RE_UPPER.search(password):
        return False, "Password must contain at least one uppercase letter"
    if not _RE_LOWER.search(password):
        return False, "Password must contain at least one lowercase letter"
    if not _RE_DIGIT.search(password):
        return False, "Password must contain at least one number"
    if password.lower() in _WEAK_PASSWORDS:
        return False, "This password is too weak or commonly used. Please choose a different one"
    return True, None


_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validate_email(email) -> bool:
    """Basic email format check: single @, non-empty local/domain, has TLD."""
    if not isinstance(email, str):
        return False
    email = email.strip()
    if not email or len(email) > 120:
        return False
    return bool(_EMAIL_RE.match(email))


def validate_username(username) -> bool:
    """3-40 chars: letters, digits, dot, dash, underscore."""
    if not isinstance(username, str):
        return False
    return bool(re.fullmatch(r"[A-Za-z0-9._-]{3,40}", username or ""))


def validate_name(name) -> bool:
    """1-60 chars, letters/spaces/hyphens/apostrophes/periods (unicode-safe)."""
    if not isinstance(name, str):
        return False
    name = name.strip()
    if not name or len(name) > 60:
        return False
    return bool(re.fullmatch(r"[\w\s.'’-]+", name, re.UNICODE))


def get_json_object():
    """
    Safely parse the request body as a JSON object.

    Returns (data, error_response). Exactly one of the two is None.
    Handles malformed JSON (silent parse) and non-object bodies.
    """
    data = request.get_json(silent=True)
    if data is None:
        return None, (jsonify({"error": "Request body must be valid JSON"}), 400)
    if not isinstance(data, dict):
        return None, (jsonify({"error": "Request body must be a JSON object"}), 400)
    return data, None


def clean_string(value, max_length: int = 255) -> str:
    """Coerce to stripped string with a hard length cap."""
    if value is None:
        return ""
    return str(value).strip()[:max_length]
