from flask import Blueprint, request, jsonify, g
from datetime import datetime, timezone, timedelta
from app.models import db, User, Account, Transaction, LoginAttempt, SecurityEvent
from app.auth import (
    hash_password, verify_password, create_token,
    get_client_ip, get_user_agent, admin_required,
)
from app.logging.security_logger import log_security_event, log_audit

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")


@admin_bp.route("/login", methods=["POST"])
def admin_login():
    """Admin login endpoint with separate tracking."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body is required"}), 400

    identifier = data.get("username") or data.get("email", "")
    password = data.get("password", "")

    if not identifier or not password:
        return jsonify({"error": "Username/email and password are required"}), 400

    user = User.query.filter(
        (User.username == identifier) | (User.email == identifier)
    ).first()

    if not user or not verify_password(password, user.password_hash):
        log_security_event(
            event_type="ADMIN_LOGIN_FAILED",
            user_id=user.id if user else None,
            username=identifier,
            status="FAILED",
            metadata={"reason": "invalid_credentials"},
        )
        return jsonify({"error": "Invalid credentials"}), 401

    if user.role != "admin":
        log_security_event(
            event_type="UNAUTHORIZED_ACCESS",
            user_id=user.id,
            username=user.username,
            status="FAILED",
            metadata={"reason": "not_admin_role", "endpoint": "/api/admin/login"},
        )
        return jsonify({"error": "Admin access required"}), 403

    log_security_event(
        event_type="ADMIN_LOGIN",
        user_id=user.id,
        username=user.username,
        status="SUCCESS",
        metadata={"source_ip": get_client_ip()},
    )

    token = create_token(user.id, user.role)
    return jsonify({
        "message": "Admin login successful",
        "token": token,
        "user": user.to_dict(),
    }), 200


@admin_bp.route("/users", methods=["GET"])
@admin_required
def get_users():
    """Get all users (admin only)."""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 50, type=int)

    pagination = User.query.order_by(User.created_at.desc()) \
        .paginate(page=page, per_page=per_page, error_out=False)

    users = []
    for u in pagination.items:
        udata = u.to_dict()
        if u.account:
            udata["account"] = u.account.to_dict()
        users.append(udata)

    return jsonify({
        "users": users,
        "total": pagination.total,
        "page": pagination.page,
        "per_page": pagination.per_page,
        "pages": pagination.pages,
    }), 200


@admin_bp.route("/users/<user_id>/toggle-status", methods=["POST"])
@admin_required
def toggle_user_status(user_id):
    """Enable/disable a user account (admin only)."""
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    user.is_active = not user.is_active
    db.session.commit()

    log_audit(
        action="UPDATE",
        resource_type="user",
        resource_id=user_id,
        user_id=g.current_user.id,
        details={"field": "is_active", "new_value": user.is_active},
    )

    return jsonify({
        "message": f"User {'enabled' if user.is_active else 'disabled'}",
        "user": user.to_dict(),
    }), 200


@admin_bp.route("/transactions", methods=["GET"])
@admin_required
def get_all_transactions():
    """Get all transactions (admin only)."""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 50, type=int)
    user_id = request.args.get("user_id")

    query = Transaction.query
    if user_id:
        query = query.filter_by(user_id=user_id)

    pagination = query.order_by(Transaction.created_at.desc()) \
        .paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "transactions": [t.to_dict() for t in pagination.items],
        "total": pagination.total,
        "page": pagination.page,
        "per_page": pagination.per_page,
        "pages": pagination.pages,
    }), 200


@admin_bp.route("/security-events", methods=["GET"])
@admin_required
def get_security_events():
    """Get security events (admin only)."""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 50, type=int)
    event_type = request.args.get("event_type")
    status = request.args.get("status")
    user_id = request.args.get("user_id")

    query = SecurityEvent.query
    if event_type:
        query = query.filter_by(event_type=event_type)
    if status:
        query = query.filter_by(status=status)
    if user_id:
        query = query.filter_by(user_id=user_id)

    pagination = query.order_by(SecurityEvent.timestamp.desc()) \
        .paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "events": [e.to_dict() for e in pagination.items],
        "total": pagination.total,
        "page": pagination.page,
        "per_page": pagination.per_page,
        "pages": pagination.pages,
    }), 200


@admin_bp.route("/login-activity", methods=["GET"])
@admin_required
def get_login_activity():
    """Get recent login activity (admin only)."""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 50, type=int)

    pagination = LoginAttempt.query.order_by(LoginAttempt.created_at.desc()) \
        .paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "login_attempts": [l.to_dict() for l in pagination.items],
        "total": pagination.total,
        "page": pagination.page,
        "per_page": pagination.per_page,
        "pages": pagination.pages,
    }), 200


@admin_bp.route("/stats", methods=["GET"])
@admin_required
def get_stats():
    """Get system statistics (admin only)."""
    now = datetime.now(timezone.utc)
    twenty_four_hours_ago = now - timedelta(hours=24)

    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    locked_users = User.query.filter_by(is_locked=True).count()
    total_transactions = Transaction.query.count()
    failed_logins_24h = LoginAttempt.query.filter(
        LoginAttempt.success == False,
        LoginAttempt.created_at >= twenty_four_hours_ago,
    ).count()
    successful_logins_24h = LoginAttempt.query.filter(
        LoginAttempt.success == True,
        LoginAttempt.created_at >= twenty_four_hours_ago,
    ).count()
    security_events_24h = SecurityEvent.query.filter(
        SecurityEvent.timestamp >= twenty_four_hours_ago,
    ).count()

    return jsonify({
        "total_users": total_users,
        "active_users": active_users,
        "locked_users": locked_users,
        "total_transactions": total_transactions,
        "failed_logins_24h": failed_logins_24h,
        "successful_logins_24h": successful_logins_24h,
        "security_events_24h": security_events_24h,
    }), 200
