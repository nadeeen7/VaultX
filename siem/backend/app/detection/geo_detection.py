"""
Geographic Anomaly Detection

Detects location-based anomalies as additional security signals:
1. New Country for User — user authenticates from a never-before-seen country
2. Impossible Travel — physically implausible geographic movement speed

These are risk signals, not definitive attack indicators.
They increase risk when combined with other suspicious activity.
"""

from datetime import datetime, timedelta
from sqlalchemy import func, distinct
from app.database import db
from app.models.security_event import SecurityEvent
from app.models.ip_intelligence import IPIntelligence
from app.models.setting import Setting


def _get_config(key, default_val):
    try:
        setting = Setting.query.filter_by(key=key).first()
        if setting:
            return type(default_val)(setting.value)
    except Exception:
        pass
    return default_val


class GeographicDetectionEngine:
    """
    Evaluates geographic signals for security events.
    Returns a list of alert dictionaries triggered by geographic anomalies.
    """

    def evaluate(self, event, ip_info):
        """Evaluate geographic anomaly rules for a given event."""
        alerts = []

        if not ip_info or ip_info.get('is_private'):
            return alerts

        alerts.extend(self._rule_new_country(event, ip_info))
        alerts.extend(self._rule_impossible_travel(event, ip_info))

        return alerts

    def _rule_new_country(self, event, ip_info):
        """
        Detect when a user authenticates from a country they've never
        been seen from before.
        """
        if not event.username or not ip_info.get('country_code'):
            return []

        country_code = ip_info['country_code']
        if country_code in ('XX', 'UN', 'PRIV'):
            return []

        # Check if this user has any events from this country before
        known_countries = db.session.query(
            func.count(distinct(IPIntelligence.country_code))
        ).join(
            SecurityEvent, SecurityEvent.source_ip == IPIntelligence.ip_address
        ).filter(
            SecurityEvent.username == event.username,
            SecurityEvent.source_ip != event.source_ip,
            IPIntelligence.country_code.isnot(None),
            IPIntelligence.country_code.notin_(['XX', 'UN', 'PRIV'])
        ).scalar() or 0

        # Check if this specific country was seen before
        country_seen_before = SecurityEvent.query.join(
            IPIntelligence, SecurityEvent.source_ip == IPIntelligence.ip_address
        ).filter(
            SecurityEvent.username == event.username,
            SecurityEvent.source_ip != event.source_ip,
            IPIntelligence.country_code == country_code
        ).count()

        if country_seen_before > 0:
            return []

        # Only trigger if user has history from other countries
        if known_countries == 0:
            return []

        # Check cooldown
        cooldown_key = f"new_country_{event.username}_{country_code}"
        cooldown_mins = _get_config('new_country_cooldown_mins', 60)
        cooldown_setting = Setting.query.filter_by(key=cooldown_key).first()
        if cooldown_setting and cooldown_setting.value:
            try:
                last_alerted = datetime.fromisoformat(cooldown_setting.value)
                if datetime.utcnow() - last_alerted < timedelta(minutes=cooldown_mins):
                    return []
            except Exception:
                pass

        # Gather evidence
        prior_events = SecurityEvent.query.filter(
            SecurityEvent.username == event.username,
            SecurityEvent.timestamp >= (event.timestamp or datetime.utcnow()) - timedelta(hours=24),
        ).order_by(SecurityEvent.timestamp.asc()).limit(20).all()

        location = f"{ip_info.get('city', 'Unknown')}, {ip_info.get('country', 'Unknown')}"

        return [{
            'title': 'New Geographic Source for User',
            'description': (
                f'User "{event.username}" authenticated from {location} '
                f'({ip_info.get("country_code")}), a country not previously '
                f'associated with this account.'
            ),
            'severity': 'MEDIUM',
            'mitre_technique_id': 'T1078',
            'rule_name': 'Geographic Rule 1: New Country for User',
            'source_ip': event.source_ip,
            'username': event.username,
            'evidence': [e.to_dict() for e in prior_events],
            'factors': {
                'new_country': ip_info.get('country'),
                'new_country_code': country_code,
                'new_city': ip_info.get('city'),
                'detection_rule': 'NEW_COUNTRY_FOR_USER',
            },
        }]

    def _rule_impossible_travel(self, event, ip_info):
        """
        Detect physically impossible geographic movement between events.
        Uses haversine distance and time difference to calculate speed.
        """
        if not event.username or not ip_info.get('latitude') or not ip_info.get('longitude'):
            return []

        now = event.timestamp or datetime.utcnow()
        window_hours = _get_config('impossible_travel_window_hours', 2)
        speed_threshold = _get_config('impossible_travel_speed_kmh', 900)

        lookback = now - timedelta(hours=window_hours)

        # Get the most recent prior login from a different location
        prior_login = SecurityEvent.query.join(
            IPIntelligence, SecurityEvent.source_ip == IPIntelligence.ip_address
        ).filter(
            SecurityEvent.username == event.username,
            SecurityEvent.timestamp >= lookback,
            SecurityEvent.timestamp < now,
            SecurityEvent.status == 'success',
            'login' in SecurityEvent.event_type,
            IPIntelligence.latitude.isnot(None),
            IPIntelligence.longitude.isnot(None),
            SecurityEvent.source_ip != event.source_ip,
        ).order_by(SecurityEvent.timestamp.desc()).first()

        if not prior_login:
            return []

        prior_intel = IPIntelligence.query.filter_by(ip_address=prior_login.source_ip).first()
        if not prior_intel or not prior_intel.latitude or not prior_intel.longitude:
            return []

        # Calculate distance and time
        from app.services.ip_service import haversine_distance
        distance_km = haversine_distance(
            prior_intel.latitude, prior_intel.longitude,
            ip_info['latitude'], ip_info['longitude']
        )

        if distance_km is None or distance_km < 100:
            return []

        time_diff_hours = (now - prior_login.timestamp).total_seconds() / 3600
        if time_diff_hours <= 0:
            return []

        speed_kmh = distance_km / time_diff_hours

        if speed_kmh < speed_threshold:
            return []

        # Check cooldown
        cooldown_key = f"impossible_travel_{event.username}"
        cooldown_setting = Setting.query.filter_by(key=cooldown_key).first()
        if cooldown_setting and cooldown_setting.value:
            try:
                last_alerted = datetime.fromisoformat(cooldown_setting.value)
                if datetime.utcnow() - last_alerted < timedelta(minutes=30):
                    return []
            except Exception:
                pass

        from_location = f"{prior_intel.city or 'Unknown'}, {prior_intel.country or 'Unknown'}"
        to_location = f"{ip_info.get('city', 'Unknown')}, {ip_info.get('country', 'Unknown')}"

        # Severity increases with speed
        severity = 'HIGH' if speed_kmh > 2000 else 'MEDIUM'

        prior_events = SecurityEvent.query.filter(
            SecurityEvent.username == event.username,
            SecurityEvent.timestamp >= lookback,
        ).order_by(SecurityEvent.timestamp.asc()).limit(20).all()

        return [{
            'title': 'Potential Impossible Travel',
            'description': (
                f'User "{event.username}" moved from {from_location} to '
                f'{to_location} ({distance_km:.0f} km) in '
                f'{time_diff_hours * 60:.0f} minutes, suggesting a travel '
                f'speed of {speed_kmh:.0f} km/h. This may indicate VPN, proxy, '
                f'or compromised credentials.'
            ),
            'severity': severity,
            'mitre_technique_id': 'T1078',
            'rule_name': 'Geographic Rule 2: Impossible Travel',
            'source_ip': event.source_ip,
            'username': event.username,
            'evidence': [e.to_dict() for e in prior_events],
            'factors': {
                'from_location': from_location,
                'to_location': to_location,
                'distance_km': round(distance_km, 1),
                'time_diff_minutes': round(time_diff_hours * 60, 1),
                'speed_kmh': round(speed_kmh, 1),
                'from_ip': prior_login.source_ip,
                'to_ip': event.source_ip,
                'detection_rule': 'IMPOSSIBLE_TRAVEL',
            },
        }]


# Global instance
geo_detection_engine = GeographicDetectionEngine()
