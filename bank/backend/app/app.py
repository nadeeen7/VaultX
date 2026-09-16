import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from config.config import config_by_name
from app.models import db
from app.routes.auth import auth_bp
from app.routes.user import user_bp
from app.routes.transactions import transactions_bp
from app.routes.admin import admin_bp
from app.routes.security_events import security_events_bp
from app.logging.security_logger import log_security_event


def create_app(config_name=None):
    """Create and configure the Flask application."""
    if config_name is None:
        config_name = os.getenv("FLASK_ENV", "development")

    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    # Initialize extensions
    db.init_app(app)

    # CORS configuration
    cors_origins = app.config.get("CORS_ORIGINS", [])
    if cors_origins:
        CORS(app, resources={r"/api/*": {"origins": cors_origins}})
    else:
        # No origins configured — block cross-origin requests in production
        CORS(app, resources={r"/api/*": {"origins": []}})

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(transactions_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(security_events_bp)

    # Mail configuration check: verify required variables are PRESENT at startup.
    # Logs only variable NAMES — never values.
    missing_mail_vars = [
        name for name in ("MAIL_SERVER", "MAIL_PORT", "MAIL_USERNAME",
                          "MAIL_PASSWORD", "MAIL_DEFAULT_SENDER")
        if not app.config.get(name)
    ]
    if missing_mail_vars:
        print(f"[MAIL] WARNING: mail configuration incomplete. Missing variables: {', '.join(missing_mail_vars)}")
        print("[MAIL] Forgot-password OTP emails will fail until these are set.")
    else:
        print(f"[MAIL] Mail configuration present (server host configured, port {app.config.get('MAIL_PORT')}).")

    # Security headers on every response. The backend serves a JSON API only,
    # so a restrictive CSP is safe here (the React app is served separately and
    # loads Google Sign-In from its own origin).
    @app.after_request
    def set_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        response.headers["Cache-Control"] = "no-store"
        return response

    # Safe centralized error handling: production clients never see stack
    # traces, SQL errors, schema details, or internal paths.
    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({"error": "Bad request"}), 400

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({"error": "Method not allowed"}), 405

    @app.errorhandler(429)
    def too_many_requests(e):
        return jsonify({"error": "Too many requests. Please wait a moment and try again."}), 429

    @app.errorhandler(500)
    def internal_error(e):
        # Roll back a possibly poisoned DB session so the worker stays healthy.
        try:
            db.session.rollback()
        except Exception:
            pass
        return jsonify({"error": "Internal server error"}), 500

    # Request middleware for suspicious request logging
    @app.before_request
    def before_request():
        """Log potentially suspicious requests."""
        suspicious_patterns = [
            "script", "eval(", "exec(", "../", "..\\",
            "<script", "javascript:", "onerror=",
            "union select", "drop table", "insert into",
        ]
        full_url = request.full_path.lower()
        for pattern in suspicious_patterns:
            if pattern in full_url:
                log_security_event(
                    event_type="SUSPICIOUS_REQUEST",
                    status="BLOCKED",
                    metadata={
                        "pattern": pattern,
                        "path": request.path,
                        "query": request.query_string.decode("utf-8", errors="replace"),
                    },
                )
                break

    # Health check endpoint
    @app.route("/api/health", methods=["GET"])
    def health():
        db_ok = False
        try:
            db.session.execute(db.text("SELECT 1"))
            db_ok = True
        except Exception:
            pass

        siem_configured = bool(app.config.get("SIEM_API_URL"))
        mail_configured = bool(
            app.config.get("MAIL_SERVER")
            and app.config.get("MAIL_USERNAME")
            and app.config.get("MAIL_PASSWORD")
            and app.config.get("MAIL_DEFAULT_SENDER")
        )

        return jsonify({
            "status": "ok",
            "service": "bank-backend",
            "database": "connected" if db_ok else "disconnected",
            "siem_configured": siem_configured,
            "mail_configured": mail_configured,
        }), 200

    # Create tables
    with app.app_context():
        db.create_all()

    # Production startup warnings
    if config_name == "production":
        if not cors_origins:
            print("[WARNING] CORS_ORIGINS is not set. Cross-origin requests will be blocked.")
            print("  Set CORS_ORIGINS to your frontend URL(s), e.g.: CORS_ORIGINS=https://bank.yourdomain.com")
        if not app.config.get("SIEM_API_URL"):
            print("[INFO] SIEM_API_URL is not configured. Security events will be logged locally but not pushed to SIEM.")
            print("  Set SIEM_API_URL when the SIEM backend is deployed, e.g.: SIEM_API_URL=https://siem-api.yourdomain.com")
        if not app.config.get("TRUST_PROXY"):
            print("[INFO] TRUST_PROXY is not enabled. Client IPs will come from remote_addr; enable it when running behind a reverse proxy (e.g. Render).")

    return app
