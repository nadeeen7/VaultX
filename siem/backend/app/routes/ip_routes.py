from datetime import datetime, timedelta
from ipaddress import ip_address as validate_ip, AddressValueError
from flask import Blueprint, jsonify, request
from sqlalchemy import func, distinct, or_
from app.database import db
from app.services.ip_service import get_ip_intelligence, haversine_distance
from app.models.ip_intelligence import IPIntelligence
from app.models.security_event import SecurityEvent
from app.models.alert import Alert
from app.services.auth_service import token_required

ip_bp = Blueprint('ip', __name__, url_prefix='/api/ip-intelligence')

def _validate_ip(ip_str):
    """Validate an IP address string. Returns the validated string or None."""
    try:
        addr = validate_ip(ip_str)
        return str(addr)
    except (AddressValueError, ValueError):
        return None

@ip_bp.route('/<ip_address>', methods=['GET'])
@token_required
def get_ip_details(ip_address):
    """Get detailed IP intelligence with event/alert counts and associated users."""
    if not _validate_ip(ip_address):
        return jsonify({'error': 'Invalid IP address', 'message': 'Please enter a valid IPv4 or IPv6 address'}), 400
    intel = get_ip_intelligence(ip_address)

    # Event counts
    event_count = SecurityEvent.query.filter_by(source_ip=ip_address).count()
    alert_count = Alert.query.filter_by(source_ip=ip_address).count()

    # User breakdown
    users = db.session.query(
        SecurityEvent.username,
        func.count(SecurityEvent.id).label('events'),
        func.sum(func.cast(SecurityEvent.status == 'failed', db.Integer)).label('failed'),
        func.sum(func.cast(SecurityEvent.status == 'success', db.Integer)).label('success'),
        func.min(SecurityEvent.timestamp).label('first_seen'),
        func.max(SecurityEvent.timestamp).label('last_seen')
    ).filter(
        SecurityEvent.source_ip == ip_address,
        SecurityEvent.username.isnot(None)
    ).group_by(SecurityEvent.username).all()

    associated_users = [{
        'username': u.username,
        'event_count': u.events,
        'failed_logins': u.failed or 0,
        'successful_logins': u.success or 0,
        'first_seen': u.first_seen.isoformat() if u.first_seen else None,
        'last_seen': u.last_seen.isoformat() if u.last_seen else None
    } for u in users]

    # Time range
    first_event = SecurityEvent.query.filter_by(source_ip=ip_address).order_by(SecurityEvent.timestamp.asc()).first()
    last_event = SecurityEvent.query.filter_by(source_ip=ip_address).order_by(SecurityEvent.timestamp.desc()).first()

    # Failed vs successful
    failed_count = SecurityEvent.query.filter_by(source_ip=ip_address, status='failed').count()
    success_count = SecurityEvent.query.filter_by(source_ip=ip_address, status='success').count()

    intel['event_count'] = event_count
    intel['alert_count'] = alert_count
    intel['associated_users'] = associated_users
    intel['first_seen'] = first_event.timestamp.isoformat() if first_event and first_event.timestamp else None
    intel['last_seen'] = last_event.timestamp.isoformat() if last_event and last_event.timestamp else None
    intel['failed_logins'] = failed_count
    intel['successful_logins'] = success_count
    intel['affected_accounts'] = len(associated_users)

    return jsonify({'ip_intelligence': intel}), 200

@ip_bp.route('/<ip_address>/events', methods=['GET'])
@token_required
def get_ip_events(ip_address):
    """Get recent security events for a specific IP."""
    if not _validate_ip(ip_address):
        return jsonify({'error': 'Invalid IP address', 'message': 'Please enter a valid IPv4 or IPv6 address'}), 400
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    query = SecurityEvent.query.filter_by(source_ip=ip_address).order_by(SecurityEvent.timestamp.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'events': [e.to_dict() for e in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'pages': pagination.pages
    }), 200

@ip_bp.route('/<ip_address>/alerts', methods=['GET'])
@token_required
def get_ip_alerts(ip_address):
    """Get alerts triggered from a specific IP."""
    if not _validate_ip(ip_address):
        return jsonify({'error': 'Invalid IP address', 'message': 'Please enter a valid IPv4 or IPv6 address'}), 400
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    query = Alert.query.filter_by(source_ip=ip_address).order_by(Alert.timestamp.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'alerts': [a.to_dict() for a in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'pages': pagination.pages
    }), 200

@ip_bp.route('', methods=['GET'])
@token_required
def list_cached_ips():
    """List all cached IP intelligence records."""
    cached_ips = IPIntelligence.query.order_by(IPIntelligence.updated_at.desc()).limit(50).all()
    return jsonify({'ips': [ip.to_dict() for ip in cached_ips]}), 200

@ip_bp.route('/geo-map', methods=['GET'])
@token_required
def get_geo_map_data():
    """Get all IPs with coordinates for map visualization."""
    ips_with_coords = IPIntelligence.query.filter(
        IPIntelligence.latitude.isnot(None),
        IPIntelligence.longitude.isnot(None),
        IPIntelligence.is_private == False
    ).all()

    map_data = []
    for ip in ips_with_coords:
        event_count = SecurityEvent.query.filter_by(source_ip=ip.ip_address).count()
        alert_count = Alert.query.filter_by(source_ip=ip.ip_address).count()
        map_data.append({
            'ip_address': ip.ip_address,
            'country': ip.country,
            'country_code': ip.country_code,
            'city': ip.city,
            'latitude': ip.latitude,
            'longitude': ip.longitude,
            'event_count': event_count,
            'alert_count': alert_count,
            'last_seen': ip.last_seen.isoformat() if ip.last_seen else None
        })

    return jsonify({'map_data': map_data}), 200

@ip_bp.route('/user/<username>/ips', methods=['GET'])
@token_required
def get_user_ips(username):
    """Get all known IP addresses for a specific user."""
    ips = db.session.query(
        SecurityEvent.source_ip,
        func.count(SecurityEvent.id).label('events'),
        func.min(SecurityEvent.timestamp).label('first_seen'),
        func.max(SecurityEvent.timestamp).label('last_seen')
    ).filter(
        SecurityEvent.username == username
    ).group_by(SecurityEvent.source_ip).order_by(func.count(SecurityEvent.id).desc()).all()

    result = []
    for ip_row in ips:
        ip_addr = ip_row.source_ip
        intel = IPIntelligence.query.filter_by(ip_address=ip_addr).first()
        result.append({
            'ip_address': ip_addr,
            'event_count': ip_row.events,
            'first_seen': ip_row.first_seen.isoformat() if ip_row.first_seen else None,
            'last_seen': ip_row.last_seen.isoformat() if ip_row.last_seen else None,
            'country': intel.country if intel else 'Unknown',
            'city': intel.city if intel else 'Unknown'
        })

    return jsonify({'username': username, 'known_ips': result}), 200

@ip_bp.route('/geo-stats', methods=['GET'])
@token_required
def get_geo_stats():
    """Get geographic statistics for the dashboard."""
    # Top countries
    countries = db.session.query(
        IPIntelligence.country,
        func.count(IPIntelligence.id).label('count')
    ).filter(IPIntelligence.country.isnot(None), IPIntelligence.is_private == False
    ).group_by(IPIntelligence.country).order_by(func.count(IPIntelligence.id).desc()).limit(10).all()

    # Top cities
    cities = db.session.query(
        IPIntelligence.city,
        IPIntelligence.country,
        func.count(IPIntelligence.id).label('count')
    ).filter(IPIntelligence.city.isnot(None), IPIntelligence.is_private == False
    ).group_by(IPIntelligence.city, IPIntelligence.country).order_by(func.count(IPIntelligence.id).desc()).limit(10).all()

    # Private vs public
    total = IPIntelligence.query.count()
    private_count = IPIntelligence.query.filter_by(is_private=True).count()
    public_count = total - private_count

    return jsonify({
        'top_countries': [{'country': c.country, 'count': c.count} for c in countries],
        'top_cities': [{'city': c.city, 'country': c.country, 'count': c.count} for c in cities],
        'total_ips': total,
        'private_ips': private_count,
        'public_ips': public_count
    }), 200
