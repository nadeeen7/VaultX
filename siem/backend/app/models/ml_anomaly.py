from datetime import datetime
from app.database import db

class MLAnomaly(db.Model):
    __tablename__ = 'ml_anomalies'

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('security_events.id'), nullable=True)
    username = db.Column(db.String(80), nullable=True, index=True)
    source_ip = db.Column(db.String(45), nullable=False, index=True)
    anomaly_score = db.Column(db.Float, nullable=False) # 0.0 to 1.0 risk normalized score
    is_anomaly = db.Column(db.Boolean, nullable=False, default=False)
    feature_vector = db.Column(db.JSON, nullable=True)
    reasoning = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def to_dict(self):
        return {
            'id': self.id,
            'event_id': self.event_id,
            'username': self.username,
            'source_ip': self.source_ip,
            'anomaly_score': self.anomaly_score,
            'is_anomaly': self.is_anomaly,
            'feature_vector': self.feature_vector or {},
            'reasoning': self.reasoning,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }
