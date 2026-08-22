import pytest
import json
from app import create_app
from app.database import db
from app.models.user import User
from app.models.security_event import SecurityEvent
from app.models.alert import Alert
from app.detection.rules import detection_engine
from app.detection.risk_engine import calculate_transparent_risk_score
from app.ml.anomaly_detector import anomaly_detector

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client

def test_login_and_auth(client):
    res = client.post('/api/auth/login', json={
        'username': 'admin',
        'password': 'admin123'
    })
    assert res.status_code == 200
    data = res.get_json()
    assert 'token' in data
    assert data['user']['username'] == 'admin'

def test_rule_1_brute_force_detection(client):
    with client.application.app_context():
        # Insert 5 failed logins
        for i in range(5):
            evt = SecurityEvent(
                external_id=f"test-bf-{i}",
                source_app="SecureBank Lab",
                event_type="login_failed",
                status="failed",
                username="admin",
                source_ip="192.168.1.100"
            )
            db.session.add(evt)
        db.session.commit()

        latest = SecurityEvent.query.filter_by(external_id="test-bf-4").first()
        alerts = detection_engine.evaluate_rules(latest)
        assert len(alerts) >= 1
        assert alerts[0]['mitre_technique_id'] == 'T1110'
        assert 'Brute Force' in alerts[0]['title']

def test_transparent_risk_scoring(client):
    alert_data = {
        'severity': 'HIGH',
        'title': 'Possible Brute Force Attack',
        'evidence': [1, 2, 3, 4, 5, 6],
        'factors': {'is_new_source': True}
    }
    score, breakdown = calculate_transparent_risk_score(alert_data, ml_anomaly_score=0.85)
    assert score >= 60.0
    assert len(breakdown['breakdown']) >= 3
