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

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["1000 per hour"]
)

celery = Celery('image_search_app')