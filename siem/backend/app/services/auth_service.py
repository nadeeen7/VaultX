import jwt
from functools import wraps
from datetime import datetime, timedelta
from flask import request, jsonify, current_app, g
from app.models.user import User

def generate_jwt_token(user):
    """Generate JWT access token containing user identity and role claims."""
    payload = {
        'user_id': user.id,
        'username': user.username,
        'email': user.email,
        'role': user.role,
        'exp': datetime.utcnow() + current_app.config.get('JWT_ACCESS_TOKEN_EXPIRES', timedelta(hours=24)),
        'iat': datetime.utcnow()
    }
    token = jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')
    return token

def token_required(f):
    """Decorator to require valid JWT token in Authorization header."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')

        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]

        if not token:
            return jsonify({'error': 'Authentication token is missing'}), 401

        try:
            payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
            user = User.query.get(payload['user_id'])
            if not user:
                return jsonify({'error': 'User associated with token no longer exists'}), 401
            g.current_user = user
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid authentication token'}), 401

        return f(*args, **kwargs)
    return decorated

def roles_required(*allowed_roles):
    """Decorator to enforce role-based access control (RBAC).

    Usage:
        @token_required
        @roles_required('Admin')
        def my_endpoint(): ...

        @token_required
        @roles_required('Admin', 'Security Analyst')
        def my_endpoint(): ...

    Admin always has access to all roles.
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not hasattr(g, 'current_user') or not g.current_user:
                return jsonify({'error': 'Authentication required'}), 401

            # Admin always has full access
            if g.current_user.role == 'Admin':
                return f(*args, **kwargs)

            if g.current_user.role not in allowed_roles:
                return jsonify({
                    'error': 'Forbidden',
                    'message': f'You do not have permission to perform this action. Required role: {", ".join(allowed_roles)}'
                }), 403

            return f(*args, **kwargs)
        return decorated
    return decorator
