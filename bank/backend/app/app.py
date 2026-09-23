import os
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from sqlalchemy.exc import OperationalError
from config.config import config_by_name
from app.models import db
from app.routes.auth import auth_bp
from app.routes.user import user_bp
from app.routes.transactions import transactions_bp
from app.routes.admin import admin_bp
from app.routes.security_events import security_events_bp
from app.logging.security_logger import log_security_event
from app.services.email_service import mail_status, log_mail_configuration

# Dedicated DB-logger. Never configured to print SQL, parameters, connection
# strings, or credentials — callers log exception TYPE plus a fixed marker only.
# WARNING level so errors surface on Render even with an unconfigured root logger.
_db_logger = logging.getLogger("vaultx.db")
_db_logger.setLevel(logging.WARNING)


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

    # Presence and actual provider selection only; no credentials or addresses.
    log_mail_configuration()

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

    @app.errorhandler(OperationalError)
    def database_operational_error(e):
        """Centralized handling for transient DB connection failures.

        The client never sees driver/SQLAlchemy internals: just a generic 503.
        Safe diagnostics are logged WITHOUT the connection URL, credentials,
        SQL statement text, query parameters, OTPs, or tokens — only the
        exception class name and a fixed classification marker.
        """
        try:
            db.session.rollback()  # never leave a failed transaction open
        except Exception:
            pass
        # "ssl_eof" marker = the Render idle-drop family (SSL EOF / server
        # closed connection). Not printed itself, just a stable classifier.
        kind = "ssl_eof" if "eof" in str(getattr(e, "orig", "")).lower() else "db"
        _db_logger.error(
            "[DB] Database connection error occurred (%s); "
            "transaction rolled back; client received 503. exception=%s",
            kind, type(e).__name__,
        )
        return jsonify({"error": "Service temporarily unavailable. Please try again shortly."}), 503

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
        mail_configured = bool(mail_status()[0])

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
        _db_logger.warning(
            "[DB] Production DB engine ready: pool_pre_ping=True, pool_recycle=%ss, pool_timeout=%ss, pool_size=%s, max_overflow=%s. "
            "SQL mode: %s. Connection URL is not logged.",
            app.config["SQLALCHEMY_ENGINE_OPTIONS"]["pool_recycle"],
            app.config["SQLALCHEMY_ENGINE_OPTIONS"]["pool_timeout"],
            app.config["SQLALCHEMY_ENGINE_OPTIONS"]["pool_size"],
            app.config["SQLALCHEMY_ENGINE_OPTIONS"]["max_overflow"],
            "enforced via DATABASE_URL sslmode" if "sslmode=" in (app.config.get("SQLALCHEMY_DATABASE_URI") or "") else "not specified in URL",
        )

    return app
