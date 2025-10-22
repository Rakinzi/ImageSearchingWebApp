from flask import current_app
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_mail import Mail
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_bcrypt import Bcrypt
from celery import Celery
import redis

db = SQLAlchemy()
jwt = JWTManager()
mail = Mail()
bcrypt = Bcrypt()

# Redis cache wrapper class
class RedisCache:
    def __init__(self):
        self._redis = None
    
    def init_app(self, app):
        self._redis = redis.from_url(app.config['REDIS_URL'])
        return self._redis
    
    def __getattr__(self, name):
        if self._redis is None:
            raise RuntimeError("Cache not initialized. Call init_app first.")
        return getattr(self._redis, name)

cache = RedisCache()

def create_limiter(app=None):
    """Create limiter with proper Redis storage configuration"""
    if app:
        storage_url = app.config.get('RATE_LIMIT_STORAGE_URL', app.config.get('REDIS_URL', 'redis://localhost:6379/2'))
    else:
        storage_url = 'redis://redis:6379/2'  # Default for Docker

    return Limiter(
        key_func=get_remote_address,
        default_limits=["1000 per hour"],
        storage_uri=storage_url
    )

# Initialize without app context for now
limiter = Limiter(key_func=get_remote_address)

celery = Celery('image_search_app')