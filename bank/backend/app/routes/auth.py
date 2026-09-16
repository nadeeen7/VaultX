import secrets
from datetime import datetime, timezone, timedelta
from flask import Blueprint, request, jsonify, g, current_app
import requests as http_requests
import bcrypt as bcrypt_lib
from app.models import db, User, LoginAttempt, OTP, gen_uuid, utcnow
from app.auth import (
    hash_password, verify_password, create_token,
    get_client_ip, get_user_agent, token_required,
)
from app.services.account_service import create_account_for_user
from app.services.email_service import send_otp_email
from app.services.validation import (
    validate_password_policy, validate_email, validate_username, validate_name,
    get_json_object,
)
from app.services.rate_limiter import rate_limit
from app.logging.security_logger import log_security_event, log_audit

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


# ──────────────────────────────────────────────
# Helper: find or create user from Google profile
# ──────────────────────────────────────────────
def _find_or_create_google_user(google_user: dict) -> User:
    """
    Given a verified Google profile dict (sub, email, name, picture),
    find an existing user by google_id or email, or create a new one.
    """
    google_id = google_user["sub"]
    email = google_user["email"]
    first_name = google_user.get("given_name", "")
    last_name = google_user.get("family_name", "")

    # 1. Check by google_id
    user = User.query.filter_by(google_id=google_id).first()
    if user:
        return user

    # 2. Check by email (user registered with email/password previously)
    user = User.query.filter_by(email=email).first()
    if user:
        # Link the Google account to existing user
        user.google_id = google_id
        user.auth_provider = "google"
        db.session.commit()
        return user

    # 3. Create a brand new user
    # Generate a unique username from email
    base_username = email.split("@")[0]
    username = base_username
    counter = 1
    while User.query.filter_by(username=username).first():
        username = f"{base_username}{counter}"
        counter += 1

    user = User(
        id=gen_uuid(),
        username=username,
        email=email,
        password_hash=None,  # No password for Google-only accounts
        first_name=first_name or "Google",
        last_name=last_name or "User",
        role="user",
        google_id=google_id,
        auth_provider="google",
    )
    db.session.add(user)
    db.session.commit()

    # Create bank account with initial balance
    create_account_for_user(user.id, initial_balance=5000.00)

    log_security_event(
        event_type="ACCOUNT_CREATED",
        user_id=user.id,
        username=user.username,
        status="SUCCESS",
        metadata={"email": user.email, "auth_provider": "google"},
    )
    log_audit(
        action="CREATE",
        resource_type="user",
        resource_id=user.id,
        user_id=user.id,
        details={"username": user.username, "auth_provider": "google"},
    )

    return user


# ──────────────────────────────────────────────
# Helper: generate and hash a 6-digit OTP
# ──────────────────────────────────────────────
def _as_aware(dt):
    """
    Ensure a datetime is timezone-aware (assume UTC for naive values).

    SQLite drivers return naive datetimes even for timezone=True columns, and
    comparing them against aware datetimes raises TypeError. Normalizing here
    keeps lockout/OTP-expiry checks working on PostgreSQL and SQLite alike.
    """
    if dt is None:
        return None
    if getattr(dt, "tzinfo", None) is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _generate_otp() -> str:
    """Generate a cryptographically secure 6-digit OTP."""
    return f"{secrets.randbelow(1000000):06d}"


def _hash_otp(otp: str) -> str:
    """Hash an OTP using bcrypt."""
    salt = bcrypt_lib.gensalt()
    return bcrypt_lib.hashpw(otp.encode("utf-8"), salt).decode("utf-8")


def _verify_otp(otp: str, otp_hash: str) -> bool:
    """Verify an OTP against its bcrypt hash."""
    return bcrypt_lib.checkpw(otp.encode("utf-8"), otp_hash.encode("utf-8"))


# ──────────────────────────────────────────────
# POST /api/auth/register
# ──────────────────────────────────────────────
@auth_bp.route("/register", methods=["POST"])
@rate_limit("register", max_requests=10, window_seconds=300, target="LOGIN")
def register():
    """Register a new user account."""
    data, err = get_json_object()
    if err:
        return err

    # Validate required fields
    required = ["username", "email", "password", "first_name", "last_name"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    # Validate field formats and lengths (no raw input straight into the DB)
    if not validate_username(data["username"]):
        return jsonify({"error": "Username must be 3-40 characters (letters, digits, dot, dash, underscore)"}), 400
    if not validate_email(data["email"]):
        return jsonify({"error": "Invalid email address"}), 400
    if not validate_name(data["first_name"]) or not validate_name(data["last_name"]):
        return jsonify({"error": "Names must be 1-60 characters"}), 400

    # Validate password confirmation
    if data.get("password") != data.get("confirm_password"):
        return jsonify({"error": "Passwords do not match"}), 400

    # Validate password strength (new-password policy)
    password = data["password"]
    ok, pw_error = validate_password_policy(password)
    if not ok:
        return jsonify({"error": pw_error}), 400

    # Check uniqueness
    username = data["username"].strip()
    email = data["email"].strip().lower()
    if User.query.filter_by(username=username).first():
        return jsonify({"error": "Username already taken"}), 409
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already registered"}), 409

    # Create user
    user = User(
        id=gen_uuid(),
        username=username,
        email=email,
        password_hash=hash_password(password),
        first_name=data["first_name"],
        last_name=data["last_name"],
        role="user",
        auth_provider="email",
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


# ──────────────────────────────────────────────
# POST /api/auth/login
# ──────────────────────────────────────────────
@auth_bp.route("/login", methods=["POST"])
@rate_limit("login", max_requests=10, window_seconds=60, target="LOGIN")
def login():
    """Authenticate a user and return a JWT."""
    data, err = get_json_object()
    if err:
        return err

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
        if datetime.now(timezone.utc) < _as_aware(user.lockout_until):
            remaining = (_as_aware(user.lockout_until) - datetime.now(timezone.utc)).seconds // 60 + 1
            log_security_event(
                event_type="BRUTE_FORCE_ATTEMPT",
                user_id=user.id,
                username=user.username,
                status="BLOCKED",
                source_ip=get_client_ip(),
                target="LOGIN",
                metadata={"reason": "login_attempt_during_lockout",
                          "remaining_minutes": remaining},
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

    if not user or not user.password_hash or not verify_password(password, user.password_hash):
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
                user.lockout_until = _as_aware(utcnow()) + timedelta(
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
                # Brute-force signature for SIEM correlation (HIGH severity)
                log_security_event(
                    event_type="BRUTE_FORCE_ATTEMPT",
                    user_id=user.id,
                    username=user.username,
                    status="BLOCKED",
                    source_ip=get_client_ip(),
                    target="LOGIN",
                    metadata={"failed_attempts": user.failed_login_attempts,
                              "lockout_minutes": current_app.config.get("LOCKOUT_DURATION_MINUTES", 15)},
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


# ──────────────────────────────────────────────
# POST /api/auth/google — Google Sign-In
# ──────────────────────────────────────────────
@auth_bp.route("/google", methods=["POST"])
@rate_limit("google", max_requests=15, window_seconds=60, target="LOGIN")
def google_login():
    """
    Authenticate or register a user via Google Sign-In.
    Expects: { "credential": "<Google ID token>" }
    """
    data, err = get_json_object()
    if err:
        return err
    if not data.get("credential"):
        return jsonify({"error": "Google credential is required"}), 400

    credential = data["credential"]

    # Verify the Google ID token
    google_client_id = current_app.config.get("GOOGLE_CLIENT_ID", "")
    if not google_client_id:
        return jsonify({"error": "Google Sign-In is not configured"}), 503

    try:
        # Verify token via Google's tokeninfo endpoint
        resp = http_requests.get(
            "https://oauth2.googleapis.com/tokeninfo",
            params={"id_token": credential},
            timeout=10,
        )
        if resp.status_code != 200:
            log_security_event(event_type="GOOGLE_LOGIN_FAILED", status="FAILED",
                               target="LOGIN", metadata={"reason": "invalid_credential"})
            return jsonify({"error": "Invalid Google credential"}), 401

        google_user = resp.json()

        # Validate audience matches our client ID
        if google_user.get("aud") != google_client_id:
            log_security_event(event_type="GOOGLE_LOGIN_FAILED", status="FAILED",
                               target="LOGIN", metadata={"reason": "invalid_audience"})
            return jsonify({"error": "Invalid Google credential audience"}), 401

        # Validate token hasn't expired
        exp = int(google_user.get("exp", 0))
        if exp < datetime.now(timezone.utc).timestamp():
            log_security_event(event_type="GOOGLE_LOGIN_FAILED", status="FAILED",
                               target="LOGIN", metadata={"reason": "credential_expired"})
            return jsonify({"error": "Google credential has expired"}), 401

        # Validate email is verified
        if not google_user.get("email_verified", False):
            log_security_event(event_type="GOOGLE_LOGIN_FAILED", status="FAILED",
                               target="LOGIN", metadata={"reason": "email_not_verified"})
            return jsonify({"error": "Google email is not verified"}), 401

    except http_requests.RequestException:
        log_security_event(event_type="GOOGLE_LOGIN_FAILED", status="FAILED",
                           target="LOGIN", metadata={"reason": "verification_unavailable"})
        return jsonify({"error": "Failed to verify Google credential"}), 502

    # Find or create user
    user = _find_or_create_google_user(google_user)

    if not user.is_active:
        return jsonify({"error": "Account is deactivated"}), 403

    # Log successful login
    login_attempt = LoginAttempt(
        user_id=user.id,
        username=user.username,
        email=user.email,
        success=True,
        source_ip=get_client_ip(),
        user_agent=get_user_agent(),
    )
    db.session.add(login_attempt)

    # A successful Google login resets any login failure counters
    user.failed_login_attempts = 0
    user.last_failed_login = None
    user.lockout_until = None
    user.is_locked = False
    db.session.commit()

    log_security_event(
        event_type="GOOGLE_LOGIN_SUCCESS",
        user_id=user.id,
        username=user.username,
        status="SUCCESS",
        target="LOGIN",
        metadata={"auth_provider": "google"},
    )
    log_security_event(
        event_type="LOGIN_SUCCESS",
        user_id=user.id,
        username=user.username,
        status="SUCCESS",
        metadata={"source_ip": get_client_ip(), "auth_provider": "google"},
    )

    token = create_token(user.id, user.role)

    return jsonify({
        "message": "Google login successful",
        "token": token,
        "user": user.to_dict(),
    }), 200


# ──────────────────────────────────────────────
# POST /api/auth/forgot-password — Request OTP
# ──────────────────────────────────────────────
@auth_bp.route("/forgot-password", methods=["POST"])
@rate_limit("forgot_password", max_requests=5, window_seconds=300, target="OTP")
def forgot_password():
    """
    Send a 6-digit OTP to the user's email for password reset.
    Always returns success to prevent email enumeration.
    """
    data, err = get_json_object()
    if err:
        return err

    if not data.get("email"):
        return jsonify({"error": "Email is required"}), 400

    email = data["email"].strip().lower()
    # Format check only — response stays identical whether or not the email exists.
    if not validate_email(email):
        return jsonify({"error": "Invalid email address"}), 400
    user = User.query.filter_by(email=email).first()

    # Always return the same response to prevent email enumeration
    success_msg = {"message": "If that email is registered, a verification code has been sent."}

    if not user:
        # Don't reveal whether email exists
        return jsonify(success_msg), 200

    # Check if user has a password (Google-only accounts can't use this)
    if not user.password_hash and user.auth_provider == "google":
        return jsonify(success_msg), 200

    # Rate limit: check for recent OTP (within last 60 seconds).
    # Only treat OTPs as "recently sent" if they were actually delivered —
    # otherwise a failed email send blocks the user from retrying for 60s.
    # `delivered_at` is set by the email service only after a successful SMTP send.
    recent_otp = OTP.query.filter(
        OTP.email == email,
        OTP.purpose == "password_reset",
        OTP.delivered_at.isnot(None),
        OTP.delivered_at > _as_aware(utcnow()) - timedelta(seconds=60),
    ).first()
    if recent_otp:
        return jsonify({"message": "A code was recently sent. Please check your inbox."}), 200

    # Invalidate any previous unused OTPs for this email
    OTP.query.filter(
        OTP.email == email,
        OTP.purpose == "password_reset",
        OTP.is_used == False,
    ).update({"is_used": True})
    db.session.commit()

    # Generate and store OTP
    otp_code = _generate_otp()
    otp_record = OTP(
        id=gen_uuid(),
        email=email,
        otp_hash=_hash_otp(otp_code),
        purpose="password_reset",
        attempts=0,
        max_attempts=5,
        is_used=False,
        created_at=utcnow(),
        expires_at=utcnow() + timedelta(minutes=10),
    )
    db.session.add(otp_record)
    db.session.commit()

    # Send OTP email
    # NOTE: the response only reveals that the account exists via delivery
    # outcomes — the generic message below never changes based on result.
    sent, reason = send_otp_email(email, otp_code, purpose="password_reset")

    if not sent:
        # Email delivery failed. Do NOT pretend it succeeded: return an error
        # so the user can retry, and log a safe reason (never OTP values,
        # credentials, or SMTP secrets).
        print(f"[MAIL] Forgot-password email delivery failed for a request (reason={reason})")
        return jsonify({
            "error": "We could not send the verification email right now. Please try again shortly."
        }), 503

    # Mark the OTP as delivered (only on successful SMTP send) so the
    # "recently sent" rate limit is based on real deliveries.
    otp_record.delivered_at = _as_aware(utcnow())
    db.session.commit()

    log_security_event(
        event_type="OTP_REQUEST",
        user_id=user.id,
        username=user.username,
        status="SUCCESS",
        target="OTP",
        metadata={"source_ip": get_client_ip()},
    )

    log_security_event(
        event_type="PASSWORD_RESET_REQUESTED",
        user_id=user.id,
        username=user.username,
        status="SUCCESS",
        metadata={"source_ip": get_client_ip()},
    )

    return jsonify(success_msg), 200


# ──────────────────────────────────────────────
# POST /api/auth/verify-otp — Verify OTP code
# ──────────────────────────────────────────────
@auth_bp.route("/verify-otp", methods=["POST"])
@rate_limit("verify_otp", max_requests=10, window_seconds=300, target="OTP")
def verify_otp():
    """
    Verify the 6-digit OTP code for password reset.
    Returns a reset token if valid.
    """
    data, err = get_json_object()
    if err:
        return err

    email = (data.get("email") or "").strip().lower()
    otp_code = (data.get("otp") or "").strip()

    if not email or not otp_code:
        return jsonify({"error": "Email and OTP code are required"}), 400

    if len(otp_code) != 6 or not otp_code.isdigit():
        return jsonify({"error": "OTP must be a 6-digit code"}), 400

    # Find the latest unused OTP for this email
    otp_record = OTP.query.filter(
        OTP.email == email,
        OTP.purpose == "password_reset",
        OTP.is_used == False,
    ).order_by(OTP.created_at.desc()).first()

    if not otp_record:
        log_security_event(
            event_type="OTP_VERIFICATION_FAILED", status="FAILED", target="OTP",
            metadata={"reason": "no_valid_code", "source_ip": get_client_ip()},
        )
        return jsonify({"error": "Invalid or expired verification code"}), 400

    # Check expiry
    if utcnow() > _as_aware(otp_record.expires_at):
        otp_record.is_used = True
        db.session.commit()
        log_security_event(
            event_type="OTP_EXPIRED", status="DETECTED", target="OTP",
            metadata={"reason": "expired_at_verification", "source_ip": get_client_ip()},
        )
        return jsonify({"error": "Verification code has expired. Please request a new one."}), 400

    # Check attempt limit
    if otp_record.attempts >= otp_record.max_attempts:
        otp_record.is_used = True
        db.session.commit()
        log_security_event(
            event_type="OTP_VERIFICATION_FAILED", status="BLOCKED", target="OTP",
            metadata={"reason": "max_attempts_exceeded", "source_ip": get_client_ip()},
        )
        return jsonify({"error": "Too many failed attempts. Please request a new code."}), 429

    # Verify OTP
    otp_record.attempts += 1
    if not _verify_otp(otp_code, otp_record.otp_hash):
        db.session.commit()
        remaining = otp_record.max_attempts - otp_record.attempts
        if remaining <= 0:
            otp_record.is_used = True
            db.session.commit()
            log_security_event(
                event_type="OTP_VERIFICATION_FAILED", status="BLOCKED", target="OTP",
                metadata={"reason": "max_attempts_exceeded", "source_ip": get_client_ip()},
            )
            return jsonify({"error": "Too many failed attempts. Please request a new code."}), 429
        log_security_event(
            event_type="OTP_VERIFICATION_FAILED", status="FAILED", target="OTP",
            metadata={"reason": "invalid_code", "attempts_remaining": remaining,
                      "source_ip": get_client_ip()},
        )
        return jsonify({"error": f"Invalid verification code. {remaining} attempts remaining."}), 400

    # OTP valid — mark as used and generate a short-lived reset token
    otp_record.is_used = True
    db.session.commit()

    # Create a short-lived token for the password reset step
    reset_token = secrets.token_urlsafe(32)
    # Store the reset token hash in a simple way: re-use OTP table or use a separate mechanism
    # For simplicity, we'll use a second OTP record as the reset token
    reset_otp = OTP(
        id=gen_uuid(),
        email=email,
        otp_hash=_hash_otp(reset_token),
        purpose="password_reset_token",
        attempts=0,
        max_attempts=1,
        is_used=False,
        created_at=utcnow(),
        expires_at=utcnow() + timedelta(minutes=10),
    )
    db.session.add(reset_otp)
    db.session.commit()

    log_security_event(
        event_type="OTP_VERIFIED",
        status="SUCCESS",
        target="OTP",
        metadata={"email": email, "source_ip": get_client_ip()},
    )

    return jsonify({
        "message": "Verification code confirmed",
        "reset_token": reset_token,
    }), 200


# ──────────────────────────────────────────────
# POST /api/auth/reset-password — Set new password
# ──────────────────────────────────────────────
@auth_bp.route("/reset-password", methods=["POST"])
@rate_limit("reset_password", max_requests=10, window_seconds=300, target="OTP")
def reset_password():
    """
    Reset the user's password using a valid reset token.
    """
    data, err = get_json_object()
    if err:
        return err

    email = (data.get("email") or "").strip().lower()
    reset_token = (data.get("reset_token") or "").strip()
    new_password = data.get("new_password", "")
    confirm_password = data.get("confirm_password", "")

    if not email or not reset_token or not new_password:
        return jsonify({"error": "Email, reset token, and new password are required"}), 400

    if new_password != confirm_password:
        return jsonify({"error": "Passwords do not match"}), 400

    # New-password policy (also enforces complexity, not just length)
    ok, pw_error = validate_password_policy(new_password)
    if not ok:
        return jsonify({"error": pw_error}), 400

    # Find and validate the reset token
    reset_otp = OTP.query.filter(
        OTP.email == email,
        OTP.purpose == "password_reset_token",
        OTP.is_used == False,
    ).order_by(OTP.created_at.desc()).first()

    if not reset_otp:
        log_security_event(
            event_type="OTP_VERIFICATION_FAILED", status="FAILED", target="OTP",
            metadata={"reason": "invalid_reset_token", "source_ip": get_client_ip()},
        )
        return jsonify({"error": "Invalid or expired reset token"}), 400

    if utcnow() > _as_aware(reset_otp.expires_at):
        reset_otp.is_used = True
        db.session.commit()
        log_security_event(
            event_type="OTP_EXPIRED", status="DETECTED", target="OTP",
            metadata={"reason": "reset_token_expired", "source_ip": get_client_ip()},
        )
        return jsonify({"error": "Reset token has expired. Please start over."}), 400

    if not _verify_otp(reset_token, reset_otp.otp_hash):
        reset_otp.attempts += 1
        db.session.commit()
        log_security_event(
            event_type="OTP_VERIFICATION_FAILED", status="FAILED", target="OTP",
            metadata={"reason": "invalid_reset_token", "source_ip": get_client_ip()},
        )
        return jsonify({"error": "Invalid reset token"}), 400

    # Token valid — find user and update password
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    user.password_hash = hash_password(new_password)
    user.auth_provider = "email"  # Ensure they can log in with password
    user.failed_login_attempts = 0
    user.is_locked = False
    user.lockout_until = None

    reset_otp.is_used = True
    db.session.commit()

    log_security_event(
        event_type="PASSWORD_RESET_COMPLETED",
        user_id=user.id,
        username=user.username,
        status="SUCCESS",
        metadata={"source_ip": get_client_ip()},
    )
    log_security_event(
        event_type="PASSWORD_RESET_SUCCESS",
        user_id=user.id,
        username=user.username,
        status="SUCCESS",
        target="OTP",
        metadata={"source_ip": get_client_ip()},
    )
    log_security_event(
        event_type="OTP_RESET_SUCCESS",
        user_id=user.id,
        username=user.username,
        status="SUCCESS",
        target="OTP",
        metadata={"source_ip": get_client_ip()},
    )
    log_audit(
        action="UPDATE",
        resource_type="user",
        resource_id=user.id,
        user_id=user.id,
        details={"action": "password_reset"},
    )

    return jsonify({"message": "Password has been reset successfully"}), 200


# ──────────────────────────────────────────────
# POST /api/auth/logout
# ──────────────────────────────────────────────
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
