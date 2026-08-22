from datetime import datetime, timedelta
from app.database import db
from app.models.security_event import SecurityEvent
from app.models.setting import Setting

def get_rule_config(key, default_val):
    """Fetch configurable threshold settings from database or return default."""
    try:
        setting = Setting.query.filter_by(key=key).first()
        if setting:
            return type(default_val)(setting.value)
    except Exception:
        pass
    return default_val

class DetectionRuleEngine:
    def __init__(self):
        pass

    def evaluate_rules(self, event, ip_info=None):
        """
        Evaluates incoming normalized event against configured security rules.
        Returns a list of triggered alert dictionaries.
        """
        alerts_triggered = []

        now = event.timestamp or datetime.utcnow()

        # Configurable Rule Parameters
        brute_force_window_mins = get_rule_config('brute_force_window_mins', 5)
        brute_force_threshold = get_rule_config('brute_force_threshold', 5)

        admin_abuse_window_mins = get_rule_config('admin_abuse_window_mins', 10)
        admin_abuse_threshold = get_rule_config('admin_abuse_threshold', 3)

        high_freq_window_mins = get_rule_config('high_freq_window_mins', 1)
        high_freq_threshold = get_rule_config('high_freq_threshold', 20)

        # RULE 1: Repeated Failed Logins (Brute Force)
        if event.status == 'failed' or 'failed' in (event.event_type or '').lower():
            window_start = now - timedelta(minutes=brute_force_window_mins)
            failed_count = SecurityEvent.query.filter(
                SecurityEvent.source_ip == event.source_ip,
                SecurityEvent.timestamp >= window_start,
                SecurityEvent.timestamp <= now,
                ((SecurityEvent.status == 'failed') | (SecurityEvent.event_type.like('%failed%')))
            ).count()

            if failed_count >= brute_force_threshold:
                recent_events = SecurityEvent.query.filter(
                    SecurityEvent.source_ip == event.source_ip,
                    SecurityEvent.timestamp >= window_start,
                    SecurityEvent.timestamp <= now
                ).all()

                alerts_triggered.append({
                    'title': 'Possible Brute Force Attack',
                    'description': f'Detected {failed_count} failed login attempts from source IP {event.source_ip} within {brute_force_window_mins} minutes.',
                    'severity': 'HIGH' if failed_count < 10 else 'CRITICAL',
                    'mitre_technique_id': 'T1110',
                    'rule_name': 'Rule 1: Repeated Failed Logins',
                    'evidence': [e.to_dict() for e in recent_events[-10:]],
                    'factors': {
                        'failed_attempts_count': failed_count,
                        'time_window_mins': brute_force_window_mins,
                        'source_ip': event.source_ip
                    }
                })

        # RULE 2: Multiple Failed Logins Followed by Successful Login (Possible Account Compromise)
        if event.status == 'success' or 'success' in (event.event_type or '').lower():
            window_start = now - timedelta(minutes=15)
            # Check for failed logins on same user or IP immediately prior to this success
            failed_prior = SecurityEvent.query.filter(
                SecurityEvent.timestamp >= window_start,
                SecurityEvent.timestamp <= now,
                ((SecurityEvent.source_ip == event.source_ip) | (SecurityEvent.username == event.username)),
                ((SecurityEvent.status == 'failed') | (SecurityEvent.event_type.like('%failed%')))
            ).count()

            if failed_prior >= 3:
                recent_events = SecurityEvent.query.filter(
                    SecurityEvent.timestamp >= window_start,
                    SecurityEvent.timestamp <= now,
                    ((SecurityEvent.source_ip == event.source_ip) | (SecurityEvent.username == event.username))
                ).all()

                alerts_triggered.append({
                    'title': 'Possible Account Compromise',
                    'description': f'Successful authentication for user "{event.username or "Unknown"}" from IP {event.source_ip} following {failed_prior} failed attempts.',
                    'severity': 'CRITICAL',
                    'mitre_technique_id': 'T1078',
                    'rule_name': 'Rule 2: Failed Logins Followed by Success',
                    'evidence': [e.to_dict() for e in recent_events[-10:]],
                    'factors': {
                        'failed_prior_count': failed_prior,
                        'successful_account': event.username,
                        'source_ip': event.source_ip,
                        'compromise_flag': True
                    }
                })

        # RULE 3: Repeated Unauthorized Admin Access (Privilege/Access Abuse)
        if 'admin' in (event.event_type or '').lower() or 'forbidden' in (event.event_type or '').lower() or event.status == 'denied':
            window_start = now - timedelta(minutes=admin_abuse_window_mins)
            denied_count = SecurityEvent.query.filter(
                SecurityEvent.source_ip == event.source_ip,
                SecurityEvent.timestamp >= window_start,
                SecurityEvent.timestamp <= now,
                ((SecurityEvent.status == 'denied') | (SecurityEvent.event_type.like('%admin%')) | (SecurityEvent.event_type.like('%forbidden%')))
            ).count()

            if denied_count >= admin_abuse_threshold:
                recent_events = SecurityEvent.query.filter(
                    SecurityEvent.source_ip == event.source_ip,
                    SecurityEvent.timestamp >= window_start,
                    SecurityEvent.timestamp <= now
                ).all()

                alerts_triggered.append({
                    'title': 'Possible Privilege / Access Abuse',
                    'description': f'Detected {denied_count} unauthorized administrative access attempts from IP {event.source_ip}.',
                    'severity': 'HIGH',
                    'mitre_technique_id': 'T1068',
                    'rule_name': 'Rule 3: Repeated Unauthorized Admin Access',
                    'evidence': [e.to_dict() for e in recent_events[-10:]],
                    'factors': {
                        'unauthorized_count': denied_count,
                        'source_ip': event.source_ip,
                        'target_user': event.username
                    }
                })

        # RULE 4: High Request Frequency (Automated/Suspicious Activity)
        window_start = now - timedelta(minutes=high_freq_window_mins)
        req_count = SecurityEvent.query.filter(
            SecurityEvent.source_ip == event.source_ip,
            SecurityEvent.timestamp >= window_start,
            SecurityEvent.timestamp <= now
        ).count()

        if req_count >= high_freq_threshold:
            recent_events = SecurityEvent.query.filter(
                SecurityEvent.source_ip == event.source_ip,
                SecurityEvent.timestamp >= window_start,
                SecurityEvent.timestamp <= now
            ).all()

            alerts_triggered.append({
                'title': 'Possible Automated / Suspicious Activity',
                'description': f'High request frequency burst detected: {req_count} events from IP {event.source_ip} within {high_freq_window_mins} minute(s).',
                'severity': 'MEDIUM' if req_count < 40 else 'HIGH',
                'mitre_technique_id': 'T1499',
                'rule_name': 'Rule 4: High Request Frequency',
                'evidence': [e.to_dict() for e in recent_events[-10:]],
                'factors': {
                    'request_count': req_count,
                    'time_window_mins': high_freq_window_mins,
                    'source_ip': event.source_ip
                }
            })

        # RULE 5: New Login Source (Unusual Login Source)
        if event.username and (event.status == 'success' or 'login' in (event.event_type or '').lower()):
            prior_login_count = SecurityEvent.query.filter(
                SecurityEvent.username == event.username,
                SecurityEvent.source_ip == event.source_ip,
                SecurityEvent.timestamp < now
            ).count()

            if prior_login_count == 0:
                alerts_triggered.append({
                    'title': 'Unusual Login Source Detected',
                    'description': f'User "{event.username}" authenticated from a previously unobserved IP address: {event.source_ip}.',
                    'severity': 'MEDIUM',
                    'mitre_technique_id': 'T1078',
                    'rule_name': 'Rule 5: New Login Source',
                    'evidence': [event.to_dict()],
                    'factors': {
                        'new_ip': event.source_ip,
                        'user': event.username,
                        'is_new_source': True
                    }
                })

        return alerts_triggered

# Global instance
detection_engine = DetectionRuleEngine()
