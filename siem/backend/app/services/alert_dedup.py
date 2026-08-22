"""
Alert Deduplication & Escalation Service

Prevents duplicate alerts for the same attack pattern.
Instead of creating N identical alerts, updates the existing active alert.

Correlation Key: rule_name + username + source_ip (normalized)
Alert States: NEW, INVESTIGATING, RESOLVED, FALSE_POSITIVE

Active alerts (NEW, INVESTIGATING) are eligible for deduplication.
Resolved/False-Positive alerts allow new alerts to be created.
"""

import json
from datetime import datetime
from sqlalchemy import func
from app.database import db, socketio
from app.models.alert import Alert
from app.models.security_event import SecurityEvent


def _build_correlation_key(alert_data):
    """
    Build a deterministic deduplication key for an alert.
    Same attack pattern + same target + same source = same alert.
    """
    rule = alert_data.get('rule_name', 'UNKNOWN')
    username = alert_data.get('username') or 'any'
    source_ip = alert_data.get('source_ip') or 'any'
    return f"{rule}|{username}|{source_ip}"


def _find_active_alert(correlation_key):
    """
    Find an existing active alert with the same correlation key.
    Active = NEW or INVESTIGATING status.
    """
    active_statuses = ['NEW', 'INVESTIGATING']
    return Alert.query.filter(
        Alert.status.in_(active_statuses),
        Alert.risk_factors['correlation_key'].as_string() == correlation_key
    ).order_by(Alert.created_at.desc()).first()


def _update_existing_alert(alert, alert_data, anomaly_score, ip_info, risk_score, risk_breakdown):
    """
    Update an existing alert with new evidence instead of creating a duplicate.
    Escalate severity/risk if the attack is worsening.
    """
    old_risk = alert.risk_score or 0
    new_risk = risk_score

    # Only escalate, never de-escalate
    if new_risk > old_risk:
        alert.risk_score = new_risk
        alert.risk_factors = risk_breakdown

    # Escalate severity if risk increased significantly
    severity_order = {'LOW': 1, 'MEDIUM': 2, 'HIGH': 3, 'CRITICAL': 4}
    new_severity = alert_data.get('severity', 'MEDIUM')
    if severity_order.get(new_severity, 0) > severity_order.get(alert.severity, 0):
        alert.severity = new_severity

    # Update evidence — append new evidence events, keep existing
    existing_evidence = alert.evidence or []
    new_evidence = alert_data.get('evidence', [])
    # Merge without duplicates (by event ID if available)
    existing_ids = set()
    for e in existing_evidence:
        if isinstance(e, dict):
            existing_ids.add(e.get('id', str(e)))
    for e in new_evidence:
        if isinstance(e, dict):
            eid = e.get('id', str(e))
            if eid not in existing_ids:
                existing_evidence.append(e)
                existing_ids.add(eid)
    alert.evidence = existing_evidence

    # Append system note
    notes = alert.notes or []
    notes.append({
        'author': 'System Dedup Engine',
        'text': f"Alert updated: additional matching events detected. Risk {old_risk:.1f} → {new_risk:.1f}.",
        'timestamp': datetime.utcnow().isoformat()
    })
    alert.notes = notes

    alert.updated_at = datetime.utcnow()
    db.session.commit()

    print(f"[Alert] Updated existing alert ALT-{alert.id} (correlated by key). Risk: {old_risk:.1f} → {new_risk:.1f}")

    # Broadcast update via Socket.IO
    try:
        socketio.emit('alert_updated', alert.to_dict())
    except Exception:
        pass

    return alert


def create_or_update_alert(alert_data, ml_anomaly_score=0.0, ip_info=None):
    """
    Main entry point: create a new alert or update an existing one.
    
    Returns: (alert, is_update) tuple
    """
    from app.detection.risk_engine import calculate_transparent_risk_score

    # Calculate risk score
    risk_score, risk_breakdown = calculate_transparent_risk_score(
        alert_data, ml_anomaly_score=ml_anomaly_score, ip_info=ip_info
    )

    # Add correlation key to risk factors for deduplication
    correlation_key = _build_correlation_key(alert_data)
    risk_breakdown['correlation_key'] = correlation_key

    # Check for existing active alert with same correlation key
    existing = _find_active_alert(correlation_key)

    if existing:
        # UPDATE existing alert instead of creating duplicate
        updated = _update_existing_alert(existing, alert_data, ml_anomaly_score, ip_info, risk_score, risk_breakdown)
        return updated, True

    # CREATE new alert
    alert = Alert(
        title=alert_data['title'],
        description=alert_data['description'],
        severity=alert_data.get('severity', 'MEDIUM'),
        source_ip=alert_data.get('source_ip'),
        username=alert_data.get('username'),
        timestamp=datetime.utcnow(),
        mitre_technique_id=alert_data.get('mitre_technique_id'),
        evidence=alert_data.get('evidence', []),
        status='NEW',
        risk_score=risk_score,
        risk_factors=risk_breakdown,
        notes=[{
            'author': 'System Detection Engine',
            'text': f"Alert created by {alert_data.get('rule_name', 'Unknown')}. Risk Score: {risk_score:.1f}/100.",
            'timestamp': datetime.utcnow().isoformat()
        }]
    )
    db.session.add(alert)
    db.session.commit()

    print(f"[Alert] Created new alert ALT-{alert.id}: {alert.title} (risk: {risk_score:.1f})")

    # Broadcast via Socket.IO
    try:
        socketio.emit('new_alert', alert.to_dict())
    except Exception:
        pass

    return alert, False
