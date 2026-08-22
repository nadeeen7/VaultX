from datetime import datetime, timezone, timedelta
from flask import Blueprint, request, jsonify, g
from app.models import db, User, LoginAttempt, gen_uuid, utcnow
from app.auth import (
    hash_password, verify_password, create_token,
    get_client_ip, get_user_agent, token_required,
)
from app.services.account_service import create_account_for_user
from app.logging.security_logger import log_security_event, log_audit
from flask import current_app

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.route("/register", methods=["POST"])
def register():
    """Register a new user account."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body is required"}), 400

    # Validate required fields
    required = ["username", "email", "password", "first_name", "last_name"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    # Validate password confirmation
    if data.get("password") != data.get("confirm_password"):
        return jsonify({"error": "Passwords do not match"}), 400

    # Validate password strength
    password = data["password"]
    if len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters"}), 400

    # Check uniqueness
    if User.query.filter_by(username=data["username"]).first():
        return jsonify({"error": "Username already taken"}), 409
    if User.query.filter_by(email=data["email"]).first():
        return jsonify({"error": "Email already registered"}), 409

    # Create user
    user = User(
        id=gen_uuid(),
        username=data["username"],
        email=data["email"],
        password_hash=hash_password(password),
        first_name=data["first_name"],
        last_name=data["last_name"],
        role="user",
    )
    db.session.add(user)
    db.session.commit()

    # Create account with fake initial balance
    create_account_for_user(user.id, initial_balance=5000.00)

    # Log security event
    log_security_event(
        event_type="ACCOUNT_CREATED",
        user_id=user.id,
        username=user.username,
        status="SUCCESS",
        metadata={"email": user.email},
    )
    log_audit(
        action="CREATE",
        resource_type="user",
        resource_id=user.id,
        user_id=user.id,
        details={"username": user.username},
    )

    token = create_token(user.id, user.role)

    return jsonify({
        "message": "Registration successful",
        "token": token,
        "user": user.to_dict(),
    }), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    """Authenticate a user and return a JWT."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body is required"}), 400

    identifier = data.get("username") or data.get("email", "")
    password = data.get("password", "")

    if not identifier or not password:
        return jsonify({"error": "Username/email and password are required"}), 400

    # Find user
    user = User.query.filter(
        (User.username == identifier) | (User.email == identifier)
    ).first()

    # Check account lockout
    if user and user.is_locked and user.lockout_until:
        if datetime.now(timezone.utc) < user.lockout_until:
            remaining = (user.lockout_until - datetime.now(timezone.utc)).seconds // 60 + 1
            log_security_event(
                event_type="LOGIN_FAILED",
                user_id=user.id,
                username=user.username,
                status="BLOCKED",
                metadata={"reason": "account_locked", "remaining_minutes": remaining},
            )
            return jsonify({
                "error": f"Account is locked. Try again in {remaining} minutes.",
                "locked": True,
            }), 423
        else:
            # Lockout expired, unlock account
            user.is_locked = False
            user.failed_login_attempts = 0
            db.session.commit()

    if not user or not verify_password(password, user.password_hash):
        # Log failed attempt
        login_attempt = LoginAttempt(
            user_id=user.id if user else None,
            username=identifier,
            email=data.get("email"),
            success=False,
            source_ip=get_client_ip(),
            user_agent=get_user_agent(),
            failure_reason="invalid_credentials" if user else "user_not_found",
        )
        db.session.add(login_attempt)

        # Update failed attempts counter
        if user:
            user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
            user.last_failed_login = utcnow()

            max_attempts = current_app.config.get("MAX_LOGIN_ATTEMPTS", 5)
            if user.failed_login_attempts >= max_attempts:
                user.is_locked = True
                user.lockout_until = utcnow() + timedelta(
                    minutes=current_app.config.get("LOCKOUT_DURATION_MINUTES", 15)
                )
                db.session.commit()
                log_security_event(
                    event_type="ACCOUNT_LOCKED",
                    user_id=user.id,
                    username=user.username,
                    status="SUCCESS",
                    metadata={"reason": "max_attempts_exceeded",
                              "attempts": user.failed_login_attempts},
                )
                return jsonify({
                    "error": "Account locked due to too many failed attempts",
                    "locked": True,
                }), 423

        db.session.commit()

        log_security_event(
            event_type="LOGIN_FAILED",
            user_id=user.id if user else None,
            username=identifier,
            status="FAILED",
            metadata={"failure_reason": "invalid_credentials" if user else "user_not_found"},
        )

        return jsonify({"error": "Invalid credentials"}), 401

    # Check if user is active
    if not user.is_active:
        return jsonify({"error": "Account is deactivated"}), 403

    # Successful login
    user.failed_login_attempts = 0
    user.last_failed_login = None
    db.session.commit()

    login_attempt = LoginAttempt(
        user_id=user.id,
        username=user.username,
        email=user.email,
        success=True,
        source_ip=get_client_ip(),
        user_agent=get_user_agent(),
    )
    db.session.add(login_attempt)
    db.session.commit()

    log_security_event(
        event_type="LOGIN_SUCCESS",
        user_id=user.id,
        username=user.username,
        status="SUCCESS",
        metadata={"source_ip": get_client_ip()},
    )

    token = create_token(user.id, user.role)

    return jsonify({
        "message": "Login successful",
        "token": token,
        "user": user.to_dict(),
    }), 200


@auth_bp.route("/logout", methods=["POST"])
@token_required
def logout():
    """Log out the current user."""
    user = g.current_user

    log_security_event(
        event_type="LOGOUT",
        user_id=user.id,
        username=user.username,
        status="SUCCESS",
    )
    log_audit(
        action="LOGOUT",
        resource_type="user",
        resource_id=user.id,
        user_id=user.id,
    )

    return jsonify({"message": "Logged out successfully"}), 200
