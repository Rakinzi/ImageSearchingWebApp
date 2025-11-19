"""
Modern configuration management using Pydantic for validation and type safety.
"""
import os
from datetime import timedelta
from typing import Dict, List, Optional, Union
from pathlib import Path

from pydantic import BaseSettings, Field, validator, AnyUrl
from pydantic.env_settings import SettingsSourceCallable


class DatabaseConfig(BaseSettings):
    """Database configuration settings."""
    url: str = Field(default="sqlite:///app.db", env="DATABASE_URL")
    track_modifications: bool = False
    pool_size: int = 20
    pool_recycle: int = 3600
    pool_pre_ping: bool = True
    pool_timeout: int = 30
    max_overflow: int = 40

    @validator('url')
    def validate_db_url(cls, v):
        if not v:
            raise ValueError('Database URL cannot be empty')
        return v

    @property
    def engine_options(self) -> Dict:
        return {
            'pool_size': self.pool_size,
            'pool_recycle': self.pool_recycle,
            'pool_pre_ping': self.pool_pre_ping,
            'pool_timeout': self.pool_timeout,
            'max_overflow': self.max_overflow
        }


class RedisConfig(BaseSettings):
    """Redis configuration settings."""
    url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    rate_limit_url: str = Field(default="redis://localhost:6379/2", env="RATE_LIMIT_STORAGE_URL")

    @validator('url', 'rate_limit_url')
    def validate_redis_url(cls, v):
        if not v.startswith(('redis://', 'rediss://')):
            raise ValueError('Redis URL must start with redis:// or rediss://')
        return v


class CeleryConfig(BaseSettings):
    """Celery configuration settings."""
    broker_url: str = Field(default="redis://localhost:6379/0", env="CELERY_BROKER_URL")
    result_backend: str = Field(default="redis://localhost:6379/1", env="CELERY_RESULT_BACKEND")

    @property
    def beat_schedule(self) -> Dict:
        return {
            'process-pending-faces': {
                'task': 'tasks.face_tasks.process_pending_faces',
                'schedule': 30.0,
            },
            'cleanup-old-logs': {
                'task': 'tasks.maintenance_tasks.cleanup_old_logs',
                'schedule': 3600.0,
            },
        }


class JWTConfig(BaseSettings):
    """JWT authentication configuration."""
    secret_key: str = Field(env="JWT_SECRET_KEY")
    algorithm: str = "HS256"
    access_token_expires: int = Field(default=3600, env="JWT_ACCESS_TOKEN_EXPIRES")
    refresh_token_expires: int = Field(default=2592000, env="JWT_REFRESH_TOKEN_EXPIRES")

    @validator('secret_key')
    def validate_secret_key(cls, v):
        if not v or len(v) < 32:
            raise ValueError('JWT secret key must be at least 32 characters long')
        return v

    @property
    def access_token_delta(self) -> timedelta:
        return timedelta(seconds=self.access_token_expires)

    @property
    def refresh_token_delta(self) -> timedelta:
        return timedelta(seconds=self.refresh_token_expires)


class EmailConfig(BaseSettings):
    """Email configuration settings."""
    server: str = Field(default="smtp.gmail.com", env="MAIL_SERVER")
    port: int = Field(default=587, env="MAIL_PORT")
    use_tls: bool = Field(default=True, env="MAIL_USE_TLS")
    username: Optional[str] = Field(env="MAIL_USERNAME")
    password: Optional[str] = Field(env="MAIL_PASSWORD")
    default_sender: Optional[str] = Field(env="MAIL_DEFAULT_SENDER")

    @validator('port')
    def validate_port(cls, v):
        if not 1 <= v <= 65535:
            raise ValueError('Port must be between 1 and 65535')
        return v


class SecurityConfig(BaseSettings):
    """Security configuration settings."""
    secret_key: str = Field(env="SECRET_KEY")
    cors_origins: List[str] = Field(default=["*"])
    max_content_length: int = Field(default=16 * 1024 * 1024, env="MAX_CONTENT_LENGTH")  # 16MB
    allowed_extensions: List[str] = Field(default=["jpg", "jpeg", "png", "gif", "webp"])

    @validator('secret_key')
    def validate_secret_key(cls, v):
        if not v or len(v) < 32:
            raise ValueError('Secret key must be at least 32 characters long')
        return v

    @validator('cors_origins', pre=True)
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v

    @validator('allowed_extensions', pre=True)
    def parse_allowed_extensions(cls, v):
        if isinstance(v, str):
            return [ext.strip().lower() for ext in v.split(',')]
        return v


class FileUploadConfig(BaseSettings):
    """File upload configuration."""
    upload_folder: str = Field(default="static/uploads", env="UPLOAD_FOLDER")
    thumbnail_size: tuple = (128, 128)
    thumbnail_quality: int = 85
    batch_size: int = Field(default=32, env="BATCH_SIZE")
    max_workers: int = Field(default=4, env="MAX_WORKERS")

    @validator('upload_folder')
    def validate_upload_folder(cls, v):
        path = Path(v)
        path.mkdir(parents=True, exist_ok=True)
        return str(path)


class AIConfig(BaseSettings):
    """AI/ML configuration settings."""
    vector_db_type: str = Field(default="chromadb", env="VECTOR_DB_TYPE")
    chromadb_path: str = Field(default="./chroma_db", env="CHROMADB_PATH")
    pinecone_api_key: Optional[str] = Field(env="PINECONE_API_KEY")
    pinecone_environment: Optional[str] = Field(env="PINECONE_ENVIRONMENT")

    # Detection thresholds
    face_detection_threshold: float = 0.99
    face_similarity_threshold: float = 0.55
    image_similarity_threshold: float = 0.85

    @validator('vector_db_type')
    def validate_vector_db_type(cls, v):
        allowed_types = ['chromadb', 'pinecone', 'pgvector']
        if v not in allowed_types:
            raise ValueError(f'Vector DB type must be one of: {allowed_types}')
        return v

    @validator('chromadb_path')
    def validate_chromadb_path(cls, v):
        path = Path(v)
        path.mkdir(parents=True, exist_ok=True)
        return str(path)


class LoggingConfig(BaseSettings):
    """Logging configuration."""
    level: str = Field(default="INFO", env="LOG_LEVEL")
    file: str = Field(default="logs/app.log", env="LOG_FILE")
    audit_file: str = Field(default="logs/audit.log", env="AUDIT_LOG_FILE")

    @validator('level')
    def validate_log_level(cls, v):
        allowed_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in allowed_levels:
            raise ValueError(f'Log level must be one of: {allowed_levels}')
        return v.upper()

    @validator('file', 'audit_file')
    def validate_log_file(cls, v):
        path = Path(v)
        path.parent.mkdir(parents=True, exist_ok=True)
        return str(path)


class MonitoringConfig(BaseSettings):
    """Monitoring and metrics configuration."""
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    metrics_port: int = Field(default=9090, env="METRICS_PORT")

    @validator('metrics_port')
    def validate_metrics_port(cls, v):
        if not 1024 <= v <= 65535:
            raise ValueError('Metrics port must be between 1024 and 65535')
        return v


class RateLimitConfig(BaseSettings):
    """Rate limiting configuration."""
    default_limit: str = Field(default="1000 per hour", env="RATE_LIMIT_DEFAULT")
    headers_enabled: bool = True


class ModernConfig(BaseSettings):
    """
    Modern configuration management with validation and type safety.

    This replaces the old Config class with a more structured approach
    using Pydantic for automatic validation and environment variable handling.
    """

    # Application settings
    debug: bool = Field(default=False, env="DEBUG")
    testing: bool = Field(default=False, env="TESTING")
    frontend_url: str = Field(default="http://localhost:3000", env="FRONTEND_URL")
    timezone: str = Field(default="Africa/Harare", env="TIMEZONE")

    # Component configurations
    database: DatabaseConfig = DatabaseConfig()
    redis: RedisConfig = RedisConfig()
    celery: CeleryConfig = CeleryConfig()
    jwt: JWTConfig = JWTConfig()
    email: EmailConfig = EmailConfig()
    security: SecurityConfig = SecurityConfig()
    file_upload: FileUploadConfig = FileUploadConfig()
    ai: AIConfig = AIConfig()
    logging: LoggingConfig = LoggingConfig()
    monitoring: MonitoringConfig = MonitoringConfig()
    rate_limiting: RateLimitConfig = RateLimitConfig()

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        allow_population_by_field_name = True

    def to_flask_config(self) -> Dict:
        """Convert to Flask configuration dictionary for backward compatibility."""
        return {
            # Flask settings
            'DEBUG': self.debug,
            'TESTING': self.testing,
            'SECRET_KEY': self.security.secret_key,

            # Database
            'SQLALCHEMY_DATABASE_URI': self.database.url,
            'SQLALCHEMY_TRACK_MODIFICATIONS': self.database.track_modifications,
            'SQLALCHEMY_ENGINE_OPTIONS': self.database.engine_options,

            # Redis
            'REDIS_URL': self.redis.url,
            'RATELIMIT_STORAGE_URL': self.redis.rate_limit_url,

            # Celery
            'CELERY_BROKER_URL': self.celery.broker_url,
            'CELERY_RESULT_BACKEND': self.celery.result_backend,
            'CELERY_BEAT_SCHEDULE': self.celery.beat_schedule,

            # JWT
            'JWT_SECRET_KEY': self.jwt.secret_key,
            'JWT_ALGORITHM': self.jwt.algorithm,
            'JWT_ACCESS_TOKEN_EXPIRES': self.jwt.access_token_delta,
            'JWT_REFRESH_TOKEN_EXPIRES': self.jwt.refresh_token_delta,

            # Email
            'MAIL_SERVER': self.email.server,
            'MAIL_PORT': self.email.port,
            'MAIL_USE_TLS': self.email.use_tls,
            'MAIL_USERNAME': self.email.username,
            'MAIL_PASSWORD': self.email.password,
            'MAIL_DEFAULT_SENDER': self.email.default_sender,

            # Security
            'CORS_ORIGINS': self.security.cors_origins,
            'MAX_CONTENT_LENGTH': self.security.max_content_length,
            'ALLOWED_EXTENSIONS': set(self.security.allowed_extensions),

            # File upload
            'UPLOAD_FOLDER': self.file_upload.upload_folder,
            'THUMBNAIL_SIZE': self.file_upload.thumbnail_size,
            'THUMBNAIL_QUALITY': self.file_upload.thumbnail_quality,
            'BATCH_SIZE': self.file_upload.batch_size,
            'MAX_WORKERS': self.file_upload.max_workers,

            # AI/ML
            'VECTOR_DB_TYPE': self.ai.vector_db_type,
            'CHROMADB_PATH': self.ai.chromadb_path,
            'PINECONE_API_KEY': self.ai.pinecone_api_key,
            'PINECONE_ENVIRONMENT': self.ai.pinecone_environment,
            'FACE_DETECTION_THRESHOLD': self.ai.face_detection_threshold,
            'FACE_SIMILARITY_THRESHOLD': self.ai.face_similarity_threshold,
            'IMAGE_SIMILARITY_THRESHOLD': self.ai.image_similarity_threshold,

            # Logging
            'LOG_LEVEL': self.logging.level,
            'LOG_FILE': self.logging.file,
            'AUDIT_LOG_FILE': self.logging.audit_file,

            # Monitoring
            'ENABLE_METRICS': self.monitoring.enable_metrics,
            'METRICS_PORT': self.monitoring.metrics_port,

            # Rate limiting
            'RATELIMIT_DEFAULT': self.rate_limiting.default_limit,
            'RATELIMIT_HEADERS_ENABLED': self.rate_limiting.headers_enabled,

            # Frontend
            'FRONTEND_URL': self.frontend_url,

            # Timezone
            'TIMEZONE': self.timezone,
        }