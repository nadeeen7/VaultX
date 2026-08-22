from datetime import datetime
from app.database import db

class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    alert_id = db.Column(db.Integer, db.ForeignKey('alerts.id'), nullable=True)
    incident_id = db.Column(db.Integer, db.ForeignKey('incidents.id'), nullable=True)
    channel = db.Column(db.String(50), nullable=False) # discord, slack, email, webhook
    status = db.Column(db.String(30), nullable=False, default='SENT') # SENT, FAILED, PENDING
    payload = db.Column(db.JSON, nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def to_dict(self):
        return {
            'id': self.id,
            'alert_id': self.alert_id,
            'incident_id': self.incident_id,
            'channel': self.channel,
            'status': self.status,
            'payload': self.payload or {},
            'error_message': self.error_message,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None
        }
