from datetime import datetime
from app.database import db

class Incident(db.Model):
    __tablename__ = 'incidents'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(180), nullable=False)
    description = db.Column(db.Text, nullable=True)
    severity = db.Column(db.String(20), nullable=False, default='MEDIUM') # LOW, MEDIUM, HIGH, CRITICAL
    status = db.Column(db.String(30), nullable=False, default='OPEN') # OPEN, INVESTIGATING, RESOLVED, CLOSED
    source_ip = db.Column(db.String(45), nullable=True, index=True)
    affected_user = db.Column(db.String(80), nullable=True, index=True)
    risk_score = db.Column(db.Float, nullable=False, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    incident_events = db.relationship('IncidentEvent', backref='incident', cascade='all, delete-orphan', lazy=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'severity': self.severity,
            'status': self.status,
            'source_ip': self.source_ip,
            'affected_user': self.affected_user,
            'risk_score': self.risk_score,
            'alert_count': len(self.incident_events),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class IncidentEvent(db.Model):
    __tablename__ = 'incident_events'

    id = db.Column(db.Integer, primary_key=True)
    incident_id = db.Column(db.Integer, db.ForeignKey('incidents.id'), nullable=False)
    alert_id = db.Column(db.Integer, db.ForeignKey('alerts.id'), nullable=True)
    security_event_id = db.Column(db.Integer, db.ForeignKey('security_events.id'), nullable=True)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)

    alert = db.relationship('Alert', lazy='joined')
    security_event = db.relationship('SecurityEvent', lazy='joined')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def to_dict(self):
        return {
            'id': self.id,
            'incident_id': self.incident_id,
            'alert_id': self.alert_id,
            'alert': self.alert.to_dict() if self.alert else None,
            'security_event_id': self.security_event_id,
            'security_event': self.security_event.to_dict() if self.security_event else None,
            'added_at': self.added_at.isoformat() if self.added_at else None
        }
