# Image Search Web Application

A modern, AI-powered image search application with face detection and semantic search capabilities.

## 🚀 Quick Start

### Prerequisites

- **Docker & Docker Compose** (recommended)
- **Node.js 16.x+** and npm (for frontend development)
- **Python 3.11** (for backend development)

## 🐳 Docker Setup (Recommended)

### 1. Start the Backend Services

```bash
cd backend

# Start all services (database, redis, rabbitmq, backend, celery workers)
docker-compose -f docker-compose.simple.yml up --build -d
```

### 2. Initialize the Database (First Time Only)

```bash
# Initialize Flask migrations
docker-compose -f docker-compose.simple.yml exec --user root app flask db init

# Create database tables
docker-compose -f docker-compose.simple.yml exec --user root app flask db migrate -m "Initial migration"

# Apply migrations
docker-compose -f docker-compose.simple.yml exec --user root app flask db upgrade
```

### 3. Start the Frontend

```bash
cd ../frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### 4. Access the Application

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8080
- **RabbitMQ Management**: http://localhost:15672 (admin/secure_rabbit_password)

## 🔧 Development Workflow

### Backend Changes

**For code changes (no dependency changes):**
```bash
# Restart just the app container
docker-compose -f docker-compose.simple.yml restart app
```

**For dependency changes:**
```bash
# Rebuild and restart
docker-compose -f docker-compose.simple.yml up --build app
```

### Frontend Changes

Frontend uses Vite with hot-reload - changes are reflected automatically.

### Database Operations

**Create new migration (after model changes):**
```bash
docker-compose -f docker-compose.simple.yml exec --user root app flask db migrate -m "Description of changes"
```

**Apply pending migrations:**
```bash
docker-compose -f docker-compose.simple.yml exec --user root app flask db upgrade
```

**Rollback to previous migration:**
```bash
docker-compose -f docker-compose.simple.yml exec --user root app flask db downgrade
```

**View migration history:**
```bash
docker-compose -f docker-compose.simple.yml exec --user root app flask db history
```

**Check current migration version:**
```bash
docker-compose -f docker-compose.simple.yml exec --user root app flask db current
```

**View logs:**
```bash
docker-compose -f docker-compose.simple.yml logs -f app
docker-compose -f docker-compose.simple.yml logs -f celery-worker
docker-compose -f docker-compose.simple.yml logs -f postgresql
```

**Connect to database:**
```bash
docker-compose -f docker-compose.simple.yml exec postgresql psql -U app_user -d image_search_db
```

**Backup database:**
```bash
docker-compose -f docker-compose.simple.yml exec postgresql pg_dump -U app_user image_search_db > backup.sql
```

**Restore database:**
```bash
docker-compose -f docker-compose.simple.yml exec -T postgresql psql -U app_user -d image_search_db < backup.sql
```

**Reset database (⚠️ deletes all data):**
```bash
# Method 1: Step by step
# Stop services
docker-compose -f docker-compose.simple.yml down

# Remove database volume
docker volume rm backend_postgresql_data

# Start and reinitialize
docker-compose -f docker-compose.simple.yml up --build -d

# Initialize database
docker-compose -f docker-compose.simple.yml exec --user root app flask db init
docker-compose -f docker-compose.simple.yml exec --user root app flask db migrate -m "Fresh start"
docker-compose -f docker-compose.simple.yml exec --user root app flask db upgrade
```

**Complete reset (one-liner):**
```bash
# Method 2: All in one command
docker-compose -f docker-compose.simple.yml down && docker volume rm backend_postgresql_data && docker-compose -f docker-compose.simple.yml up --build -d && docker-compose -f docker-compose.simple.yml exec --user root app flask db init && docker-compose -f docker-compose.simple.yml exec --user root app flask db migrate -m "Fresh start" && docker-compose -f docker-compose.simple.yml exec --user root app flask db upgrade
```

**Nuclear option (removes ALL volumes):**
```bash
# Method 3: Remove all data (database, redis, rabbitmq)
docker-compose -f docker-compose.simple.yml down -v
docker-compose -f docker-compose.simple.yml up --build -d
# Then run database initialization commands above
```

### Container Management

**Restart specific service:**
```bash
docker-compose -f docker-compose.simple.yml restart app
docker-compose -f docker-compose.simple.yml restart celery-worker
docker-compose -f docker-compose.simple.yml restart postgresql
```

**Rebuild and restart service:**
```bash
docker-compose -f docker-compose.simple.yml up --build app
```

**Scale celery workers:**
```bash
docker-compose -f docker-compose.simple.yml up --scale celery-worker=3 -d
```

**Execute commands in containers:**
```bash
# Backend container
docker-compose -f docker-compose.simple.yml exec app bash

# Database container
docker-compose -f docker-compose.simple.yml exec postgresql bash

# Run Flask commands
docker-compose -f docker-compose.simple.yml exec app flask --help
```

## 📁 Project Structure

```
├── backend/                 # Flask API server
│   ├── api/                # REST API endpoints (v1 & v2)
│   ├── models/             # Database models
│   ├── services/           # Business logic
│   ├── tasks/              # Celery background tasks
│   ├── middleware/         # Auth, logging, rate limiting
│   ├── utils/              # Utilities and validators
│   ├── docker-compose.simple.yml  # CPU-only Docker setup
│   ├── Dockerfile.cpu-only         # CPU-optimized Dockerfile
│   └── requirements.txt            # Python dependencies
│
├── frontend/               # Vue.js 3 + Naive UI
│   ├── src/
│   │   ├── components/     # Vue components
│   │   ├── views/          # Page views
│   │   ├── stores/         # Pinia state management
│   │   └── services/       # API service layer
│   ├── package.json
│   └── vite.config.js
│
└── README.md              # This file
```

## 🛠️ Technology Stack

### Backend
- **Framework**: Flask 3.0
- **Database**: PostgreSQL 15
- **Task Queue**: Celery with RabbitMQ
- **Cache**: Redis
- **AI/ML**: CLIP, FaceNet, TensorFlow CPU, ChromaDB
- **Package Manager**: UV (ultra-fast Python package installer)

### Frontend
- **Framework**: Vue.js 3 with Composition API
- **UI Library**: Naive UI (complete component library)
- **Build Tool**: Vite
- **State Management**: Pinia
- **Language**: TypeScript support

## 🔑 Authentication

1. **Register**: Create account at `/register`
2. **Login**: Sign in at `/login`

**Password Requirements**: Minimum 8 characters (simple validation)

## 🖼️ Features

- **Image Upload**: Drag & drop image upload with progress
- **Semantic Search**: AI-powered image search using CLIP
- **Face Detection**: Automatic face detection and clustering
- **Face Search**: Find images containing specific people
- **Modern UI**: Responsive design with dark/light themes
- **Background Processing**: Async image processing with Celery

## 🚨 Troubleshooting

### Permission Errors in Docker

If you get permission errors during database initialization:
```bash
# Use root user for migrations
docker-compose -f docker-compose.simple.yml exec --user root app flask db upgrade
```

### Frontend Can't Connect to Backend

Check that the backend URL is correct:
```bash
# File: frontend/.env.development
VITE_API_URL=http://localhost:8080
```

### Database Connection Issues

Ensure PostgreSQL is healthy:
```bash
docker-compose -f docker-compose.simple.yml ps
```

All services should show "healthy" status.

### Reset Everything

```bash
# Stop all services
docker-compose -f docker-compose.simple.yml down

# Remove all volumes (⚠️ deletes all data)
docker-compose -f docker-compose.simple.yml down -v

# Start fresh
docker-compose -f docker-compose.simple.yml up --build -d

# Reinitialize database (follow steps in section 2 above)
```

## 📊 Monitoring

**Health Check**: http://localhost:8080/health

**Container Status**:
```bash
docker-compose -f docker-compose.simple.yml ps
```

**Resource Usage**:
```bash
docker stats
```

## 🔧 Configuration

### Environment Variables

**Backend** (`.env`):
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `JWT_SECRET_KEY`: JWT signing key
- `TIMEZONE`: Application timezone (default: Africa/Harare)

**Frontend** (`.env.development`):
- `VITE_API_URL`: Backend API URL (default: http://localhost:8080)

### Production Deployment

For production, use the full GPU-enabled setup:
```bash
# Use the main docker-compose.yml instead
docker-compose up --build -d
```

## 💻 Manual Development Setup (Alternative)

If you prefer not to use Docker:

### Backend Setup

1. **Prerequisites**: Python 3.11, RabbitMQ server, PostgreSQL

2. **Install dependencies**:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download en_core_web_lg
```

3. **Initialize database**:
```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

4. **Start services**:
```bash
# Terminal 1: Main server
python main.py

# Terminal 2: Celery worker
celery -A main.celery worker --loglevel=info --pool=solo
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

## 🤝 Contributing

1. Make changes to the code
2. For backend changes, restart the appropriate containers
3. For frontend changes, Vite will auto-reload
4. Test your changes
5. Commit your changes

## 📝 License

This project is for educational/development purposes.