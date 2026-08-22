from datetime import datetime
from app.database import db

class MitreTechnique(db.Model):
    __tablename__ = 'mitre_techniques'

    id = db.Column(db.Integer, primary_key=True)
    technique_id = db.Column(db.String(30), unique=True, nullable=False, index=True) # e.g. T1110
    technique_name = db.Column(db.String(150), nullable=False)
    tactic = db.Column(db.String(100), nullable=False) # e.g. Credential Access
    description = db.Column(db.Text, nullable=True)
    platform = db.Column(db.String(100), default='Web Apps, Containers, OS')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def to_dict(self):
        return {
            'id': self.id,
            'technique_id': self.technique_id,
            'technique_name': self.technique_name,
            'tactic': self.tactic,
            'description': self.description,
            'platform': self.platform
        }
