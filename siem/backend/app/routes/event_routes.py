from datetime import datetime
from flask import Blueprint, request, jsonify
from app.database import db
from app.models.security_event import SecurityEvent
from app.services.auth_service import token_required
from app.collectors.securebank_collector import securebank_collector

event_bp = Blueprint('events', __name__, url_prefix='/api/events')


@event_bp.route('', methods=['POST'])
def ingest_event():
    """
    Accept security events from external sources (e.g., Bank backend).
    Authenticates via X-API-Key header matching SIEM_API_KEY env var.
    Accepts a single event object or a list of events.
    
    IMPORTANT: This route ONLY handles event ingestion/normalization.
    Detection, correlation, and alert creation run ONLY from the background collector
    to prevent double-processing of events.
    """
    from flask import current_app
    api_key = request.headers.get('X-API-Key', '')
    expected_key = current_app.config.get('SIEM_API_KEY', '')
    
    if not expected_key:
        return jsonify({'error': 'SIEM API key not configured'}), 500
    
    if api_key != expected_key:
        return jsonify({'error': 'Invalid or missing API key'}), 401
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is required'}), 400
    
    events = data if isinstance(data, list) else [data]
    
    processed = []
    errors = []
    
    for raw_event in events:
        try:
            # Ingestion only — detection runs via background collector polling
            event = securebank_collector.process_raw_event(raw_event)
            if event:
                processed.append(event.to_dict())
            else:
                errors.append({'event': raw_event.get('event_type', 'unknown'), 'error': 'Duplicate event (already ingested)'})
        except Exception as e:
            errors.append({'event': raw_event.get('event_type', 'unknown'), 'error': str(e)})
    
    return jsonify({
        'message': f'Processed {len(processed)} event(s), {len(errors)} error(s)',
        'processed': len(processed),
        'errors': len(errors),
        'details': {
            'ingested': processed,
            'error_details': errors
        }
    }), 200


@event_bp.route('', methods=['GET'])
@token_required
def get_events():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    event_type = request.args.get('event_type')
    source_ip = request.args.get('source_ip')
    username = request.args.get('username')

    query = SecurityEvent.query

    if event_type:
        query = query.filter(SecurityEvent.event_type.ilike(f"%{event_type}%"))
    if source_ip:
        query = query.filter(SecurityEvent.source_ip == source_ip)
    if username:
        query = query.filter(SecurityEvent.username.ilike(f"%{username}%"))

    pagination = query.order_by(SecurityEvent.timestamp.desc()).paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'events': [e.to_dict() for e in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'pages': pagination.pages,
        'per_page': per_page
    }), 200


@event_bp.route('/<int:event_id>', methods=['GET'])
@token_required
def get_event_detail(event_id):
    event = SecurityEvent.query.get_or_404(event_id)
    return jsonify({'event': event.to_dict()}), 200


@event_bp.route('/health', methods=['GET'])
def events_health():
    """Public health check for the event ingestion service."""
    return jsonify({'status': 'ok', 'service': 'siem-event-ingestion'}), 200
