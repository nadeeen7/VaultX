from datetime import datetime
from app.database import db

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    username = db.Column(db.String(80), nullable=True)
    action = db.Column(db.String(100), nullable=False) # e.g. Login, Logout, Update Alert Status, Generate Report
    resource_type = db.Column(db.String(64), nullable=True) # Alert, Incident, Report, Setting, User
    resource_id = db.Column(db.String(64), nullable=True)
    details = db.Column(db.JSON, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.username or 'System',
            'action': self.action,
            'resource_type': self.resource_type,
            'resource_id': str(self.resource_id) if self.resource_id else None,
            'details': self.details or {},
            'ip_address': self.ip_address,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }
