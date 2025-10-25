# Docker Setup Guide (Simple CPU Version)

## Quick Start

```bash
cd backend
docker-compose -f docker-compose.simple.yml up -d
```

That's it! The application will be available at `http://localhost:8080`

## What's Included

The simple Docker setup includes **all features**:

✅ **Embeddings** - CLIP-based semantic search
✅ **Face Detection** - MTCNN + FaceNet512
✅ **OCR** - EasyOCR text extraction
✅ **Background Processing** - Celery workers
✅ **Redis** - Caching and task queue
✅ **PostgreSQL** (optional) or SQLite

## Services

When you run `docker-compose -f docker-compose.simple.yml up`, these services start:

| Service | Purpose | Port |
|---------|---------|------|
| **app** | Main Flask API | 8080 |
| **celery-worker** | Background task processor | - |
| **redis** | Cache & message broker | 6379 |

## Configuration

### Environment Variables

Create a `.env` file in the `backend/` directory:

```bash
# Required
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-here

# Database (SQLite default, or use PostgreSQL)
DATABASE_URL=sqlite:///app.db
# For PostgreSQL: postgresql://user:password@postgres:5432/imageapp

# Redis (use service name in Docker)
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/1

# Feature Configuration
FACE_DETECTION_THRESHOLD=0.99
FACE_SIMILARITY_THRESHOLD=0.55
IMAGE_SIMILARITY_THRESHOLD=0.85

# OCR Backend (auto-detects available)
OCR_BACKEND=auto

# Uploads
UPLOAD_FOLDER=/app/static/uploads
MAX_CONTENT_LENGTH=16777216

# Vector Database
CHROMADB_PATH=/app/chroma_db
```

### Generate Secret Keys

```bash
python -c "import secrets; print('SECRET_KEY=' + secrets.token_hex(32))"
python -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_hex(32))"
```

Add these to your `.env` file.

## First Time Setup

### 1. Start Services

```bash
cd backend
docker-compose -f docker-compose.simple.yml up -d
```

### 2. Check Logs

```bash
# All services
docker-compose -f docker-compose.simple.yml logs -f

# Just the app
docker-compose -f docker-compose.simple.yml logs -f app

# Just the worker
docker-compose -f docker-compose.simple.yml logs -f celery-worker
```

### 3. Initialize Database

```bash
# Run migrations inside container
docker-compose -f docker-compose.simple.yml exec app flask db upgrade
```

### 4. Test the System

```bash
# Health check
curl http://localhost:8080/health

# Should return:
# {
#   "status": "healthy",
#   "database": "connected",
#   "redis": "connected",
#   "vector_service": {...},
#   "face_service": {...},
#   "ocr_service": {...}
# }
```

### 5. Create First User

```bash
curl -X POST http://localhost:8080/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123",
    "name": "Test User"
  }'
```

### 6. Upload Test Image

```bash
# Login first
TOKEN=$(curl -X POST http://localhost:8080/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password123"}' \
  | jq -r '.data.access_token')

# Upload image with all features enabled
curl -X POST http://localhost:8080/api/v2/images/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/path/to/your/image.jpg" \
  -F "extract_text=true" \
  -F "detect_faces=true" \
  -F "generate_embeddings=true"
```

## Testing Features

### Test Embeddings

```bash
# Run inside container
docker-compose -f docker-compose.simple.yml exec app python utils/test_embeddings.py
```

### Test Face Detection

```bash
docker-compose -f docker-compose.simple.yml exec app python utils/test_face_detection.py
```

### Test OCR

```bash
docker-compose -f docker-compose.simple.yml exec app python utils/test_ocr.py
```

## Managing Docker Services

### Start Services

```bash
docker-compose -f docker-compose.simple.yml up -d
```

### Stop Services

```bash
docker-compose -f docker-compose.simple.yml down
```

### Restart Services

```bash
docker-compose -f docker-compose.simple.yml restart
```

### Rebuild After Changes

```bash
# Rebuild images
docker-compose -f docker-compose.simple.yml build

# Rebuild and restart
docker-compose -f docker-compose.simple.yml up -d --build
```

### View Logs

```bash
# All logs
docker-compose -f docker-compose.simple.yml logs -f

# Specific service
docker-compose -f docker-compose.simple.yml logs -f app
docker-compose -f docker-compose.simple.yml logs -f celery-worker
docker-compose -f docker-compose.simple.yml logs -f redis

# Last 100 lines
docker-compose -f docker-compose.simple.yml logs --tail=100
```

### Execute Commands in Container

```bash
# Open shell
docker-compose -f docker-compose.simple.yml exec app /bin/bash

# Run Python script
docker-compose -f docker-compose.simple.yml exec app python script.py

# Run Flask command
docker-compose -f docker-compose.simple.yml exec app flask db upgrade
```

## Data Persistence

### Volumes

The Docker setup creates volumes for:

| Volume | Purpose | Location |
|--------|---------|----------|
| **Static files** | Uploaded images | `./static:/app/static` |
| **Logs** | Application logs | `./logs:/app/logs` |
| **ChromaDB** | Vector database | `./chroma_db:/app/chroma_db` |
| **Redis data** | Cache data | `redis_data` (named volume) |

### Backup Data

```bash
# Backup uploads
tar -czf uploads-backup.tar.gz static/uploads/

# Backup database (SQLite)
docker-compose -f docker-compose.simple.yml exec app cp /app/app.db /app/static/app.db
cp static/app.db app-backup.db

# Backup vector database
tar -czf chroma-backup.tar.gz chroma_db/

# Backup everything
tar -czf full-backup.tar.gz static/ logs/ chroma_db/ app.db
```

### Restore Data

```bash
# Restore uploads
tar -xzf uploads-backup.tar.gz

# Restore database
cp app-backup.db static/app.db
docker-compose -f docker-compose.simple.yml exec app cp /app/static/app.db /app/app.db

# Restore vector database
tar -xzf chroma-backup.tar.gz
```

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose -f docker-compose.simple.yml logs app

# Common issues:
# - Port 8080 already in use
# - Missing .env file
# - Invalid environment variables
```

### Out of Memory

If you see OOM errors:

```bash
# Increase Docker memory limit
# Docker Desktop → Settings → Resources → Memory → 4GB+
```

For the simple CPU version, recommend **4GB+ RAM**.

### Redis Connection Failed

```bash
# Check Redis is running
docker-compose -f docker-compose.simple.yml ps redis

# Check connection
docker-compose -f docker-compose.simple.yml exec redis redis-cli ping
# Should return: PONG
```

### Database Migration Failed

```bash
# Remove old migrations
docker-compose -f docker-compose.simple.yml exec app rm -rf migrations/

# Reinitialize
docker-compose -f docker-compose.simple.yml exec app flask db init
docker-compose -f docker-compose.simple.yml exec app flask db migrate
docker-compose -f docker-compose.simple.yml exec app flask db upgrade
```

### Celery Worker Not Processing

```bash
# Check worker logs
docker-compose -f docker-compose.simple.yml logs -f celery-worker

# Restart worker
docker-compose -f docker-compose.simple.yml restart celery-worker

# Check Redis connection
docker-compose -f docker-compose.simple.yml exec celery-worker celery -A main.celery inspect ping
```

### OCR Not Working

```bash
# Check if EasyOCR is installed
docker-compose -f docker-compose.simple.yml exec app python -c "import easyocr; print('OK')"

# Test OCR
docker-compose -f docker-compose.simple.yml exec app python utils/test_ocr.py --test 1

# If models not downloaded, they'll download on first use (~1GB)
# Check logs for download progress
```

### Face Detection Not Working

```bash
# Test face detection
docker-compose -f docker-compose.simple.yml exec app python utils/test_face_detection.py --test 1

# Check if models are downloaded
docker-compose -f docker-compose.simple.yml exec app python -c "import facenet_pytorch; print('OK')"
```

## Performance Optimization

### CPU Performance

The simple Docker setup uses **CPU-only** versions of all libraries.

**Expected Performance** (per image):
- Image embeddings: ~2s
- Face detection: ~1.5s
- OCR: ~2-3s
- **Total: ~5-6s per image**

### Optimize for Speed

1. **Reduce Image Resolution**:
```bash
# In .env
MAX_IMAGE_DIMENSION=2000
```

2. **Adjust Worker Concurrency**:
```yaml
# In docker-compose.simple.yml
command: celery -A main.celery worker --concurrency=2
```

3. **Disable Unused Features**:
Upload with only needed features enabled via frontend toggles.

### Scale Workers

```bash
# Add more workers
docker-compose -f docker-compose.simple.yml up -d --scale celery-worker=3
```

## Production Deployment

### Security Checklist

- [ ] Use strong `SECRET_KEY` and `JWT_SECRET_KEY`
- [ ] Change default database password
- [ ] Use PostgreSQL instead of SQLite
- [ ] Enable HTTPS (use reverse proxy)
- [ ] Set proper `CORS_ORIGINS`
- [ ] Configure firewall rules
- [ ] Regular backups
- [ ] Monitor logs

### Recommended Setup

```yaml
# Production docker-compose.yml
version: '3.8'

services:
  app:
    restart: always
    environment:
      - LOG_LEVEL=WARNING
      - ENABLE_METRICS=True
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G

  celery-worker:
    restart: always
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '2'
          memory: 3G

  redis:
    restart: always
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes
```

### Use Nginx Reverse Proxy

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        client_max_body_size 16M;
    }
}
```

## Monitoring

### Health Check

```bash
# Check system health
curl http://localhost:8080/health | jq

# Check metrics (Prometheus format)
curl http://localhost:8080/metrics
```

### View Resource Usage

```bash
# Container stats
docker stats

# Specific service
docker-compose -f docker-compose.simple.yml top app
```

### Log Monitoring

```bash
# Watch logs in real-time
docker-compose -f docker-compose.simple.yml logs -f | grep -i "error\|warning\|failed"

# Save logs
docker-compose -f docker-compose.simple.yml logs > app-logs-$(date +%Y%m%d).log
```

## Updates

### Update Code

```bash
# Pull latest code
git pull

# Rebuild and restart
docker-compose -f docker-compose.simple.yml down
docker-compose -f docker-compose.simple.yml up -d --build

# Run migrations
docker-compose -f docker-compose.simple.yml exec app flask db upgrade
```

### Update Dependencies

```bash
# Edit requirements-cpu.txt
# Then rebuild
docker-compose -f docker-compose.simple.yml build --no-cache
docker-compose -f docker-compose.simple.yml up -d
```

## Summary

**Simple Docker Setup Provides**:
- ✅ All features working (embeddings, faces, OCR)
- ✅ Easy one-command start
- ✅ CPU-optimized (no GPU required)
- ✅ Production-ready
- ✅ Auto-restart on failure
- ✅ Persistent data
- ✅ Easy scaling

**Quick Commands**:
```bash
# Start
docker-compose -f docker-compose.simple.yml up -d

# Logs
docker-compose -f docker-compose.simple.yml logs -f

# Stop
docker-compose -f docker-compose.simple.yml down

# Test
curl http://localhost:8080/health
```

Your system is ready for production use! 🚀
