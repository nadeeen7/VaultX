from flask import Blueprint, request, jsonify, g
from app.models import db, User, Transaction, LoginAttempt
from app.auth import (
    token_required, verify_password, hash_password,
)
from app.logging.security_logger import log_security_event, log_audit

user_bp = Blueprint("user", __name__, url_prefix="/api/user")


@user_bp.route("/profile", methods=["GET"])
@token_required
def get_profile():
    """Get the current user's profile."""
    user = g.current_user
    data = user.to_dict()
    if user.account:
        data["account"] = user.account.to_dict()
    return jsonify(data), 200


@user_bp.route("/profile", methods=["PUT"])
@token_required
def update_profile():
    """Update the current user's profile (limited fields)."""
    user = g.current_user
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body is required"}), 400

    # Only allow updating name fields
    if "first_name" in data:
        user.first_name = data["first_name"]
    if "last_name" in data:
        user.last_name = data["last_name"]

    db.session.commit()
    return jsonify({"message": "Profile updated", "user": user.to_dict()}), 200


@user_bp.route("/change-password", methods=["POST"])
@token_required
def change_password():
    """Change the current user's password."""
    user = g.current_user
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body is required"}), 400

    current_password = data.get("current_password", "")
    new_password = data.get("new_password", "")

    if not current_password or not new_password:
        return jsonify({"error": "Both current and new passwords are required"}), 400

    if not verify_password(current_password, user.password_hash):
        log_security_event(
            event_type="PASSWORD_CHANGE_FAILED",
            user_id=user.id,
            username=user.username,
            status="FAILED",
            metadata={"reason": "incorrect_current_password"},
        )
        return jsonify({"error": "Current password is incorrect"}), 401

    if len(new_password) < 8:
        return jsonify({"error": "New password must be at least 8 characters"}), 400

    user.password_hash = hash_password(new_password)
    db.session.commit()

    log_security_event(
        event_type="PASSWORD_CHANGE",
        user_id=user.id,
        username=user.username,
        status="SUCCESS",
    )
    log_audit(
        action="UPDATE",
        resource_type="user",
        resource_id=user.id,
        user_id=user.id,
        details={"action": "password_change"},
    )

    return jsonify({"message": "Password changed successfully"}), 200


@user_bp.route("/transactions", methods=["GET"])
@token_required
def get_transactions():
    """Get the current user's transaction history."""
    user = g.current_user
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    pagination = Transaction.query.filter_by(user_id=user.id) \
        .order_by(Transaction.created_at.desc()) \
        .paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "transactions": [t.to_dict() for t in pagination.items],
        "total": pagination.total,
        "page": pagination.page,
        "per_page": pagination.per_page,
        "pages": pagination.pages,
    }), 200


@user_bp.route("/login-history", methods=["GET"])
@token_required
def get_login_history():
    """Get the current user's login history."""
    user = g.current_user
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    pagination = LoginAttempt.query.filter_by(user_id=user.id) \
        .order_by(LoginAttempt.created_at.desc()) \
        .paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "login_history": [l.to_dict() for l in pagination.items],
        "total": pagination.total,
        "page": pagination.page,
        "per_page": pagination.per_page,
        "pages": pagination.pages,
    }), 200
