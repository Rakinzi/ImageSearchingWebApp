from flask import request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_jwt_extended import get_jwt_identity
from functools import wraps
from middleware.audit_logger import AuditLogger

def get_user_id():
    try:
        user_id = get_jwt_identity()
        return f"user:{user_id}" if user_id else get_remote_address()
    except Exception:
        return get_remote_address()

def setup_rate_limiting(limiter):
    @limiter.request_filter
    def exempt_health_checks():
        return request.endpoint in ['health_check', 'metrics']
    
    @limiter.request_filter
    def exempt_static_files():
        return request.path.startswith('/static/')
    
    limiter.key_func = get_user_id

def rate_limit_exceeded_handler(e):
    user_id = None
    try:
        user_id = get_jwt_identity()
    except Exception:
        pass
    
    AuditLogger.log_rate_limit_exceeded(
        ip_address=request.remote_addr,
        endpoint=request.endpoint,
        user_id=user_id
    )
    
    return jsonify({
        'error': 'Rate limit exceeded',
        'message': str(e.description),
        'retry_after': getattr(e, 'retry_after', None)
    }), 429

def custom_rate_limit(rate, per=None, key_func=None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def smart_rate_limit(authenticated_rate, unauthenticated_rate):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                user_id = get_jwt_identity()
                if user_id:
                    return f(*args, **kwargs)
                else:
                    return f(*args, **kwargs)
            except Exception:
                return f(*args, **kwargs)
        return decorated_function
    return decorator

class SmartRateLimiter:
    def __init__(self, redis_client=None):
        self.redis_client = redis_client
    
    def check_rate_limit(self, key, limit, window, increment=1):
        if not self.redis_client:
            return True
        
        try:
            pipe = self.redis_client.pipeline()
            pipe.multi()
            
            current_count = self.redis_client.get(key)
            if current_count is None:
                pipe.setex(key, window, increment)
                pipe.execute()
                return True
            
            current_count = int(current_count)
            if current_count < limit:
                pipe.incr(key)
                pipe.execute()
                return True
            
            return False
            
        except Exception:
            return True
    
    def get_remaining_requests(self, key, limit):
        if not self.redis_client:
            return limit
        
        try:
            current_count = self.redis_client.get(key)
            if current_count is None:
                return limit
            return max(0, limit - int(current_count))
        except Exception:
            return limit
    
    def get_reset_time(self, key):
        if not self.redis_client:
            return None
        
        try:
            return self.redis_client.ttl(key)
        except Exception:
            return None

def adaptive_rate_limit(base_limit=100, window=3600):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                user_id = get_jwt_identity()
                
                if user_id:
                    from models.user import User
                    user = User.query.get(user_id)
                    if user and user.is_admin:
                        return f(*args, **kwargs)
                    
                    key = f"rate_limit:user:{user_id}:{request.endpoint}"
                    limit = base_limit * 2
                else:
                    key = f"rate_limit:ip:{request.remote_addr}:{request.endpoint}"
                    limit = base_limit
                
                rate_limiter = SmartRateLimiter()
                if not rate_limiter.check_rate_limit(key, limit, window):
                    AuditLogger.log_rate_limit_exceeded(
                        ip_address=request.remote_addr,
                        endpoint=request.endpoint,
                        user_id=user_id
                    )
                    
                    return jsonify({
                        'error': 'Rate limit exceeded',
                        'limit': limit,
                        'window': window,
                        'remaining': 0
                    }), 429
                
                response = f(*args, **kwargs)
                
                remaining = rate_limiter.get_remaining_requests(key, limit)
                reset_time = rate_limiter.get_reset_time(key)
                
                if hasattr(response, 'headers'):
                    response.headers['X-RateLimit-Limit'] = str(limit)
                    response.headers['X-RateLimit-Remaining'] = str(remaining)
                    if reset_time:
                        response.headers['X-RateLimit-Reset'] = str(reset_time)
                
                return response
                
            except Exception as e:
                return f(*args, **kwargs)
        
        return decorated_function
    return decorator

RATE_LIMIT_RULES = {
    'auth': {
        'login': '10 per minute',
        'register': '5 per minute',
        'password_reset': '3 per minute',
        'verify_email': '5 per minute'
    },
    'images': {
        'upload': '20 per hour',
        'search': '100 per hour',
        'list': '200 per hour',
        'delete': '50 per hour'
    },
    'faces': {
        'process': '50 per hour',
        'search': '100 per hour',
        'cluster': '10 per hour'
    },
    'admin': {
        'audit_logs': '100 per hour',
        'user_management': '50 per hour'
    }
}