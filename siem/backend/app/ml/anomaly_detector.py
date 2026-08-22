import numpy as np
from sklearn.ensemble import IsolationForest
from datetime import datetime, timedelta
from app.database import db
from app.models.security_event import SecurityEvent
from app.models.ml_anomaly import MLAnomaly

class AnomalyDetector:
    def __init__(self):
        # Isolation Forest instance
        self.model = IsolationForest(
            n_estimators=100,
            contamination=0.1,
            random_state=42
        )
        self.is_trained = False

    def extract_features_for_event(self, event):
        """
        Extract numerical feature vector for an incoming security event:
        1. login_hour: 0 to 23
        2. login_frequency_1h: event count from this user/IP in past 1h
        3. failed_logins_1h: failed logins count from this IP/user in past 1h
        4. success_logins_1h: successful logins count in past 1h
        5. unique_ips_1h: unique IPs seen for this user in past 1h
        6. is_new_ip: 1 if source IP never seen before for this user, else 0
        7. request_freq_1m: request count in past 1 minute
        """
        now = event.timestamp or datetime.utcnow()
        one_hour_ago = now - timedelta(hours=1)
        one_min_ago = now - timedelta(minutes=1)

        login_hour = now.hour

        # Historical window queries
        recent_events = SecurityEvent.query.filter(
            SecurityEvent.timestamp >= one_hour_ago,
            SecurityEvent.timestamp <= now
        ).all()

        user_events = [e for e in recent_events if e.username and e.username == event.username]
        ip_events = [e for e in recent_events if e.source_ip == event.source_ip]

        login_freq_1h = len(user_events) if event.username else len(ip_events)
        failed_logins_1h = sum(1 for e in (user_events or ip_events) if e.status == 'failed' or 'failed' in (e.event_type or ''))
        success_logins_1h = sum(1 for e in (user_events or ip_events) if e.status == 'success' or 'success' in (e.event_type or ''))

        unique_ips = len(set(e.source_ip for e in user_events)) if event.username else 1

        # Check if IP has ever been seen before for this user
        if event.username:
            prior_count = SecurityEvent.query.filter(
                SecurityEvent.username == event.username,
                SecurityEvent.source_ip == event.source_ip,
                SecurityEvent.timestamp < now
            ).count()
            is_new_ip = 1 if prior_count == 0 else 0
        else:
            is_new_ip = 0

        # Request frequency in 1 minute
        request_freq_1m = sum(1 for e in ip_events if e.timestamp >= one_min_ago)

        feature_vector = [
            float(login_hour),
            float(login_freq_1h),
            float(failed_logins_1h),
            float(success_logins_1h),
            float(unique_ips),
            float(is_new_ip),
            float(request_freq_1m)
        ]

        feature_names = {
            'login_hour': login_hour,
            'login_freq_1h': login_freq_1h,
            'failed_logins_1h': failed_logins_1h,
            'success_logins_1h': success_logins_1h,
            'unique_ips_1h': unique_ips,
            'is_new_ip': bool(is_new_ip),
            'request_freq_1m': request_freq_1m
        }

        return feature_vector, feature_names

    def train_on_history(self, sample_events=None):
        """Train Isolation Forest on baseline historical events."""
        if not sample_events:
            sample_events = SecurityEvent.query.order_by(SecurityEvent.timestamp.desc()).limit(500).all()

        if len(sample_events) < 10:
            # Generate synthetic baseline normal vector if database is fresh
            X = np.array([
                [9.0, 2.0, 0.0, 1.0, 1.0, 0.0, 1.0],
                [10.0, 3.0, 0.0, 2.0, 1.0, 0.0, 2.0],
                [14.0, 1.0, 0.0, 1.0, 1.0, 0.0, 1.0],
                [15.0, 4.0, 0.0, 3.0, 1.0, 0.0, 2.0],
                [11.0, 2.0, 0.0, 1.0, 1.0, 0.0, 1.0],
                [16.0, 5.0, 0.0, 4.0, 1.0, 0.0, 3.0],
                [12.0, 1.0, 0.0, 1.0, 1.0, 0.0, 1.0],
                [13.0, 2.0, 0.0, 2.0, 1.0, 0.0, 2.0],
                [17.0, 3.0, 0.0, 2.0, 1.0, 0.0, 1.0],
                [10.0, 1.0, 0.0, 1.0, 1.0, 0.0, 1.0]
            ])
        else:
            X = []
            for ev in sample_events:
                vec, _ = self.extract_features_for_event(ev)
                X.append(vec)
            X = np.array(X)

        self.model.fit(X)
        self.is_trained = True

    def analyze_event(self, event):
        """Evaluates an event for behavioral anomaly score."""
        if not self.is_trained:
            self.train_on_history()

        vec, feature_dict = self.extract_features_for_event(event)
        X = np.array([vec])

        # Isolation forest decision function (lower/negative values mean anomalous)
        raw_score = float(self.model.decision_function(X)[0])
        prediction = int(self.model.predict(X)[0]) # -1 for anomaly, 1 for normal

        # Map raw score [-0.5, 0.5] to a normalized risk score [0.0, 1.0]
        # More negative decision_function => higher anomaly probability score
        anomaly_score = round(float(np.clip((0.2 - raw_score) / 0.4, 0.0, 1.0)), 2)
        is_anomaly = (prediction == -1) or (anomaly_score >= 0.70)

        # Generate human-readable reasoning
        reasons = []
        if feature_dict['failed_logins_1h'] >= 3:
            reasons.append(f"Elevated failed logins count ({feature_dict['failed_logins_1h']}/hr)")
        if feature_dict['is_new_ip']:
            reasons.append("Authentication attempt from previously unobserved IP address")
        if feature_dict['request_freq_1m'] > 15:
            reasons.append(f"High request frequency burst ({feature_dict['request_freq_1m']} req/min)")
        if feature_dict['login_hour'] < 6 or feature_dict['login_hour'] > 22:
            reasons.append(f"Unusual login timeframe (Hour: {feature_dict['login_hour']}:00)")

        reasoning_str = "; ".join(reasons) if reasons else "Behavioral profile deviates from normal baseline pattern."

        ml_record = MLAnomaly(
            event_id=event.id,
            username=event.username,
            source_ip=event.source_ip,
            anomaly_score=anomaly_score,
            is_anomaly=is_anomaly,
            feature_vector=feature_dict,
            reasoning=reasoning_str,
            timestamp=event.timestamp or datetime.utcnow()
        )
        db.session.add(ml_record)
        db.session.commit()

        return anomaly_score, is_anomaly, reasoning_str, feature_dict

# Global singleton
anomaly_detector = AnomalyDetector()
