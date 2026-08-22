from datetime import datetime, timedelta
from app.database import db
from app.models.alert import Alert
from app.models.incident import Incident, IncidentEvent

def correlate_alert_into_incident(alert):
    """
    Automatically groups new incoming alerts into existing open/investigating incidents,
    or spawns a new Incident if no active incident matches the attacker source IP or user.
    """
    now = alert.timestamp or datetime.utcnow()
    lookback = now - timedelta(hours=4)

    # Search for an existing active Incident with same source IP or affected user within 4 hours
    existing_incident = None
    if alert.source_ip:
        existing_incident = Incident.query.filter(
            Incident.source_ip == alert.source_ip,
            Incident.status.in_(['OPEN', 'INVESTIGATING']),
            Incident.created_at >= lookback
        ).first()

    if not existing_incident and alert.username:
        existing_incident = Incident.query.filter(
            Incident.affected_user == alert.username,
            Incident.status.in_(['OPEN', 'INVESTIGATING']),
            Incident.created_at >= lookback
        ).first()

    if existing_incident:
        # Attach alert to existing incident
        inc_event = IncidentEvent(
            incident_id=existing_incident.id,
            alert_id=alert.id,
            added_at=now
        )
        db.session.add(inc_event)

        # Upgrade incident severity if new alert is higher severity
        severity_order = {'LOW': 1, 'MEDIUM': 2, 'HIGH': 3, 'CRITICAL': 4}
        if severity_order.get(alert.severity, 1) > severity_order.get(existing_incident.severity, 1):
            existing_incident.severity = alert.severity

        # Update composite risk score
        existing_incident.risk_score = min(100.0, existing_incident.risk_score + (alert.risk_score * 0.3))
        existing_incident.updated_at = datetime.utcnow()
        db.session.commit()
        return existing_incident
    else:
        # Create a new Incident
        new_incident = Incident(
            title=f"Incident: {alert.title}",
            description=f"Correlated security incident initiated by alert '{alert.title}' targeting user {alert.username or 'N/A'} from IP {alert.source_ip}.",
            severity=alert.severity,
            status='OPEN',
            source_ip=alert.source_ip,
            affected_user=alert.username,
            risk_score=alert.risk_score,
            created_at=now
        )
        db.session.add(new_incident)
        db.session.flush() # get new_incident.id

        inc_event = IncidentEvent(
            incident_id=new_incident.id,
            alert_id=alert.id,
            added_at=now
        )
        db.session.add(inc_event)
        db.session.commit()
        return new_incident

def build_attack_timeline(incident_id=None, source_ip=None, username=None):
    """
    Constructs a chronological attack timeline combining security events and alerts.
    Format: Timestamp, Event, Source IP, User, Detection/Rule, Severity.
    """
    timeline_entries = []

    if incident_id:
        incident = Incident.query.get(incident_id)
        if not incident:
            return []
        
        inc_events = IncidentEvent.query.filter_by(incident_id=incident_id).all()
        alert_ids = [e.alert_id for e in inc_events if e.alert_id]
        
        alerts = Alert.query.filter(Alert.id.in_(alert_ids)).all() if alert_ids else []
        for a in alerts:
            timeline_entries.append({
                'id': f"alert-{a.id}",
                'timestamp': a.timestamp.isoformat() if a.timestamp else None,
                'type': 'ALERT',
                'event_title': a.title,
                'source_ip': a.source_ip,
                'user': a.username or 'N/A',
                'detection': f"MITRE {a.mitre_technique_id or 'General'}",
                'severity': a.severity,
                'details': a.description
            })
            # Add evidence events if present
            for ev in (a.evidence or []):
                timeline_entries.append({
                    'id': f"ev-{ev.get('id', 'unk')}",
                    'timestamp': ev.get('timestamp'),
                    'type': 'EVENT',
                    'event_title': ev.get('event_type', 'Raw Security Event').upper().replace('_', ' '),
                    'source_ip': ev.get('source_ip', a.source_ip),
                    'user': ev.get('username', a.username),
                    'detection': f"Status: {ev.get('status', 'recorded')}",
                    'severity': 'INFO' if ev.get('status') == 'success' else 'WARN',
                    'details': f"Raw telemetry event from {ev.get('source_app', 'SecureBank')}"
                })

    # Sort chronology ascending by timestamp
    timeline_entries.sort(key=lambda x: str(x.get('timestamp') or ''))
    return timeline_entries

def get_defensive_recommendations(alert_title, severity):
    """Provides actionable defensive SOC playbooks and response recommendations."""
    title_lower = (alert_title or '').lower()

    if 'brute force' in title_lower:
        return [
            {'action': 'Investigate Source IP', 'description': 'Check IP reputation, ISP, and historical events from this address.'},
            {'action': 'Account Protection', 'description': 'Review affected user account, enforce password reset if necessary.'},
            {'action': 'Simulate IP Blocking', 'description': 'Simulate adding source IP to firewall drop list.'},
            {'action': 'Review Success Logins', 'description': 'Verify if any successful login occurred from this IP during the attack window.'}
        ]
    elif 'compromise' in title_lower:
        return [
            {'action': 'Immediate Session Revocation', 'description': 'Revoke active JWT tokens and active sessions for the user.'},
            {'action': 'Force Password Reset', 'description': 'Flag user account for mandatory password reset upon next attempt.'},
            {'action': 'Enable Mandatory MFA', 'description': 'Require multi-factor authentication enforcement.'},
            {'action': 'Audit Post-Authentication Activity', 'description': 'Inspect all transactions and API requests performed right after login.'}
        ]
    elif 'admin' in title_lower or 'privilege' in title_lower:
        return [
            {'action': 'Review Role Authorization', 'description': 'Audit user role and permissions in system directory.'},
            {'action': 'Inspect Endpoint Traffic', 'description': 'Check administrative endpoint request logs for privilege escalation vectors.'},
            {'action': 'Simulate Account Lockout', 'description': 'Simulate temporary account suspension for investigation.'}
        ]
    elif 'password spray' in title_lower:
        return [
            {'action': 'Identify Attacker Source', 'description': 'Investigate the source IP and its network owner/ISP.'},
            {'action': 'Review Targeted Accounts', 'description': 'Check all targeted usernames for unauthorized access or compromise.'},
            {'action': 'Enforce Account Lockout', 'description': 'Temporarily lock accounts showing spray pattern for investigation.'},
            {'action': 'Deploy IP Blocklist', 'description': 'Add the attacking source IP to the firewall or WAF block list.'}
        ]
    elif 'distributed' in title_lower:
        return [
            {'action': 'Map Attack Scope', 'description': 'Identify all source IPs and targeted usernames across the distributed activity.'},
            {'action': 'Correlate with Threat Intel', 'description': 'Check source IPs against threat intelligence feeds for known attack infrastructure.'},
            {'action': 'Alert Security Team', 'description': 'This may indicate a coordinated attack. Escalate to senior SOC analysts.'},
            {'action': 'Review All Targeted Accounts', 'description': 'Verify none of the targeted accounts show evidence of successful compromise.'}
        ]
    elif 'multi-source' in title_lower:
        return [
            {'action': 'Investigate All Source IPs', 'description': 'Determine if the IPs are from the same network block or geography.'},
            {'action': 'Check Account for Compromise', 'description': 'Review if the targeted account shows any successful login or unauthorized activity.'},
            {'action': 'Force Password Reset', 'description': 'Consider a mandatory password reset for the targeted account.'},
            {'action': 'Enable Enhanced Monitoring', 'description': 'Add the account to a high-priority watchlist for 24 hours.'}
        ]
    elif 'suspicious' in title_lower and 'success' in title_lower:
        return [
            {'action': 'Immediate Session Review', 'description': 'Review all activity performed by the user after the successful login.'},
            {'action': 'Verify Transaction Legitimacy', 'description': 'Check if any transactions performed after login are authorized by the account holder.'},
            {'action': 'Revoke Active Sessions', 'description': 'Invalidate all current sessions for the affected user.'},
            {'action': 'Force Password Reset', 'description': 'Mandate a password reset before the user can log in again.'}
        ]
    elif 'automated' in title_lower or 'frequency' in title_lower:
        return [
            {'action': 'Enable Rate Limiting', 'description': 'Apply API rate limiters (e.g. 10 req/min per IP).'},
            {'action': 'Challenge WAF Captcha', 'description': 'Issue web application firewall bot challenge.'},
            {'action': 'Inspect User-Agent Header', 'description': 'Look for automated scripts or headless browser user-agents.'}
        ]
    else:
        return [
            {'action': 'SOC Analyst Inspection', 'description': 'Assign alert to Tier 2 analyst for deep packet/log inspection.'},
            {'action': 'Monitor Target Account', 'description': 'Add affected account to heightened monitoring watchlist.'}
        ]
