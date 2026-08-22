import os
from flask import Flask, jsonify
from flask_cors import CORS
from app.config import Config
from app.database import db, bcrypt, socketio
from app.routes import register_routes
from app.collectors.securebank_collector import securebank_collector
from app.mitre.mitre_mapping import seed_mitre_techniques
from app.models.user import User

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize CORS - allow Bank frontend and SIEM frontend
    CORS(app, resources={
        r"/api/*": {
            "origins": [
                "http://localhost:5173",
                "http://localhost:5174",
                "http://localhost:5000",
            ],
            "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization", "X-API-Key"],
        }
    })

    # Determine database: try PostgreSQL first, fallback to SQLite
    db_uri = app.config['DATABASE_URL']
    db_label = 'PostgreSQL'
    try:
        import psycopg2
        conn = psycopg2.connect(app.config['DATABASE_URL'])
        conn.close()
        print("[Database] Successfully connected to PostgreSQL database.")
    except Exception as pg_err:
        print(f"[Database] PostgreSQL unavailable ({pg_err}). Falling back to SQLite.")
        db_uri = app.config['SQLITE_FALLBACK_URL']
        db_label = 'SQLite'

    app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
    db.init_app(app)
    print(f"[Database] Using {db_label} database.")

    bcrypt.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*")

    # Register API blueprints
    register_routes(app)

    # Health check endpoint
    @app.route('/api/health', methods=['GET'])
    def health_check():
        db_ok = False
        try:
            db.session.execute(db.text('SELECT 1'))
            db_ok = True
        except Exception:
            pass
        return jsonify({
            'status': 'ok',
            'service': 'siem-backend',
            'database': 'connected' if db_ok else 'disconnected',
            'database_type': db_label,
        }), 200

    # Initialize database tables, seed default Admin user & MITRE database
    with app.app_context():
        db.create_all()
        seed_mitre_techniques()

        # Seed default SOC Admin & Analyst accounts if fresh DB
        if not User.query.filter_by(username='admin').first():
            admin_user = User(
                username='admin',
                email='admin@soc.minisiem.internal',
                role='Admin'
            )
            admin_user.set_password('admin123')
            db.session.add(admin_user)

            analyst_user = User(
                username='analyst',
                email='analyst@soc.minisiem.internal',
                role='Security Analyst'
            )
            analyst_user.set_password('analyst123')
            db.session.add(analyst_user)

            viewer_user = User(
                username='viewer',
                email='viewer@soc.minisiem.internal',
                role='Viewer'
            )
            viewer_user.set_password('viewer123')
            db.session.add(viewer_user)

            db.session.commit()
            print("[Database] Default SOC users created: admin/admin123, analyst/analyst123, viewer/viewer123.")

    # Start SecureBank Background Collector
    securebank_collector.start(app)

    return app
