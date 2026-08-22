from app.routes.auth_routes import auth_bp
from app.routes.event_routes import event_bp
from app.routes.alert_routes import alert_bp
from app.routes.incident_routes import incident_bp
from app.routes.mitre_routes import mitre_bp
from app.routes.ip_routes import ip_bp
from app.routes.analytics_routes import analytics_bp
from app.routes.report_routes import report_bp
from app.routes.user_routes import user_bp
from app.routes.settings_routes import settings_bp

def register_routes(app):
    app.register_blueprint(auth_bp)
    app.register_blueprint(event_bp)
    app.register_blueprint(alert_bp)
    app.register_blueprint(incident_bp)
    app.register_blueprint(mitre_bp)
    app.register_blueprint(ip_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(settings_bp)
