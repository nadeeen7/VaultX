from datetime import datetime
from app.database import db

class SecurityEvent(db.Model):
    __tablename__ = 'security_events'

    id = db.Column(db.Integer, primary_key=True)
    external_id = db.Column(db.String(128), unique=True, nullable=True, index=True)
    source_app = db.Column(db.String(64), nullable=False, default='SecureBank Lab')
    event_type = db.Column(db.String(64), nullable=False, index=True) # e.g. login_success, login_failed, admin_access_denied, high_request_rate
    status = db.Column(db.String(32), nullable=True) # success, failed, denied
    username = db.Column(db.String(80), nullable=True, index=True)
    source_ip = db.Column(db.String(45), nullable=False, index=True)
    destination_ip = db.Column(db.String(45), nullable=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    details = db.Column(db.JSON, nullable=True) # JSON dictionary of additional metadata
    raw_data = db.Column(db.Text, nullable=True)
    normalized_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed = db.Column(db.Boolean, default=False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def to_dict(self):
        return {
            'id': self.id,
            'external_id': self.external_id,
            'source_app': self.source_app,
            'event_type': self.event_type,
            'status': self.status,
            'username': self.username,
            'source_ip': self.source_ip,
            'destination_ip': self.destination_ip,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'details': self.details or {},
            'raw_data': self.raw_data,
            'normalized_at': self.normalized_at.isoformat() if self.normalized_at else None,
            'processed': self.processed
        }
