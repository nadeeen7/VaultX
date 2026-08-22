import threading
import requests
from datetime import datetime, timezone
from app.models import db, SecurityEvent, AuditLog, gen_uuid
from flask import request


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
        print(f"[SIEM PUSH] Error sending event to SIEM: {e}")


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
):
    """
    Log a structured security event to the database AND push to SIEM.

    This function is the centralized entry point for all security events.
    It writes to the security_events table and asynchronously sends to SIEM.
    """
    # Get context from Flask request if available
    if source_ip is None:
        try:
            source_ip = request.remote_addr
            if request.headers.get("X-Forwarded-For"):
                source_ip = request.headers["X-Forwarded-For"].split(",")[0].strip()
        except RuntimeError:
            source_ip = "unknown"

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
            metadata_json=metadata or {},
        )
        db.session.add(event)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"[SECURITY LOG ERROR] Failed to log event {event_type}: {e}")

    # Push to SIEM in background thread (non-blocking)
    siem_event = {
        'event_id': event.event_id if event else gen_uuid(),
        'source_app': 'VaultX Bank',
        'event_type': event_type,
        'status': status,
        'user_id': user_id,
        'username': username,
        'source_ip': source_ip,
        'user_agent': user_agent,
        'endpoint': endpoint,
        'http_method': http_method,
        'timestamp': (event.timestamp.isoformat() if event else datetime.now(timezone.utc).isoformat()),
        'details': metadata or {},
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
            try:
                source_ip = request.remote_addr
            except RuntimeError:
                source_ip = "unknown"

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
        print(f"[AUDIT LOG ERROR] Failed to write audit log: {e}")
        return None
