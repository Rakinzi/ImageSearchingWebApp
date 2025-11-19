# Docker Setup - Quick Reference

This document provides a quick reference for running the complete Image Search application with Docker.

## What's Included

The Docker setup includes **all services** needed to run the application:

1. **Frontend** (Vue.js + Nginx) - Port 80
2. **Backend** (Flask API) - Port 8080 (internal)
3. **PostgreSQL** (Database) - Port 5432
4. **Redis** (Cache) - Port 6379
5. **RabbitMQ** (Message Broker) - Ports 5672, 15672
6. **Celery Worker** (Background tasks)
7. **Celery Beat** (Scheduled tasks)

## Quick Start

### Option 1: Using the Start Script (Easiest)

**Mac/Linux:**
```bash
./start.sh
```

**Windows:**
```
start.bat
```

The script will:
- Check if Docker is running
- Create `.env` file if needed
- Build and start all services
- Initialize the database
- Show you access URLs

### Option 2: Manual Commands

```bash
# 1. Create environment file
cp .env.example .env

# 2. Start all services
docker-compose up -d --build

# 3. Initialize database (first time only)
docker-compose exec --user root app flask db init
docker-compose exec --user root app flask db migrate -m "Initial migration"
docker-compose exec --user root app flask db upgrade
```

## Access Your Application

Once running, access:

- **Web Application**: http://localhost
- **API Endpoint**: http://localhost/api/
- **Health Check**: http://localhost/health
- **RabbitMQ Dashboard**: http://localhost:15672
  - Username: `admin`
  - Password: `secure_rabbit_password` (from .env)

## How It Works

### Network Architecture

```
User Browser
    ↓
Frontend (Nginx) :80
    ↓
    ├─→ Serves Vue.js app
    └─→ Proxies /api/* → Backend :8080
            ↓
        Flask API
            ↓
        PostgreSQL + Redis + RabbitMQ
            ↓
        Celery Workers (process images)
```

### Key Features

1. **Single Port Access**: Users only need port 80
2. **Automatic API Routing**: Nginx proxies `/api/*` requests to backend
3. **Seamless Integration**: All services linked via Docker network
4. **Data Persistence**: Volumes preserve data across restarts
5. **Health Checks**: Automatic service health monitoring

## Common Commands

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f frontend
docker-compose logs -f app
docker-compose logs -f celery-worker

# Restart services
docker-compose restart

# Stop services (keeps data)
docker-compose down

# Stop and remove all data (⚠️ destructive)
docker-compose down -v

# Check service status
docker-compose ps

# Update after code changes
docker-compose up -d --build
```

## Testing on Mac

The setup works perfectly on Mac with Docker Desktop:

1. Install Docker Desktop for Mac
2. Run `./start.sh`
3. Access http://localhost
4. Done!

## Deploying to Linux Server

The **same files** work on Linux - see `DEPLOYMENT.md` for full details.

## Need More Help?

- Full deployment guide: `DEPLOYMENT.md`
- Development guide: `CLAUDE.md`

---

**Ready to start?** Run `./start.sh` and access http://localhost
