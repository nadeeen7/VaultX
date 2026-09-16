import threading
import requests
from datetime import datetime, timezone
from app.models import db, SecurityEvent, AuditLog, gen_uuid
from flask import request

# ──────────────────────────────────────────────────
# Severity classification (centralized — call sites pass only event_type)
# ──────────────────────────────────────────────────
EVENT_SEVERITY = {
    # Authentication
    "LOGIN_SUCCESS": "LOW",
    "LOGIN_FAILED": "MEDIUM",
    "LOGOUT": "LOW",
    "ACCOUNT_LOCKED": "HIGH",
    "BRUTE_FORCE_ATTEMPT": "HIGH",
    # Google authentication
    "GOOGLE_LOGIN_SUCCESS": "LOW",
    "GOOGLE_LOGIN_FAILED": "MEDIUM",
    # Password / OTP
    "PASSWORD_RESET_REQUESTED": "LOW",
    "PASSWORD_RESET_REQUEST": "LOW",
    "PASSWORD_RESET_COMPLETED": "LOW",
    "PASSWORD_RESET_SUCCESS": "LOW",
    "OTP_REQUEST": "LOW",
    "OTP_VERIFIED": "LOW",
    "OTP_VERIFICATION_FAILED": "MEDIUM",
    "OTP_EXPIRED": "MEDIUM",
    "OTP_RESET_SUCCESS": "LOW",
    "PASSWORD_CHANGE": "LOW",
    "PASSWORD_CHANGE_FAILED": "MEDIUM",
    "ACCOUNT_CREATED": "LOW",
    # Authorization
    "UNAUTHORIZED_ACCESS": "HIGH",
    # Suspicious activity
    "SUSPICIOUS_REQUEST": "MEDIUM",
    "SUSPICIOUS_INPUT": "MEDIUM",
    "RATE_LIMIT_EXCEEDED": "MEDIUM",
    # Transactions
    "TRANSFER_CREATED": "LOW",
    "TRANSFER_FAILED": "MEDIUM",
    # Admin
    "ADMIN_LOGIN": "LOW",
    "ADMIN_LOGIN_FAILED": "HIGH",
}

SEVERITY_ORDER = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}

# Keys that must never appear in event metadata. Acts as a final safety net if
# a call site passes user-controlled or secret data by mistake.
_FORBIDDEN_META_KEYS = {
    "password", "new_password", "confirm_password", "current_password",
    "password_hash", "otp", "otp_code", "otp_hash", "reset_token",
    "credential", "id_token", "token", "access_token", "refresh_token",
    "authorization", "jwt", "secret", "api_key", "database_url", "mail_password",
}


def _redact_metadata(metadata: dict) -> dict:
    """Remove forbidden keys from metadata before it is stored or pushed to SIEM."""
    if not isinstance(metadata, dict):
        return {}
    safe = {}
    for key, value in metadata.items():
        key_lower = str(key).lower()
        if key_lower in _FORBIDDEN_META_KEYS or "password" in key_lower or "token" in key_lower or "secret" in key_lower:
            continue  # drop rather than log: safest failure mode
        if isinstance(value, dict):
            safe[key] = _redact_metadata(value)
        else:
            safe[key] = value
    return safe


def _get_trusted_client_ip() -> str:
    """
    Get the client IP, honoring the app-wide TRUST_PROXY setting.

    Behind Render (or any reverse proxy) remote_addr is the proxy, so the real
    client IP must come from X-Forwarded-For. Only trust forwarded headers when
    TRUST_PROXY=true is configured, to prevent header spoofing when exposed.
    Safe to call outside a request context (returns "unknown").
    """
    try:
        from flask import current_app
        try:
            trust_proxy = current_app.config.get("TRUST_PROXY", False)
        except RuntimeError:
            trust_proxy = False

        if trust_proxy:
            forwarded = request.headers.get("X-Forwarded-For")
            if forwarded:
                # First entry = original client (Render appends proxies at the end)
                return forwarded.split(",")[0].strip()
            real_ip = request.headers.get("X-Real-IP")
            if real_ip:
                return real_ip.strip()

        return request.remote_addr or "unknown"
    except RuntimeError:
        return "unknown"


def _send_event_to_siem(event_data):
    """
    Background thread function to send a security event to the SIEM backend.
    This is non-blocking - failures don't affect the Bank application.
    """
    try:
        from flask import current_app
        siem_url = current_app.config.get('SIEM_API_URL')
        siem_key = current_app.config.get('SIEM_API_KEY')

        if not siem_url or not siem_key:
            return  # SIEM not configured, skip

        headers = {
            'Content-Type': 'application/json',
            'X-API-Key': siem_key,
        }

        resp = requests.post(
            f"{siem_url}/api/events",
            json=event_data,
            headers=headers,
            timeout=5.0,
        )

        if resp.status_code not in (200, 201, 204):
            print(f"[SIEM PUSH] Failed to send event to SIEM: HTTP {resp.status_code}")
    except requests.exceptions.ConnectionError:
        # SIEM might be offline - this is expected during development
        pass
    except Exception as e:
        print(f"[SIEM PUSH] Error sending event to SIEM: {type(e).__name__}")


def log_security_event(
    event_type: str,
    status: str,
    user_id: str = None,
    username: str = None,
    source_ip: str = None,
    user_agent: str = None,
    endpoint: str = None,
    http_method: str = None,
    metadata: dict = None,
    severity: str = None,
    target: str = None,
):
    """
    Log a structured security event to the database AND push to SIEM.

    This function is the centralized entry point for all security events.
    It writes to the security_events table and asynchronously sends to SIEM.

    Severity is derived automatically from event_type (EVENT_SEVERITY map)
    unless explicitly overridden. `target` classifies the resource under
    attack/observation (LOGIN, OTP, TRANSACTION, ADMIN, ...). Never include
    passwords, OTP values, tokens, or other secrets in `metadata` — they are
    redacted as a safety net, but do not rely on that.
    """
    # Get context from Flask request if available
    if source_ip is None:
        source_ip = _get_trusted_client_ip()

    if user_agent is None:
        try:
            user_agent = request.headers.get("User-Agent", "unknown")
        except RuntimeError:
            user_agent = "unknown"

    if endpoint is None:
        try:
            endpoint = request.path
        except RuntimeError:
            endpoint = "unknown"

    if http_method is None:
        try:
            http_method = request.method
        except RuntimeError:
            http_method = "unknown"

    # Severity: explicit override wins; else map; else LOW.
    if severity is None:
        severity = EVENT_SEVERITY.get(event_type, "LOW")
    if severity not in SEVERITY_ORDER:
        severity = "LOW"

    # Final safety net: strip any forbidden keys from metadata.
    safe_metadata = _redact_metadata(metadata or {})

    # Save to local database
    event = None
    try:
        event = SecurityEvent(
            event_id=gen_uuid(),
            timestamp=datetime.now(timezone.utc),
            event_type=event_type,
            user_id=user_id,
            username=username,
            source_ip=source_ip,
            user_agent=user_agent,
            endpoint=endpoint,
            http_method=http_method,
            status=status,
            severity=severity,
            target=target,
            metadata_json=safe_metadata,
        )
        db.session.add(event)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"[SECURITY LOG ERROR] Failed to log event {event_type}: {type(e).__name__}")

    # Push to SIEM in background thread (non-blocking)
    siem_event = {
        'event_id': event.event_id if event else gen_uuid(),
        'source_app': 'VaultX Bank',
        'event_type': event_type,
        'status': status,
        'severity': severity,
        'target': target,
        'user_id': user_id,
        'username': username,
        'source_ip': source_ip,
        'user_agent': user_agent,
        'endpoint': endpoint,
        'http_method': http_method,
        'timestamp': (event.timestamp.isoformat() if event else datetime.now(timezone.utc).isoformat()),
        'details': safe_metadata,
    }

    thread = threading.Thread(target=_send_event_to_siem, args=(siem_event,), daemon=True)
    thread.start()

    return event


def log_audit(
    action: str,
    resource_type: str,
    resource_id: str = None,
    user_id: str = None,
    details: dict = None,
    source_ip: str = None,
):
    """
    Log an audit trail entry.
    """
    try:
        if source_ip is None:
            source_ip = _get_trusted_client_ip()

        log = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
            source_ip=source_ip,
        )
        db.session.add(log)
        db.session.commit()
        return log
    except Exception as e:
        db.session.rollback()
        print(f"[AUDIT LOG ERROR] Failed to write audit log: {type(e).__name__}")
        return None
