from datetime import datetime, timedelta
from flask import Blueprint, jsonify
from sqlalchemy import func
from app.database import db
from app.models.security_event import SecurityEvent
from app.models.alert import Alert
from app.models.incident import Incident
from app.models.ml_anomaly import MLAnomaly
from app.models.ip_intelligence import IPIntelligence
from app.services.auth_service import token_required

analytics_bp = Blueprint('analytics', __name__, url_prefix='/api/analytics')

@analytics_bp.route('/dashboard', methods=['GET'])
@token_required
def get_dashboard_metrics():
    """Provides real-time SOC dashboard metrics, counts, and chart aggregations."""
    total_events = SecurityEvent.query.count()
    total_alerts = Alert.query.count()
    critical_alerts = Alert.query.filter_by(severity='CRITICAL').count()
    high_alerts = Alert.query.filter_by(severity='HIGH').count()
    open_incidents = Incident.query.filter(Incident.status.in_(['OPEN', 'INVESTIGATING'])).count()
    total_anomalies = MLAnomaly.query.filter_by(is_anomaly=True).count()

    # 1. Events over time (grouped by hour or 15m intervals)
    now = datetime.utcnow()
    last_24h = now - timedelta(hours=24)
    
    events_24h = SecurityEvent.query.filter(SecurityEvent.timestamp >= last_24h).all()
    
    # Bucket into hourly series
    hourly_counts = {i: 0 for i in range(24)}
    hourly_alerts = {i: 0 for i in range(24)}

    for e in events_24h:
        if e.timestamp:
            h = e.timestamp.hour
            hourly_counts[h] += 1

    alerts_24h = Alert.query.filter(Alert.timestamp >= last_24h).all()
    for a in alerts_24h:
        if a.timestamp:
            h = a.timestamp.hour
            hourly_alerts[h] += 1

    events_timeline = [
        {'hour': f"{h:02d}:00", 'events': hourly_counts[h], 'alerts': hourly_alerts[h]}
        for h in range(24)
    ]

    # 2. Alerts by Severity
    severity_counts = {
        'CRITICAL': Alert.query.filter_by(severity='CRITICAL').count(),
        'HIGH': Alert.query.filter_by(severity='HIGH').count(),
        'MEDIUM': Alert.query.filter_by(severity='MEDIUM').count(),
        'LOW': Alert.query.filter_by(severity='LOW').count(),
    }
    severity_distribution = [
        {'name': sev, 'value': count} for sev, count in severity_counts.items()
    ]

    # 3. Top Source IPs
    top_ips = db.session.query(
        Alert.source_ip, func.count(Alert.id).label('count')
    ).group_by(Alert.source_ip).order_by(func.count(Alert.id).desc()).limit(5).all()

    top_source_ips = [{'ip': ip, 'count': count} for ip, count in top_ips]

    # 4. Top Attack Types (Alert Titles)
    top_attacks = db.session.query(
        Alert.title, func.count(Alert.id).label('count')
    ).group_by(Alert.title).order_by(func.count(Alert.id).desc()).limit(5).all()

    top_attack_types = [{'title': title, 'count': count} for title, count in top_attacks]

    # 5. MITRE Techniques Distribution
    top_mitre = db.session.query(
        Alert.mitre_technique_id, func.count(Alert.id).label('count')
    ).filter(Alert.mitre_technique_id.isnot(None)).group_by(Alert.mitre_technique_id).order_by(func.count(Alert.id).desc()).limit(5).all()

    mitre_distribution = [{'technique_id': tech_id, 'count': count} for tech_id, count in top_mitre]

    # 6. Geographic Distribution (by country)
    geo_data = db.session.query(
        IPIntelligence.country, func.count(IPIntelligence.id).label('count')
    ).filter(IPIntelligence.is_private == False).group_by(IPIntelligence.country).order_by(func.count(IPIntelligence.id).desc()).limit(5).all()

    geo_distribution = [{'country': country or 'Unknown', 'count': count} for country, count in geo_data]

    # 7. Geographic anomaly signals (recent new-country alerts)
    geo_anomaly_count = Alert.query.filter(
        Alert.risk_factors['detection_rule'].as_string() == 'NEW_COUNTRY_FOR_USER'
    ).count() if hasattr(Alert, 'risk_factors') else 0

    impossible_travel_count = Alert.query.filter(
        Alert.risk_factors['detection_rule'].as_string() == 'IMPOSSIBLE_TRAVEL'
    ).count() if hasattr(Alert, 'risk_factors') else 0

    # Recent Alerts table snippet
    recent_alerts = [a.to_dict() for a in Alert.query.order_by(Alert.timestamp.desc()).limit(10).all()]

    return jsonify({
        'metrics': {
            'total_events': total_events,
            'total_alerts': total_alerts,
            'critical_alerts': critical_alerts,
            'high_alerts': high_alerts,
            'open_incidents': open_incidents,
            'total_anomalies': total_anomalies,
            'geo_anomalies': geo_anomaly_count,
            'impossible_travel': impossible_travel_count
        },
        'charts': {
            'events_over_time': events_timeline,
            'severity_distribution': severity_distribution,
            'top_source_ips': top_source_ips,
            'top_attack_types': top_attack_types,
            'mitre_distribution': mitre_distribution,
            'geo_distribution': geo_distribution
        },
        'recent_alerts': recent_alerts
    }), 200

@analytics_bp.route('/ml', methods=['GET'])
@token_required
def get_ml_analytics():
    anomalies = MLAnomaly.query.order_by(MLAnomaly.timestamp.desc()).limit(50).all()
    total_scanned = SecurityEvent.query.count()
    flagged_count = MLAnomaly.query.filter_by(is_anomaly=True).count()

    return jsonify({
        'summary': {
            'total_scanned': total_scanned,
            'flagged_anomalies': flagged_count,
            'anomaly_ratio': round(flagged_count / max(1, total_scanned), 3)
        },
        'recent_anomalies': [a.to_dict() for a in anomalies]
    }), 200
