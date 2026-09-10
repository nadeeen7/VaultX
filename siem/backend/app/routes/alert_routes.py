from datetime import datetime
from flask import Blueprint, request, jsonify, g
from app.database import db, socketio
from app.models.alert import Alert
from app.models.security_event import SecurityEvent
from app.models.user import User
from app.services.auth_service import token_required, roles_required
from app.services.audit_service import log_audit_action
from app.mitre.mitre_mapping import get_mitre_info
from app.services.ip_service import get_ip_intelligence
from app.services.incident_service import get_defensive_recommendations

alert_bp = Blueprint('alerts', __name__, url_prefix='/api/alerts')

@alert_bp.route('', methods=['GET'])
@token_required
def get_alerts():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    severity = request.args.get('severity')
    status = request.args.get('status')
    source_ip = request.args.get('source_ip')
    detection_rule = request.args.get('detection_rule')

    query = Alert.query

    # Alert Visibility filter
    # all = no assignment filter (default for Admin/Viewer)
    # mine = only alerts assigned to current user
    # unassigned = only alerts with no assignee
    visibility = request.args.get('visibility', 'all')

    if visibility == 'mine':
        query = query.filter_by(assigned_to_id=g.current_user.id)
    elif visibility == 'unassigned':
        query = query.filter_by(assigned_to_id=None)
    # visibility == 'all' → no assignment filter applied

    if severity:
        query = query.filter_by(severity=severity.upper())
    if status:
        query = query.filter_by(status=status.upper())
    if source_ip:
        query = query.filter_by(source_ip=source_ip)
    if detection_rule:
        # Filter by detection rule stored in risk_factors JSON
        query = query.filter(Alert.risk_factors['detection_rule'].as_string() == detection_rule)

    pagination = query.order_by(Alert.timestamp.desc()).paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'alerts': [a.to_dict() for a in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'pages': pagination.pages,
        'per_page': per_page
    }), 200

@alert_bp.route('/<int:alert_id>', methods=['GET'])
@token_required
def get_alert_detail(alert_id):
    alert = Alert.query.get_or_404(alert_id)

    # RBAC: Security Analysts can only view alerts assigned to them
    if g.current_user.role == 'Security Analyst' and alert.assigned_to_id != g.current_user.id:
        return jsonify({'error': 'Forbidden', 'message': 'You do not have access to this alert'}), 403

    mitre_data = get_mitre_info(alert.mitre_technique_id)
    ip_info = get_ip_intelligence(alert.source_ip)
    recommendations = get_defensive_recommendations(alert.title, alert.severity)

    res = alert.to_dict()
    res['mitre_details'] = mitre_data
    res['ip_intelligence'] = ip_info
    res['recommendations'] = recommendations

    return jsonify({'alert': res}), 200

@alert_bp.route('/<int:alert_id>/status', methods=['PATCH', 'PUT'])
@token_required
@roles_required('Admin', 'Security Analyst')
def update_alert_status(alert_id):
    alert = Alert.query.get_or_404(alert_id)
    data = request.get_json() or {}
    new_status = data.get('status') # NEW, INVESTIGATING, RESOLVED, FALSE_POSITIVE

    if new_status not in ['NEW', 'INVESTIGATING', 'RESOLVED', 'FALSE_POSITIVE']:
        return jsonify({'error': 'Invalid status'}), 400

    old_status = alert.status
    alert.status = new_status
    alert.updated_at = datetime.utcnow()

    # Append note to audit trail — use list() to force SQLAlchemy JSON change detection
    notes = list(alert.notes or [])
    notes.append({
        'author': g.current_user.username,
        'text': f"Status changed from {old_status} to {new_status}.",
        'timestamp': datetime.utcnow().isoformat()
    })
    alert.notes = notes

    db.session.commit()

    log_audit_action(
        user_id=g.current_user.id,
        username=g.current_user.username,
        action=f"Updated Alert Status ({old_status} -> {new_status})",
        resource_type='Alert',
        resource_id=alert.id,
        ip_address=request.remote_addr
    )

    try:
        socketio.emit('alert_updated', alert.to_dict())
    except Exception:
        pass

    return jsonify({'message': 'Alert status updated', 'alert': alert.to_dict()}), 200

@alert_bp.route('/<int:alert_id>/assign', methods=['POST'])
@token_required
@roles_required('Admin')
def assign_alert(alert_id):
    alert = Alert.query.get_or_404(alert_id)
    data = request.get_json() or {}
    user_id = data.get('user_id')

    # If user_id is null/empty, unassign the alert
    if user_id is None or user_id == '' or user_id == 0:
        old_assignee = alert.assigned_user.username if alert.assigned_user else 'Unassigned'
        alert.assigned_to_id = None
        alert.updated_at = datetime.utcnow()

        # Create a new list to force SQLAlchemy to detect the JSON change
        notes = list(alert.notes or [])
        notes.append({
            'author': g.current_user.username,
            'text': f"Unassigned alert (was {old_assignee}).",
            'timestamp': datetime.utcnow().isoformat()
        })
        alert.notes = notes

        db.session.commit()

        log_audit_action(
            user_id=g.current_user.id,
            username=g.current_user.username,
            action=f"Unassigned Alert ALT-{alert.id} (was {old_assignee})",
            resource_type='Alert',
            resource_id=alert.id,
            ip_address=request.remote_addr
        )

        try:
            socketio.emit('alert_updated', alert.to_dict())
        except Exception:
            pass

        return jsonify({'message': 'Alert unassigned', 'alert': alert.to_dict()}), 200

    # Assign to a specific user
    target_user = User.query.get(user_id)
    if not target_user:
        return jsonify({'error': 'User not found'}), 404

    # Verify the target is a Security Analyst (Admins are not assignable as analysts)
    if target_user.role != 'Security Analyst':
        return jsonify({'error': 'Can only assign to Security Analyst users'}), 400

    old_assignee = alert.assigned_user.username if alert.assigned_user else 'Unassigned'
    alert.assigned_to_id = target_user.id
    alert.updated_at = datetime.utcnow()

    # Create a new list to force SQLAlchemy to detect the JSON change
    notes = list(alert.notes or [])
    notes.append({
        'author': g.current_user.username,
        'text': f"Assigned alert to analyst {target_user.username} (was {old_assignee}).",
        'timestamp': datetime.utcnow().isoformat()
    })
    alert.notes = notes

    db.session.commit()

    log_audit_action(
        user_id=g.current_user.id,
        username=g.current_user.username,
        action=f"Assigned ALT-{alert.id} to '{target_user.username}' (was {old_assignee})",
        resource_type='Alert',
        resource_id=alert.id,
        ip_address=request.remote_addr
    )

    try:
        socketio.emit('alert_updated', alert.to_dict())
    except Exception:
        pass

    return jsonify({'message': 'Alert assigned', 'alert': alert.to_dict()}), 200

@alert_bp.route('/<int:alert_id>/notes', methods=['POST'])
@token_required
@roles_required('Admin', 'Security Analyst')
def add_alert_note(alert_id):
    alert = Alert.query.get_or_404(alert_id)
    data = request.get_json() or {}
    text = data.get('text')

    if not text:
        return jsonify({'error': 'Note text is required'}), 400

    # Create a new list to force SQLAlchemy to detect the JSON change
    notes = list(alert.notes or [])
    notes.append({
        'author': g.current_user.username,
        'text': text,
        'timestamp': datetime.utcnow().isoformat()
    })
    alert.notes = notes
    alert.updated_at = datetime.utcnow()

    db.session.commit()

    log_audit_action(
        user_id=g.current_user.id,
        username=g.current_user.username,
        action="Added Note to Alert",
        resource_type='Alert',
        resource_id=alert.id,
        details={'note': text}
    )

    return jsonify({'message': 'Note added', 'alert': alert.to_dict()}), 200


@alert_bp.route('/<int:alert_id>/related-events', methods=['GET'])
@token_required
def get_related_events(alert_id):
    """
    Retrieve related security events for a correlation alert.
    Uses evidence from the alert and queries for additional events
    matching the same username or source IP within the alert's time window.
    """
    alert = Alert.query.get_or_404(alert_id)

    # Time window: 1 hour before and after the alert
    from datetime import timedelta
    lookback = alert.timestamp - timedelta(hours=1) if alert.timestamp else None
    lookahead = alert.timestamp + timedelta(hours=1) if alert.timestamp else None

    query = SecurityEvent.query

    if lookback and lookahead:
        query = query.filter(
            SecurityEvent.timestamp >= lookback,
            SecurityEvent.timestamp <= lookahead
        )

    # Match by username or source_ip from the alert
    filters = []
    if alert.username:
        filters.append(SecurityEvent.username == alert.username)
    if alert.source_ip:
        filters.append(SecurityEvent.source_ip == alert.source_ip)

    if filters:
        from sqlalchemy import or_
        query = query.filter(or_(*filters))

    events = query.order_by(SecurityEvent.timestamp.asc()).limit(50).all()

    return jsonify({
        'events': [e.to_dict() for e in events],
        'total': len(events),
        'alert_id': alert_id,
    }), 200


@alert_bp.route('/detection-types', methods=['GET'])
@token_required
def get_detection_types():
    """
    Return distinct detection rule types that have generated alerts,
    along with their counts. Used for dashboard filtering.
    """
    from sqlalchemy import func, JSON

    results = db.session.query(
        Alert.risk_factors['detection_rule'].as_string().label('rule'),
        func.count(Alert.id).label('count')
    ).filter(
        Alert.risk_factors['detection_rule'].as_string().isnot(None)
    ).group_by('rule').order_by(func.count(Alert.id).desc()).all()

    types = [
        {'rule': r.rule, 'count': r.count}
        for r in results if r.rule
    ]

    return jsonify({'detection_types': types}), 200
