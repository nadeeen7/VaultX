from flask import Blueprint, request, jsonify
from app.models import SecurityEvent

security_events_bp = Blueprint("security_events", __name__, url_prefix="/api/security-events")


@security_events_bp.route("", methods=["GET"])
def get_security_events():
    """
    Public endpoint to retrieve security events.
    Designed for SIEM consumption with filtering and pagination.

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
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 100, type=int), 1000)
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
            from datetime import datetime, timezone
            st = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
            query = query.filter(SecurityEvent.timestamp >= st)
        except (ValueError, AttributeError):
            pass
    if end_time:
        try:
            from datetime import datetime, timezone
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
