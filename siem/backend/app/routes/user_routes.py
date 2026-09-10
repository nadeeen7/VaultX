from flask import Blueprint, request, jsonify, g
from app.database import db
from app.models.user import User
from app.services.auth_service import token_required, roles_required
from app.services.audit_service import log_audit_action

user_bp = Blueprint('users', __name__, url_prefix='/api/users')

@user_bp.route('', methods=['GET'])
@token_required
@roles_required('Admin')
def get_users():
    users = User.query.order_by(User.created_at.desc()).all()
    return jsonify({'users': [u.to_dict() for u in users]}), 200

@user_bp.route('/analysts', methods=['GET'])
@token_required
@roles_required('Admin', 'Security Analyst')
def get_analysts():
    """Return active analysts for alert assignment dropdown."""
    analysts = User.query.filter(
        User.role == 'Security Analyst',
    ).order_by(User.username.asc()).all()
    return jsonify({'analysts': [u.to_dict() for u in analysts]}), 200

@user_bp.route('', methods=['POST'])
@token_required
@roles_required('Admin')
def create_user():
    data = request.get_json() or {}
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'Security Analyst')

    if not username or not email or not password:
        return jsonify({'error': 'Username, email, and password are required'}), 400

    if role not in ['Admin', 'Security Analyst', 'Viewer']:
        return jsonify({'error': 'Invalid role'}), 400

    if User.query.filter((User.username == username) | (User.email == email)).first():
        return jsonify({'error': 'Username or email already registered'}), 400

    user = User(username=username, email=email, role=role)
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    log_audit_action(
        user_id=g.current_user.id,
        username=g.current_user.username,
        action=f"Created User '{username}' ({role})"
    )

    return jsonify({'message': 'User created successfully', 'user': user.to_dict()}), 201

@user_bp.route('/<int:user_id>/role', methods=['PATCH', 'PUT'])
@token_required
@roles_required('Admin')
def update_user_role(user_id):
    user = User.query.get_or_404(user_id)
    data = request.get_json() or {}
    new_role = data.get('role')

    if new_role not in ['Admin', 'Security Analyst', 'Viewer']:
        return jsonify({'error': 'Invalid role'}), 400

    old_role = user.role
    user.role = new_role
    db.session.commit()

    log_audit_action(
        user_id=g.current_user.id,
        username=g.current_user.username,
        action=f"Updated User Role for '{user.username}' ({old_role} -> {new_role})"
    )

    return jsonify({'message': 'User role updated', 'user': user.to_dict()}), 200
