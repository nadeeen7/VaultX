from flask import Blueprint, request, jsonify, g
from app.database import db
from app.models.user import User
from app.services.auth_service import generate_jwt_token, token_required
from app.services.audit_service import log_audit_action

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400

    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        log_audit_action(action='Failed SIEM Login Attempt', details={'attempted_username': username}, ip_address=request.remote_addr)
        return jsonify({'error': 'Invalid username or password'}), 401

    token = generate_jwt_token(user)
    log_audit_action(user_id=user.id, username=user.username, action='User Login', ip_address=request.remote_addr)

    return jsonify({
        'message': 'Authentication successful',
        'token': token,
        'user': user.to_dict()
    }), 200

@auth_bp.route('/me', methods=['GET'])
@token_required
def get_current_user():
    return jsonify({'user': g.current_user.to_dict()}), 200

@auth_bp.route('/logout', methods=['POST'])
@token_required
def logout():
    log_audit_action(user_id=g.current_user.id, username=g.current_user.username, action='User Logout', ip_address=request.remote_addr)
    return jsonify({'message': 'Logged out successfully'}), 200
