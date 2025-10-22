import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', os.urandom(32))
    
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 20,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
        'pool_timeout': 30,
        'max_overflow': 40
    }
    
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/1')
    
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', os.urandom(32))
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(seconds=int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 3600)))
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(seconds=int(os.getenv('JWT_REFRESH_TOKEN_EXPIRES', 2592000)))
    JWT_ALGORITHM = 'HS256'
    
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER')
    
    FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000')
    
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'static/uploads')
    ALLOWED_EXTENSIONS = set(os.getenv('ALLOWED_EXTENSIONS', 'jpg,jpeg,png,gif,webp').split(','))
    
    RATELIMIT_STORAGE_URL = os.getenv('RATE_LIMIT_STORAGE_URL', 'redis://localhost:6379/2')
    RATELIMIT_DEFAULT = os.getenv('RATE_LIMIT_DEFAULT', '1000 per hour')
    RATELIMIT_HEADERS_ENABLED = True
    
    CORS_ORIGINS = ['*']  # Configure properly for production
    
    VECTOR_DB_TYPE = os.getenv('VECTOR_DB_TYPE', 'chromadb')
    CHROMADB_PATH = os.getenv('CHROMADB_PATH', './chroma_db')
    PINECONE_API_KEY = os.getenv('PINECONE_API_KEY')
    PINECONE_ENVIRONMENT = os.getenv('PINECONE_ENVIRONMENT')
    
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/app.log')
    AUDIT_LOG_FILE = os.getenv('AUDIT_LOG_FILE', 'logs/audit.log')
    
    ENABLE_METRICS = os.getenv('ENABLE_METRICS', 'True').lower() == 'true'
    METRICS_PORT = int(os.getenv('METRICS_PORT', 9090))

    TIMEZONE = os.getenv('TIMEZONE', 'Africa/Harare')
    
    FACE_DETECTION_THRESHOLD = 0.99
    FACE_SIMILARITY_THRESHOLD = 0.55
    IMAGE_SIMILARITY_THRESHOLD = 0.85

    THUMBNAIL_SIZE = (300, 300)
    THUMBNAIL_QUALITY = 85
    
    BATCH_SIZE = int(os.getenv('BATCH_SIZE', 32))
    MAX_WORKERS = int(os.getenv('MAX_WORKERS', 4))
    
    CELERY_BEAT_SCHEDULE = {
        'process-pending-faces': {
            'task': 'tasks.face_tasks.process_pending_faces',
            'schedule': 30.0,
        },
        'cleanup-old-logs': {
            'task': 'tasks.maintenance_tasks.cleanup_old_logs',
            'schedule': 3600.0,
        },
    }