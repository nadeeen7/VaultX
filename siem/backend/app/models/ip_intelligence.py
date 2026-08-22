from datetime import datetime
from app.database import db

class IPIntelligence(db.Model):
    __tablename__ = 'ip_intelligence'

    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(45), unique=True, nullable=False, index=True)
    country = db.Column(db.String(100), nullable=True)
    country_code = db.Column(db.String(10), nullable=True)
    region = db.Column(db.String(100), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    isp = db.Column(db.String(150), nullable=True)
    org = db.Column(db.String(150), nullable=True)
    asn = db.Column(db.String(30), nullable=True)
    timezone = db.Column(db.String(50), nullable=True)
    is_private = db.Column(db.Boolean, default=False)
    is_malicious_flag = db.Column(db.Boolean, default=False)
    raw_json = db.Column(db.JSON, nullable=True)
    event_count = db.Column(db.Integer, default=0)
    alert_count = db.Column(db.Integer, default=0)
    first_seen = db.Column(db.DateTime, nullable=True)
    last_seen = db.Column(db.DateTime, nullable=True)
    cached_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def to_dict(self):
        return {
            'id': self.id,
            'ip_address': self.ip_address,
            'country': self.country or ('Private Network' if self.is_private else 'Unknown'),
            'country_code': self.country_code,
            'region': self.region or 'N/A',
            'city': self.city or 'N/A',
            'latitude': self.latitude,
            'longitude': self.longitude,
            'isp': self.isp or ('Local Infrastructure' if self.is_private else 'Unknown ISP'),
            'org': self.org or 'N/A',
            'asn': self.asn or 'N/A',
            'timezone': self.timezone or 'N/A',
            'is_private': self.is_private,
            'is_malicious_flag': self.is_malicious_flag,
            'event_count': self.event_count or 0,
            'alert_count': self.alert_count or 0,
            'first_seen': self.first_seen.isoformat() if self.first_seen else None,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
            'cached_at': self.cached_at.isoformat() if self.cached_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
