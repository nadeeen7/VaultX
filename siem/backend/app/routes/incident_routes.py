from datetime import datetime
from flask import Blueprint, request, jsonify, g
from app.database import db, socketio
from app.models.incident import Incident, IncidentEvent
from app.services.auth_service import token_required, roles_required
from app.services.incident_service import build_attack_timeline
from app.services.audit_service import log_audit_action

incident_bp = Blueprint('incidents', __name__, url_prefix='/api/incidents')

@incident_bp.route('', methods=['GET'])
@token_required
def get_incidents():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status = request.args.get('status')
    severity = request.args.get('severity')

    query = Incident.query

    if status:
        query = query.filter_by(status=status.upper())
    if severity:
        query = query.filter_by(severity=severity.upper())

    pagination = query.order_by(Incident.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'incidents': [i.to_dict() for i in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'pages': pagination.pages,
        'per_page': per_page
    }), 200

@incident_bp.route('/<int:incident_id>', methods=['GET'])
@token_required
def get_incident_detail(incident_id):
    incident = Incident.query.get_or_404(incident_id)
    inc_events = IncidentEvent.query.filter_by(incident_id=incident_id).all()
    timeline = build_attack_timeline(incident_id=incident_id)

    res = incident.to_dict()
    res['events'] = [e.to_dict() for e in inc_events]
    res['timeline'] = timeline

    return jsonify({'incident': res}), 200

@incident_bp.route('/<int:incident_id>/status', methods=['PATCH', 'PUT'])
@token_required
@roles_required('Admin', 'Security Analyst')
def update_incident_status(incident_id):
    incident = Incident.query.get_or_404(incident_id)
    data = request.get_json() or {}
    new_status = data.get('status') # OPEN, INVESTIGATING, RESOLVED, CLOSED

    if new_status not in ['OPEN', 'INVESTIGATING', 'RESOLVED', 'CLOSED']:
        return jsonify({'error': 'Invalid incident status'}), 400

    old_status = incident.status
    incident.status = new_status
    incident.updated_at = datetime.utcnow()

    db.session.commit()

    log_audit_action(
        user_id=g.current_user.id,
        username=g.current_user.username,
        action=f"Updated Incident Status ({old_status} -> {new_status})",
        resource_type='Incident',
        resource_id=incident.id
    )

    try:
        socketio.emit('incident_updated', incident.to_dict())
    except Exception:
        pass

    return jsonify({'message': 'Incident status updated', 'incident': incident.to_dict()}), 200

@incident_bp.route('/timeline', methods=['GET'])
@token_required
def get_global_attack_timeline():
    incident_id = request.args.get('incident_id', type=int)
    timeline = build_attack_timeline(incident_id=incident_id)
    return jsonify({'timeline': timeline}), 200
