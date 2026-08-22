from datetime import datetime
from app.database import db
from app.models.audit_log import AuditLog

def log_audit_action(user_id=None, username=None, action="", resource_type=None, resource_id=None, details=None, ip_address=None):
    """Utility helper to append structured security audit logs."""
    try:
        log_entry = AuditLog(
            user_id=user_id,
            username=username or 'System',
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id else None,
            details=details or {},
            ip_address=ip_address,
            timestamp=datetime.utcnow()
        )
        db.session.add(log_entry)
        db.session.commit()
        return log_entry
    except Exception as err:
        print(f"[Audit Log Error] Failed to log action '{action}': {err}")
        return None
