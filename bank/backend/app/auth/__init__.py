import jwt
import bcrypt
from datetime import datetime, timezone, timedelta
from functools import wraps
from flask import request, jsonify, g
from app.models import User
from app.logging.security_logger import log_security_event


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against a bcrypt hash."""
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def create_token(user_id: str, role: str) -> str:
    """Create a JWT token for a user."""
    from flask import current_app
    payload = {
        "user_id": user_id,
        "role": role,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + current_app.config.get(
            "JWT_ACCESS_TOKEN_EXPIRES", timedelta(hours=1)
        ),
    }
    return jwt.encode(payload, current_app.config["JWT_SECRET_KEY"], algorithm="HS256")


def decode_token(token: str) -> dict:
    """Decode and verify a JWT token."""
    from flask import current_app
    return jwt.decode(token, current_app.config["JWT_SECRET_KEY"], algorithms=["HS256"])


def get_client_ip() -> str:
    """Get the client's IP address.
    
    Only trusts proxy headers when TRUST_PROXY=true is configured.
    This prevents attackers from spoofing X-Forwarded-For.
    """
    from flask import current_app
    
    # Only trust forwarded headers if explicitly configured
    trust_proxy = current_app.config.get('TRUST_PROXY', False)
    
    if trust_proxy:
        forwarded = request.headers.get('X-Forwarded-For')
        if forwarded:
            return forwarded.split(",")[0].strip()
        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip
    
    return request.remote_addr or "unknown"


def get_user_agent() -> str:
    """Get the user agent string."""
    return request.headers.get("User-Agent", "unknown")


def token_required(f):
    """Decorator to require a valid JWT token."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]

        if not token:
            return jsonify({"error": "Authentication required"}), 401

        try:
            data = decode_token(token)
            user = User.query.get(data["user_id"])
            if not user or not user.is_active:
                return jsonify({"error": "Invalid or inactive account"}), 401
            g.current_user = user
            g.token_data = data
        except jwt.ExpiredSignatureError:
            log_security_event(
                event_type="UNAUTHORIZED_ACCESS", status="BLOCKED", target="LOGIN",
                metadata={"reason": "expired_token"},
            )
            return jsonify({"error": "Token expired"}), 401
        except jwt.InvalidTokenError:
            log_security_event(
                event_type="UNAUTHORIZED_ACCESS", status="BLOCKED", target="LOGIN",
                metadata={"reason": "invalid_token"},
            )
            return jsonify({"error": "Invalid token"}), 401

        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    """Decorator to require admin role."""
    @wraps(f)
    @token_required
    def decorated(*args, **kwargs):
        if g.current_user.role != "admin":
            log_security_event(
                event_type="UNAUTHORIZED_ACCESS",
                user_id=g.current_user.id,
                username=g.current_user.username,
                status="BLOCKED",
                target="ADMIN",
                metadata={"attempted_resource": request.endpoint},
            )
            return jsonify({"error": "Admin access required"}), 403
        return f(*args, **kwargs)
    return decorated
