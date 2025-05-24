from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_mail import Mail
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from celery import Celery
import redis

db = SQLAlchemy()
jwt = JWTManager()
mail = Mail()

cache = None

def init_cache(app):
    global cache
    import redis
    cache = redis.from_url(app.config['REDIS_URL'])
    return cache

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["1000 per hour"]
)

celery = Celery('image_search_app')

def init_celery(app):
    celery.conf.update(
        broker_url=app.config['CELERY_BROKER_URL'],
        result_backend=app.config['CELERY_RESULT_BACKEND'],
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='UTC',
        enable_utc=True,
        worker_prefetch_multiplier=1,
        task_acks_late=True,
        worker_max_tasks_per_child=100,
        task_routes={
            'tasks.image_tasks.*': {'queue': 'image_processing'},
            'tasks.face_tasks.*': {'queue': 'face_processing'},
            'tasks.maintenance_tasks.*': {'queue': 'maintenance'},
        },
        beat_schedule=app.config.get('CELERY_BEAT_SCHEDULE', {})
    )
    return celery