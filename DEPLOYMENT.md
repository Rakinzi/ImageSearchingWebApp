# Deployment Guide - Image Search Web Application

This guide covers deploying the complete application stack (frontend + backend) using Docker Compose on both Mac (for testing) and Linux (for production).

## Overview

The application consists of:
- **Frontend**: Vue.js 3 with Nginx (Port 80)
- **Backend API**: Flask application (Port 8080)
- **PostgreSQL**: Database with pgvector extension (Port 5432)
- **Redis**: Cache and session storage (Port 6379)
- **RabbitMQ**: Message broker for async tasks (Ports 5672, 15672)
- **Celery Worker**: Background image processing
- **Celery Beat**: Scheduled tasks

All services are linked via Docker networking and communicate seamlessly.

## Prerequisites

### For Mac (Testing)
- Docker Desktop for Mac (4.0+)
- Docker Compose (included with Docker Desktop)
- 8GB+ RAM available for Docker
- 20GB+ free disk space

### For Linux Server (Production)
- Docker Engine (20.10+)
- Docker Compose (2.0+)
- Ubuntu 20.04+ / Debian 11+ / CentOS 8+ (recommended)
- 8GB+ RAM
- 50GB+ free disk space
- Open ports: 80 (HTTP), 443 (HTTPS - optional)

## Quick Start

### 1. Clone the Repository
```bash
git clone <your-repo-url>
cd ImageSearchingWebApp-master
```

### 2. Configure Environment Variables
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and update the values (especially for production!)
nano .env  # or use your preferred editor
```

**IMPORTANT FOR PRODUCTION**: Change these values in `.env`:
- `POSTGRES_PASSWORD`: Use a strong random password
- `RABBITMQ_PASSWORD`: Use a strong random password
- `JWT_SECRET_KEY`: Generate with `python -c "import secrets; print(secrets.token_hex(32))"`

### 3. Start All Services
```bash
# Build and start all services
docker-compose up -d --build

# Check service status
docker-compose ps

# View logs
docker-compose logs -f
```

### 4. Initialize the Database
```bash
# Run database migrations (first time only)
docker-compose exec --user root app flask db init
docker-compose exec --user root app flask db migrate -m "Initial migration"
docker-compose exec --user root app flask db upgrade
```

### 5. Access the Application
- **Frontend (Web UI)**: http://localhost
- **Backend API**: http://localhost/api/ (proxied through nginx)
- **Direct Backend**: http://localhost:8080 (for development)
- **RabbitMQ Management**: http://localhost:15672 (admin/secure_rabbit_password)
- **Health Check**: http://localhost/health

## Architecture Details

### Nginx Reverse Proxy
The frontend nginx server proxies API requests to the backend:
- `http://localhost/` → Frontend (Vue.js SPA)
- `http://localhost/api/*` → Backend Flask API
- `http://localhost/health` → Backend health check
- `http://localhost/metrics` → Backend metrics

This means users only need to access port 80, and all API requests are automatically routed to the backend.

### Docker Networking
All services communicate via the `app_network` bridge network:
- Frontend → Backend: `http://app:8080`
- Backend → PostgreSQL: `postgresql:5432`
- Backend → Redis: `redis:6379`
- Backend → RabbitMQ: `rabbitmq:5672`

### Data Persistence
Docker volumes ensure data persists across container restarts:
- `postgresql_data`: Database files
- `redis_data`: Redis persistence
- `rabbitmq_data`: RabbitMQ data
- `./backend/static`: Uploaded images
- `./backend/chroma_db`: Vector database
- `./backend/logs`: Application logs
- `./backend/model_cache`: AI model cache
- `./backend/deepface_models`: Face recognition models

## Common Operations

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f frontend
docker-compose logs -f app
docker-compose logs -f celery-worker

# Last 100 lines
docker-compose logs --tail=100 app
```

### Restart Services
```bash
# Restart specific service
docker-compose restart frontend
docker-compose restart app

# Restart all services
docker-compose restart
```

### Stop Services
```bash
# Stop all services
docker-compose stop

# Stop and remove containers (data persists in volumes)
docker-compose down

# Stop and remove everything including volumes (⚠️ deletes all data)
docker-compose down -v
```

### Update After Code Changes
```bash
# Frontend changes
docker-compose up -d --build frontend

# Backend changes
docker-compose up -d --build app celery-worker celery-beat

# All changes
docker-compose up -d --build
```

### Database Operations
```bash
# Create new migration
docker-compose exec --user root app flask db migrate -m "Description of changes"

# Apply migrations
docker-compose exec --user root app flask db upgrade

# Rollback migration
docker-compose exec --user root app flask db downgrade

# View migration history
docker-compose exec --user root app flask db history

# Access PostgreSQL shell
docker-compose exec postgresql psql -U app_user -d image_search_db
```

### Backup and Restore

#### Backup Database
```bash
# Create backup
docker-compose exec postgresql pg_dump -U app_user image_search_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Backup with compression
docker-compose exec postgresql pg_dump -U app_user image_search_db | gzip > backup_$(date +%Y%m%d_%H%M%S).sql.gz
```

#### Restore Database
```bash
# Restore from backup
cat backup_20250119_120000.sql | docker-compose exec -T postgresql psql -U app_user image_search_db

# Restore from compressed backup
gunzip -c backup_20250119_120000.sql.gz | docker-compose exec -T postgresql psql -U app_user image_search_db
```

#### Backup Uploaded Images
```bash
# Backup images and vector database
tar -czf images_backup_$(date +%Y%m%d_%H%M%S).tar.gz \
    backend/static \
    backend/chroma_db
```

## Production Deployment on Linux Server

### 1. Server Preparation
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

### 2. Firewall Configuration
```bash
# Allow HTTP traffic
sudo ufw allow 80/tcp

# Allow HTTPS (if using SSL)
sudo ufw allow 443/tcp

# Enable firewall
sudo ufw enable
```

### 3. Deploy Application
```bash
# Clone repository
git clone <your-repo-url>
cd ImageSearchingWebApp-master

# Configure environment
cp .env.example .env
nano .env  # Update production values

# Start services
docker-compose up -d --build

# Initialize database
docker-compose exec --user root app flask db init
docker-compose exec --user root app flask db migrate -m "Initial migration"
docker-compose exec --user root app flask db upgrade

# Verify all services are healthy
docker-compose ps
```

### 4. SSL/HTTPS Setup (Optional but Recommended)

For production, add SSL using Let's Encrypt:

1. Install Certbot:
```bash
sudo apt install certbot python3-certbot-nginx -y
```

2. Update nginx configuration to use your domain

3. Get SSL certificate:
```bash
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

### 5. Set Up Automatic Startup
```bash
# Create systemd service
sudo nano /etc/systemd/system/image-search-app.service
```

Add:
```ini
[Unit]
Description=Image Search Application
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/path/to/ImageSearchingWebApp-master
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
```

Enable:
```bash
sudo systemctl daemon-reload
sudo systemctl enable image-search-app
sudo systemctl start image-search-app
```

## Monitoring and Maintenance

### Health Checks
```bash
# Check service health
curl http://localhost/health

# Check all container status
docker-compose ps

# Check resource usage
docker stats
```

### Log Rotation
Application logs are stored in `backend/logs/`. Set up log rotation:

```bash
sudo nano /etc/logrotate.d/image-search-app
```

Add:
```
/path/to/ImageSearchingWebApp-master/backend/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    missingok
    create 0644 root root
}
```

### Regular Maintenance
```bash
# Clean up unused Docker resources
docker system prune -a --volumes -f

# Update application
git pull
docker-compose up -d --build

# Backup database (daily recommended)
docker-compose exec postgresql pg_dump -U app_user image_search_db | gzip > backup_$(date +%Y%m%d).sql.gz
```

## Troubleshooting

### Services Won't Start
```bash
# Check logs
docker-compose logs

# Check disk space
df -h

# Check Docker resources
docker system df

# Verify ports are available
sudo netstat -tlnp | grep -E ':(80|8080|5432|6379|5672)'
```

### Database Connection Issues
```bash
# Verify PostgreSQL is healthy
docker-compose exec postgresql pg_isready -U app_user

# Check database logs
docker-compose logs postgresql

# Restart database
docker-compose restart postgresql
```

### Frontend Can't Reach Backend
```bash
# Check nginx logs
docker-compose logs frontend

# Verify backend is running
curl http://localhost:8080/health

# Check network connectivity
docker-compose exec frontend ping app
```

### Celery Worker Issues
```bash
# Check worker logs
docker-compose logs celery-worker

# Restart worker
docker-compose restart celery-worker

# Check RabbitMQ
docker-compose logs rabbitmq
```

### Model Download Issues
The first time you upload images, CLIP models (~1.7GB) will be downloaded. This may take time depending on your internet connection. Monitor with:
```bash
docker-compose logs -f celery-worker
```

## Performance Tuning

### For Production
Edit `docker-compose.yml`:

```yaml
# Increase Celery workers for faster processing
celery-worker:
  command:
    - celery -A app.celery worker --loglevel=info --pool=solo --concurrency=2 --max-tasks-per-child=1
```

### Resource Limits
Add to each service in `docker-compose.yml`:
```yaml
deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: 4G
    reservations:
      cpus: '1.0'
      memory: 2G
```

## Security Checklist

- [ ] Change all default passwords in `.env`
- [ ] Generate strong JWT secret key
- [ ] Enable firewall and only open required ports
- [ ] Set up SSL/HTTPS for production
- [ ] Regularly update Docker images: `docker-compose pull && docker-compose up -d`
- [ ] Set up automated backups
- [ ] Monitor logs for suspicious activity
- [ ] Keep system packages updated
- [ ] Use non-root users where possible
- [ ] Restrict RabbitMQ management interface (port 15672) to localhost only

## Support

For issues or questions:
1. Check the logs: `docker-compose logs -f`
2. Review this documentation
3. Check the main README.md and CLAUDE.md files
4. Verify all prerequisites are met
5. Ensure `.env` is properly configured

---

**Last Updated**: 2025-11-19
**Docker Compose Version**: 3.8
**Tested On**: macOS (Docker Desktop), Ubuntu 22.04, Debian 12
