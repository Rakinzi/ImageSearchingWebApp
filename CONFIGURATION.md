# Configuration Guide

## Table of Contents
- [Overview](#overview)
- [Environment Variables](#environment-variables)
- [Backend Configuration](#backend-configuration)
- [Frontend Configuration](#frontend-configuration)
- [Docker Configuration](#docker-configuration)
- [Development vs Production](#development-vs-production)
- [Common Configuration Tasks](#common-configuration-tasks)

## Overview

This application uses environment variables and configuration files to manage settings across different environments. The backend uses Python-based configuration with Pydantic validation, while the frontend uses Vite's environment variable system.

## Environment Variables

### Backend Environment Variables

Create a `.env` file in the `backend/` directory:

```bash
# Security
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here
JWT_ACCESS_TOKEN_EXPIRES=3600  # 1 hour in seconds
JWT_REFRESH_TOKEN_EXPIRES=2592000  # 30 days in seconds

# Database
DATABASE_URL=sqlite:///app.db
# For PostgreSQL: postgresql://user:password@localhost:5432/dbname

# Redis & Celery
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1
RATE_LIMIT_STORAGE_URL=redis://localhost:6379/2

# Email Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=your-email@gmail.com

# Frontend URL (for CORS and email links)
FRONTEND_URL=http://localhost:3000

# File Upload Settings
MAX_CONTENT_LENGTH=16777216  # 16MB in bytes
UPLOAD_FOLDER=static/uploads
ALLOWED_EXTENSIONS=jpg,jpeg,png,gif,webp

# Rate Limiting
RATE_LIMIT_DEFAULT=1000 per hour

# Vector Database
VECTOR_DB_TYPE=chromadb  # chromadb or pinecone
CHROMADB_PATH=./chroma_db
# For Pinecone:
# PINECONE_API_KEY=your-pinecone-api-key
# PINECONE_ENVIRONMENT=your-pinecone-environment

# Logging
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FILE=logs/app.log
AUDIT_LOG_FILE=logs/audit.log

# Monitoring
ENABLE_METRICS=True
METRICS_PORT=9090

# Localization
TIMEZONE=Africa/Harare

# Processing
BATCH_SIZE=32
MAX_WORKERS=4
```

### Frontend Environment Variables

Create a `.env` file in the `frontend/` directory:

```bash
# API Configuration
VITE_API_BASE_URL=http://localhost:8080

# Application Settings
VITE_APP_TITLE=Image Search App
VITE_APP_DESCRIPTION=Search and organize your images with AI

# Feature Flags
VITE_ENABLE_FACE_RECOGNITION=true
VITE_ENABLE_TEXT_EXTRACTION=true
VITE_ENABLE_SEMANTIC_SEARCH=true
```

## Backend Configuration

### Configuration Files

#### 1. Legacy Configuration (`config/settings.py`)

Used by v1 API endpoints. Key settings:

```python
class Config:
    # Security thresholds
    FACE_DETECTION_THRESHOLD = 0.99
    FACE_SIMILARITY_THRESHOLD = 0.55
    IMAGE_SIMILARITY_THRESHOLD = 0.85

    # Thumbnail settings
    THUMBNAIL_SIZE = (300, 300)
    THUMBNAIL_QUALITY = 85

    # Database connection pooling
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 20,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
        'pool_timeout': 30,
        'max_overflow': 40
    }
```

#### 2. Modern Configuration (`config/modern_settings.py`)

Used by v2 API endpoints with Pydantic validation:

```python
# Automatically validates environment variables
# Provides type safety and default values
# Includes comprehensive error messages
```

### Celery Beat Schedule

Periodic tasks are configured in `config/settings.py`:

```python
CELERY_BEAT_SCHEDULE = {
    'process-pending-faces': {
        'task': 'tasks.face_tasks.process_pending_faces',
        'schedule': 30.0,  # Run every 30 seconds
    },
    'cleanup-old-logs': {
        'task': 'tasks.maintenance_tasks.cleanup_old_logs',
        'schedule': 3600.0,  # Run every hour
    },
}
```

## Frontend Configuration

### Vite Configuration (`frontend/vite.config.ts`)

```typescript
export default defineConfig({
  plugins: [vue()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8080',
        changeOrigin: true,
      }
    }
  },
  build: {
    outDir: 'dist',
    sourcemap: true
  }
})
```

### API Service Configuration (`frontend/src/services/api.js`)

```javascript
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080';
```

## Docker Configuration

### Simple Docker Compose (`docker-compose.simple.yml`)

CPU-only version for most deployments:

```yaml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  app:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8080:8080"
    environment:
      - DATABASE_URL=sqlite:///app.db
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/0
    volumes:
      - ./static:/app/static
      - ./logs:/app/logs
    depends_on:
      - redis

  celery-worker:
    build:
      context: .
      dockerfile: Dockerfile
    command: celery -A main.celery worker --loglevel=info
    environment:
      - DATABASE_URL=sqlite:///app.db
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/0
    volumes:
      - ./static:/app/static
      - ./logs:/app/logs
    depends_on:
      - redis
      - app
```

### GPU Docker Compose (`docker-compose.yml`)

For deployments with NVIDIA GPU support:

```yaml
# Requires nvidia-docker runtime
# Uses GPU-accelerated ML models
# Better performance for image processing
```

### Environment Variables in Docker

Create `.env` file in `backend/` directory for Docker:

```bash
# All environment variables from Backend section above
# Docker will automatically load these
```

## Development vs Production

### Development Settings

**Backend:**
```bash
# .env for development
LOG_LEVEL=DEBUG
ENABLE_METRICS=True
FRONTEND_URL=http://localhost:3000
DATABASE_URL=sqlite:///dev.db
```

**Frontend:**
```bash
# .env.development
VITE_API_BASE_URL=http://localhost:8080
```

### Production Settings

**Backend:**
```bash
# .env.production
LOG_LEVEL=WARNING
SECRET_KEY=<strong-random-key>
JWT_SECRET_KEY=<strong-random-key>
DATABASE_URL=postgresql://user:pass@host:5432/dbname
FRONTEND_URL=https://yourdomain.com
CORS_ORIGINS=https://yourdomain.com
```

**Frontend:**
```bash
# .env.production
VITE_API_BASE_URL=https://api.yourdomain.com
```

**Security Checklist for Production:**
- [ ] Use strong SECRET_KEY and JWT_SECRET_KEY
- [ ] Configure specific CORS_ORIGINS (not '*')
- [ ] Use PostgreSQL instead of SQLite
- [ ] Enable HTTPS
- [ ] Set appropriate rate limits
- [ ] Configure email service properly
- [ ] Set LOG_LEVEL to WARNING or ERROR
- [ ] Backup database regularly
- [ ] Monitor logs and metrics

## Common Configuration Tasks

### 1. Changing the Database

**SQLite to PostgreSQL:**

```bash
# Install PostgreSQL driver
pip install psycopg2-binary

# Update .env
DATABASE_URL=postgresql://username:password@localhost:5432/imageapp

# Run migrations
flask db upgrade
```

### 2. Configuring Email Service

**Gmail:**
```bash
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password  # Use app-specific password
```

**Other providers:**
- Outlook: smtp-mail.outlook.com:587
- Yahoo: smtp.mail.yahoo.com:587
- SendGrid: smtp.sendgrid.net:587

### 3. Adjusting Image Processing Thresholds

Edit `backend/config/settings.py`:

```python
# Higher = more strict, fewer matches
FACE_DETECTION_THRESHOLD = 0.99  # 0.0 to 1.0
FACE_SIMILARITY_THRESHOLD = 0.55  # Lower = more matches
IMAGE_SIMILARITY_THRESHOLD = 0.85  # Lower = more matches
```

### 4. Scaling Worker Processes

```bash
# Increase concurrent workers
MAX_WORKERS=8  # in .env

# Or run multiple Celery workers
celery -A main.celery worker --concurrency=8
```

### 5. Changing Upload Limits

```bash
# Backend .env
MAX_CONTENT_LENGTH=33554432  # 32MB in bytes

# Also update nginx/proxy if using one
client_max_body_size 32M;
```

### 6. Using Pinecone Vector Database

```bash
# .env
VECTOR_DB_TYPE=pinecone
PINECONE_API_KEY=your-api-key
PINECONE_ENVIRONMENT=your-environment
```

### 7. Configuring Rate Limits

Edit `backend/config/settings.py`:

```python
RATELIMIT_DEFAULT = '1000 per hour'

# Or set per-endpoint in route decorators:
@limiter.limit("100 per hour")
def upload_endpoint():
    pass
```

### 8. Custom Celery Beat Schedule

Edit `config/settings.py`:

```python
CELERY_BEAT_SCHEDULE = {
    'custom-task': {
        'task': 'tasks.custom.my_task',
        'schedule': 300.0,  # 5 minutes
        'args': (arg1, arg2)
    }
}
```

### 9. Enabling/Disabling Features

**Backend** (`config/settings.py`):
```python
ENABLE_METRICS = True/False
ENABLE_FACE_DETECTION = True/False
```

**Frontend** (`.env`):
```bash
VITE_ENABLE_FACE_RECOGNITION=true/false
VITE_ENABLE_TEXT_EXTRACTION=true/false
```

### 10. Monitoring and Logging

**Log Files:**
```bash
# Configure in .env
LOG_FILE=logs/app.log
AUDIT_LOG_FILE=logs/audit.log

# Ensure directories exist
mkdir -p logs
```

**Metrics:**
```bash
# Enable Prometheus metrics
ENABLE_METRICS=True
METRICS_PORT=9090

# Access metrics at http://localhost:9090/metrics
```

## Troubleshooting Configuration

### Issue: "No module named 'config'"
**Solution:** Ensure you're running from the backend directory or PYTHONPATH is set correctly.

### Issue: Database connection errors
**Solution:** Check DATABASE_URL format and ensure database server is running.

### Issue: Redis connection errors
**Solution:** Ensure Redis is running on the specified REDIS_URL.

### Issue: CORS errors in frontend
**Solution:** Verify FRONTEND_URL in backend .env matches your frontend URL.

### Issue: File upload fails
**Solution:** Check MAX_CONTENT_LENGTH and ALLOWED_EXTENSIONS settings.

### Issue: Celery tasks not processing
**Solution:** Ensure Celery worker is running and CELERY_BROKER_URL is correct.

## Configuration Validation

The modern configuration system validates settings on startup:

```bash
# Run backend to validate configuration
cd backend
python main.py

# Check for validation errors in output
# Errors will show missing or invalid configuration
```

## Best Practices

1. **Never commit `.env` files** - Add them to `.gitignore`
2. **Use environment-specific files** - `.env.development`, `.env.production`
3. **Generate strong secrets** - Use `python -c "import secrets; print(secrets.token_hex(32))"`
4. **Document custom settings** - Add comments to your `.env` file
5. **Validate configuration** - Test in development before deploying
6. **Backup configuration** - Keep secure backups of production `.env` files
7. **Use Docker secrets** - For sensitive data in production Docker deployments
8. **Monitor configuration changes** - Track changes in version control (template files only)
9. **Test with production-like settings** - Use staging environment
10. **Keep dependencies updated** - Regularly update requirements.txt and package.json

## Quick Start Configurations

### Minimal Development Setup

**Backend .env:**
```bash
SECRET_KEY=dev-secret-key
JWT_SECRET_KEY=dev-jwt-key
DATABASE_URL=sqlite:///app.db
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
```

**Frontend .env:**
```bash
VITE_API_BASE_URL=http://localhost:8080
```

### Production-Ready Setup

See [Development vs Production](#development-vs-production) section above.

## Additional Resources

- [Flask Configuration Documentation](https://flask.palletsprojects.com/en/2.3.x/config/)
- [Celery Configuration Reference](https://docs.celeryproject.org/en/stable/userguide/configuration.html)
- [Vite Environment Variables](https://vitejs.dev/guide/env-and-mode.html)
- [Pydantic Settings Management](https://docs.pydantic.dev/latest/usage/settings/)
