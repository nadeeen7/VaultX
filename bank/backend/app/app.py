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

        return jsonify({
            "status": "ok",
            "service": "bank-backend",
            "database": "connected" if db_ok else "disconnected",
            "siem_configured": siem_configured,
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

    return app
