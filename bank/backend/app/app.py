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
    CORS(app, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}})

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
        return jsonify({
            "status": "ok",
            "service": "bank-backend",
            "database": "connected" if db_ok else "disconnected",
        }), 200

    # Create tables
    with app.app_context():
        db.create_all()

    return app
