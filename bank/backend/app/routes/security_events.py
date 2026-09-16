import hmac
from flask import Blueprint, request, jsonify, current_app, g
from app.models import SecurityEvent
from app.auth import decode_token
from app.models import User

security_events_bp = Blueprint("security_events", __name__, url_prefix="/api/security-events")


def _authorize_events_access():
    """
    Authorize access to security events. Two accepted principals:

    1. The SIEM collector — Authorization: Bearer <SIEM_API_KEY> (constant-time
       compare). This preserves the existing SIEM pull integration, which sends
       exactly this header.
    2. An authenticated admin user — valid JWT whose user has role=admin.

    Returns None when authorized, otherwise (response, status_code).
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return jsonify({"error": "Authentication required"}), 401
    presented = auth_header[7:]

    # 1) SIEM collector key (constant-time comparison)
    siem_key = current_app.config.get("SIEM_API_KEY", "")
    if siem_key and hmac.compare_digest(presented, siem_key):
        return None

    # 2) Admin JWT
    try:
        data = decode_token(presented)
    except Exception:
        return jsonify({"error": "Invalid token"}), 401
    user = User.query.get(data.get("user_id"))
    if not user or not user.is_active:
        return jsonify({"error": "Invalid or inactive account"}), 401
    if user.role != "admin":
        return jsonify({"error": "Admin access required"}), 403
    g.current_user = user
    return None


@security_events_bp.route("", methods=["GET"])
def get_security_events():
    """
    Retrieve security events (restricted: SIEM collector key or admin JWT).

    Query parameters:
    - page: Page number (default: 1)
    - per_page: Results per page (default: 100, max: 1000)
    - event_type: Filter by event type (e.g., LOGIN_FAILED, TRANSFER_CREATED)
    - status: Filter by status (SUCCESS, FAILED, BLOCKED)
    - user_id: Filter by user ID
    - username: Filter by username (partial match)
    - source_ip: Filter by source IP
    - start_time: ISO 8601 timestamp for start of range
    - end_time: ISO 8601 timestamp for end of range
    """
    auth_error = _authorize_events_access()
    if auth_error is not None:
        return auth_error

    page = max(request.args.get("page", 1, type=int) or 1, 1)
    per_page = min(max(request.args.get("per_page", 100, type=int) or 100, 1), 1000)
    event_type = request.args.get("event_type")
    status = request.args.get("status")
    user_id = request.args.get("user_id")
    username = request.args.get("username")
    source_ip = request.args.get("source_ip")
    start_time = request.args.get("start_time")
    end_time = request.args.get("end_time")

    query = SecurityEvent.query

    if event_type:
        query = query.filter(SecurityEvent.event_type == event_type)
    if status:
        query = query.filter(SecurityEvent.status == status)
    if user_id:
        query = query.filter(SecurityEvent.user_id == user_id)
    if username:
        query = query.filter(SecurityEvent.username.ilike(f"%{username}%"))
    if source_ip:
        query = query.filter(SecurityEvent.source_ip == source_ip)
    if start_time:
        try:
            from datetime import datetime
            st = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
            query = query.filter(SecurityEvent.timestamp >= st)
        except (ValueError, AttributeError):
            pass
    if end_time:
        try:
            from datetime import datetime
            et = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
            query = query.filter(SecurityEvent.timestamp <= et)
        except (ValueError, AttributeError):
            pass

    pagination = query.order_by(SecurityEvent.timestamp.desc()) \
        .paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "events": [e.to_dict() for e in pagination.items],
        "total": pagination.total,
        "page": pagination.page,
        "per_page": pagination.per_page,
        "pages": pagination.pages,
    }), 200
