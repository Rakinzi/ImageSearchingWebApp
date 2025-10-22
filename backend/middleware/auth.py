from flask import jsonify, request, current_app
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from functools import wraps
from models.user import User
from models.audit_log import AuditLog
from datetime import datetime

def setup_jwt_handlers(jwt):
    @jwt.additional_claims_loader
    def add_claims_to_jwt(identity):
        user = User.query.get(identity)
        if user:
            return {
                'is_admin': user.is_admin,
                'is_verified': user.is_verified,
                'name': user.name,
                'email': user.email
            }
        return {}
    
    @jwt.user_identity_loader
    def user_identity_lookup(user):
        # Convert to string for PyJWT compatibility
        if hasattr(user, 'id'):
            return str(user.id)
        return str(user) if user is not None else None
    
    @jwt.user_lookup_loader
    def user_lookup_callback(_jwt_header, jwt_data):
        identity = jwt_data["sub"]
        # Convert string identity back to integer for database lookup
        try:
            user_id = int(identity)
            return User.query.filter_by(id=user_id).one_or_none()
        except (ValueError, TypeError):
            return None
    
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        AuditLog.log_auth_event(
            'token_expired',
            user_id=jwt_payload.get('sub'),
            ip_address=request.remote_addr if request else None,
            status='failure'
        )
        return jsonify({'error': 'Token has expired'}), 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        AuditLog.log_security_event(
            'invalid_token_attempt',
            ip_address=request.remote_addr if request else None,
            user_agent=request.headers.get('User-Agent') if request else None,
            additional_data={'error': str(error)},
            risk_level='medium'
        )
        return jsonify({'error': 'Invalid token'}), 401
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({'error': 'Authorization token is required'}), 401
    
    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        AuditLog.log_security_event(
            'revoked_token_used',
            user_id=jwt_payload.get('sub'),
            ip_address=request.remote_addr if request else None,
            risk_level='high'
        )
        return jsonify({'error': 'Token has been revoked'}), 401

def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            verify_jwt_in_request()
            current_user_id = get_jwt_identity()
            # Convert string identity back to integer for database lookup
            try:
                user_id = int(current_user_id)
                user = User.query.get(user_id)
            except (ValueError, TypeError):
                return jsonify({'error': 'Invalid user identity'}), 401

            if not user or not user.is_active:
                AuditLog.log_security_event(
                    'inactive_user_access_attempt',
                    user_id=current_user_id,
                    ip_address=request.remote_addr,
                    risk_level='medium'
                )
                return jsonify({'error': 'User account is inactive'}), 403
            
            if not user.is_verified:
                return jsonify({'error': 'Email verification required'}), 403
            
            return f(current_user=user, *args, **kwargs)
        except Exception as e:
            current_app.logger.error(f"Authentication error: {str(e)}")
            return jsonify({'error': 'Authentication failed'}), 401
    
    return decorated_function

def require_admin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            verify_jwt_in_request()
            current_user_id = get_jwt_identity()
            # Convert string identity back to integer for database lookup
            try:
                user_id = int(current_user_id)
                user = User.query.get(user_id)
            except (ValueError, TypeError):
                return jsonify({'error': 'Invalid user identity'}), 401

            if not user or not user.is_active:
                return jsonify({'error': 'User account is inactive'}), 403
            
            if not user.is_admin:
                AuditLog.log_security_event(
                    'unauthorized_admin_access',
                    user_id=current_user_id,
                    ip_address=request.remote_addr,
                    risk_level='high'
                )
                return jsonify({'error': 'Admin privileges required'}), 403
            
            return f(current_user=user, *args, **kwargs)
        except Exception as e:
            current_app.logger.error(f"Admin authentication error: {str(e)}")
            return jsonify({'error': 'Authentication failed'}), 401
    
    return decorated_function

def require_verified_user(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            verify_jwt_in_request()
            current_user_id = get_jwt_identity()
            # Convert string identity back to integer for database lookup
            try:
                user_id = int(current_user_id)
                user = User.query.get(user_id)
            except (ValueError, TypeError):
                return jsonify({'error': 'Invalid user identity'}), 401

            if not user or not user.is_active:
                return jsonify({'error': 'User account is inactive'}), 403
            
            if not user.is_verified:
                return jsonify({'error': 'Email verification required'}), 403
            
            return f(current_user=user, *args, **kwargs)
        except Exception as e:
            current_app.logger.error(f"Verification error: {str(e)}")
            return jsonify({'error': 'Authentication failed'}), 401
    
    return decorated_function

def optional_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        current_user = None
        try:
            verify_jwt_in_request(optional=True)
            current_user_id = get_jwt_identity()
            if current_user_id:
                try:
                    user_id = int(current_user_id)
                    current_user = User.query.get(user_id)
                except (ValueError, TypeError):
                    current_user = None
        except Exception:
            pass
        
        return f(current_user=current_user, *args, **kwargs)
    
    return decorated_function

def get_current_user():
    try:
        verify_jwt_in_request(optional=True)
        current_user_id = get_jwt_identity()
        if current_user_id:
            try:
                user_id = int(current_user_id)
                return User.query.get(user_id)
            except (ValueError, TypeError):
                return None
    except Exception:
        pass
    return None