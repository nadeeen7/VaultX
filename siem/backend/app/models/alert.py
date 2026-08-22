from datetime import datetime
from app.database import db

class Alert(db.Model):
    __tablename__ = 'alerts'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    severity = db.Column(db.String(20), nullable=False, default='MEDIUM') # LOW, MEDIUM, HIGH, CRITICAL
    source_ip = db.Column(db.String(45), nullable=False, index=True)
    username = db.Column(db.String(80), nullable=True, index=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    mitre_technique_id = db.Column(db.String(30), nullable=True, index=True)
    evidence = db.Column(db.JSON, nullable=True) # JSON list/object of events / telemetry
    status = db.Column(db.String(30), nullable=False, default='NEW') # NEW, INVESTIGATING, RESOLVED, FALSE_POSITIVE
    risk_score = db.Column(db.Float, nullable=False, default=0.0)
    risk_factors = db.Column(db.JSON, nullable=True) # Explanation of score
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    notes = db.Column(db.JSON, nullable=True) # List of analyst notes
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    assigned_user = db.relationship('User', foreign_keys=[assigned_to_id], lazy='joined')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'severity': self.severity,
            'source_ip': self.source_ip,
            'username': self.username,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'mitre_technique_id': self.mitre_technique_id,
            'evidence': self.evidence or [],
            'status': self.status,
            'risk_score': self.risk_score,
            'risk_factors': self.risk_factors or {},
            'assigned_to': self.assigned_user.username if self.assigned_user else None,
            'assigned_to_id': self.assigned_to_id,
            'notes': self.notes or [],
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
