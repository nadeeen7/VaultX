"""
Advanced Authentication Correlation Engine

Detects sophisticated attack patterns by correlating multiple security events
across time windows, usernames, and source IPs. Operates on top of the existing
detection rule engine without replacing it.

Detection Rules:
  1. Brute Force (same user, same IP, repeated failures)
  2. Password Spraying (same source IP, many different usernames, failures)
  3. Distributed Authentication Anomaly (many users, many IPs, failures)
  4. Multi-Source Account Attack (one user, many source IPs, failures)
  5. Suspicious Auth Success (failures followed by success)
  6. Potential Account Compromise (failures -> success -> sensitive action)
"""

from datetime import datetime, timedelta
from sqlalchemy import func, distinct
from app.database import db, socketio
from app.models.security_event import SecurityEvent
from app.models.setting import Setting


def _get_config(key, default_val):
    """Fetch a configurable threshold from the settings table, or return default."""
    try:
        setting = Setting.query.filter_by(key=key).first()
        if setting:
            return type(default_val)(setting.value)
    except Exception:
        pass
    return default_val


def _check_cooldown(alert_key, window_minutes=15):
    """
    Prevent duplicate alerts for the same correlation pattern within a cooldown window.
    Uses the Setting table to track last-alerted timestamps.
    Returns True if a cooldown is active (should skip), False if we can alert.
    """
    cooldown_key = f"cooldown_{alert_key}"
    try:
        setting = Setting.query.filter_by(key=cooldown_key).first()
        if setting and setting.value:
            last_alerted = datetime.fromisoformat(setting.value)
            if datetime.utcnow() - last_alerted < timedelta(minutes=window_minutes):
                return True
            # Update the timestamp
            setting.value = datetime.utcnow().isoformat()
        else:
            if not setting:
                setting = Setting(
                    key=cooldown_key,
                    value=datetime.utcnow().isoformat(),
                    description=f"Cooldown tracker for {alert_key} alerts"
                )
                db.session.add(setting)
            else:
                setting.value = datetime.utcnow().isoformat()
        db.session.commit()
    except Exception:
        pass
    return False


def _safe_event_list(events):
    """Convert SecurityEvent objects to dicts for evidence storage."""
    return [e.to_dict() if hasattr(e, 'to_dict') else str(e) for e in events]


class CorrelationEngine:
    """
    Evaluates incoming events against multi-event correlation rules.
    Returns a list of triggered alert dictionaries with evidence and factors.
    """

    def evaluate(self, event):
        """
        Main entry point: evaluate a newly arrived event against all
        correlation rules. Returns list of alert dicts.
        """
        alerts = []

        alerts.extend(self._rule_brute_force(event))
        alerts.extend(self._rule_password_spraying(event))
        alerts.extend(self._rule_distributed_auth(event))
        alerts.extend(self._rule_multi_source_account(event))
        alerts.extend(self._rule_suspicious_auth_success(event))
        alerts.extend(self._rule_account_compromise(event))

        return alerts

    # ─────────────────────────────────────────────
    # RULE 1: Brute Force (same user/IP, failures)
    # ─────────────────────────────────────────────
    def _rule_brute_force(self, event):
        """
        Detect repeated failed logins for the same user from the same source IP.
        Triggers when the count reaches the configured threshold within the window.
        """
        if event.status != 'failed':
            return []

        window_mins = _get_config('brute_force_window_mins', 5)
        threshold = _get_config('brute_force_threshold', 5)

        now = event.timestamp or datetime.utcnow()
        window_start = now - timedelta(minutes=window_mins)

        failed_count = SecurityEvent.query.filter(
            SecurityEvent.source_ip == event.source_ip,
            SecurityEvent.username == event.username,
            SecurityEvent.timestamp >= window_start,
            SecurityEvent.timestamp <= now,
            SecurityEvent.status == 'failed',
        ).count()

        if failed_count < threshold:
            return []

        if _check_cooldown(f"brute_force_{event.source_ip}_{event.username}", window_mins):
            return []

        # Gather evidence
        evidence_events = SecurityEvent.query.filter(
            SecurityEvent.source_ip == event.source_ip,
            SecurityEvent.username == event.username,
            SecurityEvent.timestamp >= window_start,
            SecurityEvent.timestamp <= now,
            SecurityEvent.status == 'failed',
        ).order_by(SecurityEvent.timestamp.desc()).limit(20).all()

        severity = 'HIGH' if failed_count < 10 else 'CRITICAL'

        return [{
            'title': 'Possible Brute Force Attack',
            'description': (
                f'{failed_count} failed login attempts for user "{event.username}" '
                f'from source IP {event.source_ip} within {window_mins} minutes.'
            ),
            'severity': severity,
            'mitre_technique_id': 'T1110',
            'rule_name': 'Correlation Rule 1: Brute Force',
            'source_ip': event.source_ip,
            'username': event.username,
            'evidence': _safe_event_list(evidence_events),
            'factors': {
                'failed_attempts_count': failed_count,
                'unique_users': 1,
                'unique_source_ips': 1,
                'time_window_mins': window_mins,
                'source_ip': event.source_ip,
                'username': event.username,
                'detection_rule': 'BRUTE_FORCE',
            },
        }]

    # ─────────────────────────────────────────────
    # RULE 2: Password Spraying (same IP, many users)
    # ─────────────────────────────────────────────
    def _rule_password_spraying(self, event):
        """
        Detect password spraying: many different usernames targeted with
        failed logins from the same source IP within a time window.
        """
        if event.status != 'failed':
            return []

        window_mins = _get_config('password_spray_window_mins', 10)
        user_threshold = _get_config('password_spray_user_threshold', 5)

        now = event.timestamp or datetime.utcnow()
        window_start = now - timedelta(minutes=window_mins)

        # Count distinct usernames with failed logins from this IP
        distinct_users = db.session.query(
            func.count(distinct(SecurityEvent.username))
        ).filter(
            SecurityEvent.source_ip == event.source_ip,
            SecurityEvent.timestamp >= window_start,
            SecurityEvent.timestamp <= now,
            SecurityEvent.status == 'failed',
            SecurityEvent.username.isnot(None),
        ).scalar()

        if distinct_users < user_threshold:
            return []

        if _check_cooldown(f"password_spray_{event.source_ip}", window_mins):
            return []

        # Gather evidence
        evidence_events = SecurityEvent.query.filter(
            SecurityEvent.source_ip == event.source_ip,
            SecurityEvent.timestamp >= window_start,
            SecurityEvent.timestamp <= now,
            SecurityEvent.status == 'failed',
        ).order_by(SecurityEvent.timestamp.asc()).limit(30).all()

        total_failures = len(evidence_events)
        targeted_users = list(set(
            e.username for e in evidence_events if e.username
        ))

        return [{
            'title': 'Possible Password Spraying Attack',
            'description': (
                f'{total_failures} failed authentication attempts targeting '
                f'{distinct_users} different usernames from source IP {event.source_ip} '
                f'within {window_mins} minutes.'
            ),
            'severity': 'HIGH',
            'mitre_technique_id': 'T1110',
            'rule_name': 'Correlation Rule 2: Password Spraying',
            'source_ip': event.source_ip,
            'username': None,  # Multiple users targeted
            'evidence': _safe_event_list(evidence_events),
            'factors': {
                'failed_attempts_count': total_failures,
                'unique_users': distinct_users,
                'targeted_usernames': targeted_users[:10],
                'unique_source_ips': 1,
                'time_window_mins': window_mins,
                'source_ip': event.source_ip,
                'detection_rule': 'PASSWORD_SPRAYING',
            },
        }]

    # ─────────────────────────────────────────────
    # RULE 3: Distributed Auth Anomaly (many users, many IPs, failures)
    # ─────────────────────────────────────────────
    def _rule_distributed_auth(self, event):
        """
        Detect distributed authentication anomalies: many different usernames
        AND many different source IPs with repeated failures in a broader
        time window. This catches slow distributed attacks that simple
        same-IP rules would miss.
        """
        if event.status != 'failed':
            return []

        window_mins = _get_config('distributed_auth_window_mins', 60)
        total_threshold = _get_config('distributed_auth_threshold', 5)
        unique_ip_threshold = _get_config('distributed_auth_unique_ip_threshold', 3)
        unique_user_threshold = _get_config('distributed_auth_unique_user_threshold', 3)

        now = event.timestamp or datetime.utcnow()
        window_start = now - timedelta(minutes=window_mins)

        # Count total failures from all sources in window
        total_failures = SecurityEvent.query.filter(
            SecurityEvent.timestamp >= window_start,
            SecurityEvent.timestamp <= now,
            SecurityEvent.status == 'failed',
        ).count()

        if total_failures < total_threshold:
            return []

        # Count distinct IPs
        distinct_ips = db.session.query(
            func.count(distinct(SecurityEvent.source_ip))
        ).filter(
            SecurityEvent.timestamp >= window_start,
            SecurityEvent.timestamp <= now,
            SecurityEvent.status == 'failed',
        ).scalar()

        # Count distinct usernames
        distinct_users = db.session.query(
            func.count(distinct(SecurityEvent.username))
        ).filter(
            SecurityEvent.timestamp >= window_start,
            SecurityEvent.timestamp <= now,
            SecurityEvent.status == 'failed',
            SecurityEvent.username.isnot(None),
        ).scalar()

        # All thresholds must be met
        if distinct_ips < unique_ip_threshold or distinct_users < unique_user_threshold:
            return []

        if _check_cooldown(f"distributed_auth", window_mins):
            return []

        # Gather evidence
        evidence_events = SecurityEvent.query.filter(
            SecurityEvent.timestamp >= window_start,
            SecurityEvent.timestamp <= now,
            SecurityEvent.status == 'failed',
        ).order_by(SecurityEvent.timestamp.asc()).limit(30).all()

        targeted_users = list(set(e.username for e in evidence_events if e.username))
        source_ips = list(set(e.source_ip for e in evidence_events))

        return [{
            'title': 'Distributed Authentication Anomaly',
            'description': (
                f'Detected {total_failures} failed authentication attempts across '
                f'{distinct_users} different usernames and {distinct_ips} source IPs '
                f'within {window_mins} minutes. This pattern suggests a coordinated '
                f'or distributed attack.'
            ),
            'severity': 'HIGH' if distinct_ips >= 4 and distinct_users >= 4 else 'MEDIUM',
            'mitre_technique_id': 'T1110',
            'rule_name': 'Correlation Rule 3: Distributed Authentication Anomaly',
            'source_ip': event.source_ip,
            'username': None,  # Multiple users
            'evidence': _safe_event_list(evidence_events),
            'factors': {
                'failed_attempts_count': total_failures,
                'unique_users': distinct_users,
                'unique_source_ips': distinct_ips,
                'targeted_usernames': targeted_users[:10],
                'source_ips': source_ips[:10],
                'time_window_mins': window_mins,
                'detection_rule': 'DISTRIBUTED_AUTH_ANOMALY',
            },
        }]

    # ─────────────────────────────────────────────
    # RULE 4: Multi-Source Account Attack (one user, many IPs)
    # ─────────────────────────────────────────────
    def _rule_multi_source_account(self, event):
        """
        Detect a single account being targeted from multiple source IPs.
        """
        if event.status != 'failed' or not event.username:
            return []

        window_mins = _get_config('multi_source_account_window_mins', 15)
        ip_threshold = _get_config('multi_source_account_threshold', 3)

        now = event.timestamp or datetime.utcnow()
        window_start = now - timedelta(minutes=window_mins)

        # Count distinct IPs targeting this specific username
        distinct_ips = db.session.query(
            func.count(distinct(SecurityEvent.source_ip))
        ).filter(
            SecurityEvent.username == event.username,
            SecurityEvent.timestamp >= window_start,
            SecurityEvent.timestamp <= now,
            SecurityEvent.status == 'failed',
        ).scalar()

        if distinct_ips < ip_threshold:
            return []

        if _check_cooldown(f"multi_source_{event.username}", window_mins):
            return []

        # Gather evidence
        evidence_events = SecurityEvent.query.filter(
            SecurityEvent.username == event.username,
            SecurityEvent.timestamp >= window_start,
            SecurityEvent.timestamp <= now,
            SecurityEvent.status == 'failed',
        ).order_by(SecurityEvent.timestamp.asc()).limit(20).all()

        total_failures = len(evidence_events)
        source_ips = list(set(e.source_ip for e in evidence_events))

        return [{
            'title': 'Multi-Source Account Attack',
            'description': (
                f'Account "{event.username}" is being targeted from '
                f'{distinct_ips} different source IPs with {total_failures} failed '
                f'authentication attempts within {window_mins} minutes.'
            ),
            'severity': 'HIGH',
            'mitre_technique_id': 'T1110',
            'rule_name': 'Correlation Rule 4: Multi-Source Account Attack',
            'source_ip': event.source_ip,
            'username': event.username,
            'evidence': _safe_event_list(evidence_events),
            'factors': {
                'failed_attempts_count': total_failures,
                'unique_users': 1,
                'unique_source_ips': distinct_ips,
                'source_ips': source_ips[:10],
                'time_window_mins': window_mins,
                'targeted_account': event.username,
                'detection_rule': 'MULTI_SOURCE_ACCOUNT_ATTACK',
            },
        }]

    # ─────────────────────────────────────────────
    # RULE 5: Suspicious Auth Success (failures -> success)
    # ─────────────────────────────────────────────
    def _rule_suspicious_auth_success(self, event):
        """
        Detect successful authentication preceded by multiple failures
        from the same user or same source IP. This strongly suggests
        credential guessing was successful.
        """
        if event.status != 'success':
            return []

        # Only check for login-related successful events
        event_type = (event.event_type or '').lower()
        if 'login' not in event_type and event_type not in ('admin_login',):
            return []

        window_mins = _get_config('suspicious_success_window_mins', 15)
        fail_threshold = _get_config('suspicious_success_fail_threshold', 3)

        now = event.timestamp or datetime.utcnow()
        window_start = now - timedelta(minutes=window_mins)

        # Count failed logins for same username OR same IP prior to this success
        failed_prior = SecurityEvent.query.filter(
            SecurityEvent.timestamp >= window_start,
            SecurityEvent.timestamp < now,
            ((SecurityEvent.username == event.username) | (SecurityEvent.source_ip == event.source_ip)),
            SecurityEvent.status == 'failed',
        ).count()

        if failed_prior < fail_threshold:
            return []

        if _check_cooldown(f"suspicious_success_{event.username}_{event.source_ip}", window_mins):
            return []

        # Gather evidence: the failures + this success
        prior_events = SecurityEvent.query.filter(
            SecurityEvent.timestamp >= window_start,
            SecurityEvent.timestamp <= now,
            ((SecurityEvent.username == event.username) | (SecurityEvent.source_ip == event.source_ip)),
        ).order_by(SecurityEvent.timestamp.asc()).limit(20).all()

        severity = 'CRITICAL' if failed_prior >= 5 else 'HIGH'

        return [{
            'title': 'Suspicious Authentication Success After Multiple Failures',
            'description': (
                f'User "{event.username}" successfully authenticated from '
                f'IP {event.source_ip} after {failed_prior} failed attempts '
                f'within {window_mins} minutes. This may indicate successful '
                f'credential guessing.'
            ),
            'severity': severity,
            'mitre_technique_id': 'T1078',
            'rule_name': 'Correlation Rule 5: Suspicious Auth Success',
            'source_ip': event.source_ip,
            'username': event.username,
            'evidence': _safe_event_list(prior_events),
            'factors': {
                'failed_prior_count': failed_prior,
                'successful_account': event.username,
                'source_ip': event.source_ip,
                'time_window_mins': window_mins,
                'compromise_flag': True,
                'detection_rule': 'SUSPICIOUS_AUTH_SUCCESS',
            },
        }]

    # ─────────────────────────────────────────────
    # RULE 6: Account Compromise (failures -> success -> sensitive action)
    # ─────────────────────────────────────────────
    def _rule_account_compromise(self, event):
        """
        Detect potential account compromise: multiple failures, then a
        successful login, then a sensitive transaction (transfer) from
        the same user/IP within a broader window.
        """
        event_type = (event.event_type or '').lower()
        if 'transfer' not in event_type:
            return []

        window_mins = _get_config('compromise_window_mins', 30)
        fail_threshold = _get_config('compromise_fail_threshold', 3)

        now = event.timestamp or datetime.utcnow()
        window_start = now - timedelta(minutes=window_mins)

        if not event.username:
            return []

        # Look for a successful login for this user within the window
        success_login = SecurityEvent.query.filter(
            SecurityEvent.username == event.username,
            SecurityEvent.timestamp >= window_start,
            SecurityEvent.timestamp < now,
            SecurityEvent.status == 'success',
            SecurityEvent.event_type.like('%login%'),
        ).order_by(SecurityEvent.timestamp.desc()).first()

        if not success_login:
            return []

        # Count failures before that successful login
        fail_count = SecurityEvent.query.filter(
            SecurityEvent.username == event.username,
            SecurityEvent.timestamp >= window_start,
            SecurityEvent.timestamp < success_login.timestamp,
            SecurityEvent.status == 'failed',
        ).count()

        if fail_count < fail_threshold:
            return []

        if _check_cooldown(f"account_compromise_{event.username}", window_mins):
            return []

        # Gather full timeline: failures -> success -> this transaction
        timeline_events = SecurityEvent.query.filter(
            SecurityEvent.username == event.username,
            SecurityEvent.timestamp >= window_start,
            SecurityEvent.timestamp <= now,
        ).order_by(SecurityEvent.timestamp.asc()).limit(30).all()

        return [{
            'title': 'Potential Account Compromise',
            'description': (
                f'User "{event.username}" performed a sensitive transaction '
                f'(transfer) after {fail_count} failed login attempts and a '
                f'successful authentication within {window_mins} minutes. '
                f'This pattern strongly suggests the account may have been '
                f'compromised through credential guessing.'
            ),
            'severity': 'CRITICAL',
            'mitre_technique_id': 'T1078',
            'rule_name': 'Correlation Rule 6: Account Compromise',
            'source_ip': event.source_ip,
            'username': event.username,
            'evidence': _safe_event_list(timeline_events),
            'factors': {
                'failed_prior_count': fail_count,
                'successful_login_time': success_login.timestamp.isoformat() if success_login.timestamp else None,
                'successful_login_ip': success_login.source_ip,
                'transaction_time': event.timestamp.isoformat() if event.timestamp else None,
                'sensitive_action': event.event_type,
                'time_window_mins': window_mins,
                'compromise_flag': True,
                'detection_rule': 'ACCOUNT_COMPROMISE',
            },
        }]


# Global instance
correlation_engine = CorrelationEngine()
