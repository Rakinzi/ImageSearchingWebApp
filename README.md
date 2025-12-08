<div align="center">

# Image Search Web Application

### AI-Powered Image Search with Face Detection & Semantic Search

[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![Vue.js](https://img.shields.io/badge/Vue.js-3.x-4FC08D?logo=vue.js&logoColor=white)](https://vuejs.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0-000000?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![License](https://img.shields.io/badge/License-Educational-green.svg)](LICENSE)

[Features](#-features) • [Quick Start](#-quick-start) • [Tech Stack](#-technology-stack) • [Documentation](#-project-structure)

</div>

---

## 🎯 Overview

A production-ready image search application leveraging state-of-the-art AI models for semantic search and face recognition. Built with modern web technologies and optimized for both CPU and GPU deployments.

### Key Capabilities

- **Semantic Search**: Natural language queries using OpenAI CLIP and OpenCLIP models
- **Face Detection**: Automatic face detection, clustering, and recognition with FaceNet & DeepFace
- **Vector Search**: Efficient similarity search using pgvector and ChromaDB
- **Async Processing**: Background task queue with Celery for scalable image processing
- **Modern UI**: Responsive Vue 3 interface with Tailwind CSS and shadcn-vue components

---

## 🚀 Quick Start

### Prerequisites

- **Docker & Docker Compose** (recommended - simplest setup)
- **Node.js 18.x+** and npm (for frontend development)
- **Python 3.11+** (for backend development without Docker)

## 🐳 Docker Setup (Recommended)

**One-command startup** for the complete stack:

```bash
# 1️⃣ Start backend services (PostgreSQL, Redis, RabbitMQ, Flask, Celery)
cd backend && docker-compose -f docker-compose.simple.yml up --build -d

# 2️⃣ Initialize database (first time only)
docker-compose -f docker-compose.simple.yml exec --user root app flask db init
docker-compose -f docker-compose.simple.yml exec --user root app flask db migrate -m "Initial migration"
docker-compose -f docker-compose.simple.yml exec --user root app flask db upgrade

# 3️⃣ Start frontend
cd ../frontend && npm install && npm run dev
```

### Access Points

| Service | URL | Credentials |
|---------|-----|-------------|
| **Frontend** | http://localhost:5173 | Register new account |
| **Backend API** | http://localhost:8080 | - |
| **API Health** | http://localhost:8080/health | - |
| **RabbitMQ Admin** | http://localhost:15672 | `admin` / `secure_rabbit_password` |

---

## 🔧 Development Workflow

<details>
<summary><b>Backend Development</b></summary>

**Code changes** (no new dependencies):
```bash
docker-compose -f docker-compose.simple.yml restart app
```

**Dependency changes** (requirements.txt modified):
```bash
docker-compose -f docker-compose.simple.yml up --build app
```

**View logs**:
```bash
docker-compose -f docker-compose.simple.yml logs -f app          # Flask app
docker-compose -f docker-compose.simple.yml logs -f celery-worker # Celery
```

</details>

<details>
<summary><b>Frontend Development</b></summary>

Vite provides **instant hot-reload** - changes appear automatically. No restart needed.

```bash
cd frontend
npm run dev          # Development server
npm run build        # Production build
npm run preview      # Preview production build
```

</details>

<details>
<summary><b>Database Operations</b></summary>

### Migrations

```bash
# Create migration after model changes
docker-compose -f docker-compose.simple.yml exec --user root app flask db migrate -m "Description"

# Apply migrations
docker-compose -f docker-compose.simple.yml exec --user root app flask db upgrade

# Rollback
docker-compose -f docker-compose.simple.yml exec --user root app flask db downgrade

# View history
docker-compose -f docker-compose.simple.yml exec --user root app flask db history
```

### Database Management

```bash
# Connect to PostgreSQL
docker-compose -f docker-compose.simple.yml exec postgresql psql -U app_user -d image_search_db

# Backup
docker-compose -f docker-compose.simple.yml exec postgresql pg_dump -U app_user image_search_db > backup.sql

# Restore
docker-compose -f docker-compose.simple.yml exec -T postgresql psql -U app_user -d image_search_db < backup.sql

# Reset database (⚠️ DELETES ALL DATA)
docker-compose -f docker-compose.simple.yml down
docker volume rm backend_postgresql_data
docker-compose -f docker-compose.simple.yml up --build -d
# Then reinitialize (see Quick Start step 2)
```

</details>

<details>
<summary><b>Container Management</b></summary>

```bash
# Restart specific services
docker-compose -f docker-compose.simple.yml restart app
docker-compose -f docker-compose.simple.yml restart celery-worker

# Scale Celery workers
docker-compose -f docker-compose.simple.yml up --scale celery-worker=3 -d

# Execute commands in containers
docker-compose -f docker-compose.simple.yml exec app bash
docker-compose -f docker-compose.simple.yml exec postgresql psql -U app_user -d image_search_db

# Monitor resources
docker stats
```

</details>

---

## 📁 Project Structure

```
ImageSearchingWebApp/
│
├── backend/                           # Flask API Server
│   ├── api/
│   │   ├── v1/                       # REST API v1 endpoints
│   │   └── v2/                       # REST API v2 endpoints
│   ├── models/                       # SQLAlchemy database models
│   ├── services/                     # Business logic layer
│   ├── tasks/                        # Celery async tasks
│   │   ├── image_tasks.py           # Image processing tasks
│   │   ├── face_tasks.py            # Face detection tasks
│   │   └── maintenance_tasks.py      # Scheduled maintenance
│   ├── middleware/                   # Request/response middleware
│   │   ├── auth.py                  # JWT authentication
│   │   ├── rate_limiter.py          # Rate limiting
│   │   └── audit_logger.py          # Request auditing
│   ├── utils/                        # Helper utilities
│   ├── config/                       # App configuration
│   ├── docker-compose.simple.yml     # CPU-optimized Docker setup
│   ├── Dockerfile.cpu-only          # CPU-only image
│   ├── requirements.txt             # Python dependencies
│   └── main.py                      # Application entry point
│
├── frontend/                         # Vue.js 3 Application
│   ├── src/
│   │   ├── components/              # Reusable Vue components
│   │   │   └── ui/                  # shadcn-vue UI components
│   │   ├── views/                   # Page components
│   │   ├── stores/                  # Pinia state stores
│   │   │   ├── authStore.js        # Authentication state
│   │   │   ├── imagesStore.js      # Image management
│   │   │   └── FaceStore.js        # Face detection state
│   │   ├── services/                # API client layer
│   │   ├── router/                  # Vue Router config
│   │   └── main.js                  # App entry point
│   ├── package.json                 # NPM dependencies
│   ├── vite.config.js              # Vite configuration
│   └── tailwind.config.js          # Tailwind CSS config
│
└── README.md                         # You are here
```

## 🛠️ Technology Stack

### Backend

| Category | Technologies |
|----------|-------------|
| **Framework** | Flask 3.0 + Flask-CORS + Flask-SQLAlchemy |
| **Database** | PostgreSQL 15 with pgvector extension |
| **Task Queue** | Celery + RabbitMQ (message broker) |
| **Cache** | Redis (session storage, rate limiting) |
| **Authentication** | JWT (Flask-JWT-Extended) + BCrypt |
| **AI/ML Models** | OpenAI CLIP, OpenCLIP (ViT-L/14), FaceNet, DeepFace |
| **Vector DB** | ChromaDB + pgvector for similarity search |
| **Image Processing** | Pillow, OpenCV, EasyOCR |
| **NLP** | spaCy, NLTK, Sentence Transformers |
| **ML Frameworks** | PyTorch, TensorFlow/Keras, scikit-learn |
| **Server** | Gunicorn with Eventlet workers |

### Frontend

| Category | Technologies |
|----------|-------------|
| **Framework** | Vue.js 3 (Composition API) |
| **UI Components** | shadcn-vue, Reka UI, Lucide icons |
| **Styling** | Tailwind CSS 4.x, Tailwind Merge |
| **Build Tool** | Vite 5.x |
| **State Management** | Pinia 2.x |
| **HTTP Client** | Axios |
| **Utilities** | VueUse, Day.js, Vue Sonner (toasts) |
| **Type Safety** | TypeScript support |

### Infrastructure

| Service | Purpose |
|---------|---------|
| **Docker Compose** | Multi-container orchestration |
| **PostgreSQL 15** | Primary database with vector extension |
| **Redis** | Caching, session storage, Celery results |
| **RabbitMQ** | Message broker for async tasks |
| **Celery Beat** | Scheduled task execution |

---

## 🖼️ Features

### Core Functionality

| Feature | Description |
|---------|-------------|
| **Semantic Search** | Natural language image search powered by CLIP - search using descriptions like "sunset over mountains" or "person wearing red shirt" |
| **Face Detection** | Automatic face detection in uploaded images using FaceNet and DeepFace models |
| **Face Clustering** | Group similar faces together for organization and quick retrieval |
| **Face Search** | Find all images containing a specific person |
| **Vector Similarity** | Efficient nearest-neighbor search using pgvector and ChromaDB |
| **Batch Upload** | Upload multiple images simultaneously with progress tracking |
| **Background Processing** | All heavy AI operations run asynchronously via Celery |

### User Experience

- **Modern UI**: Clean, responsive interface built with Vue 3 and Tailwind CSS
- **Image Lightbox**: Full-screen image viewing with vue-easy-lightbox
- **Real-time Updates**: Live upload progress and processing status
- **Dark/Light Themes**: System-aware theme switching
- **Drag & Drop**: Intuitive file upload interface
- **Toast Notifications**: User-friendly feedback with Vue Sonner

### Security & Performance

- **JWT Authentication**: Secure token-based auth with refresh tokens
- **Rate Limiting**: Per-user and per-endpoint rate limits
- **Audit Logging**: Comprehensive request/response logging
- **Input Validation**: Server-side validation with bleach and email-validator
- **CORS Protection**: Configurable cross-origin resource sharing
- **Session Management**: Redis-backed session storage

---

## 🚨 Troubleshooting

<details>
<summary><b>Permission errors during database migrations</b></summary>

Use `--user root` flag:
```bash
docker-compose -f docker-compose.simple.yml exec --user root app flask db upgrade
```

</details>

<details>
<summary><b>Frontend can't connect to backend</b></summary>

Verify backend URL in `frontend/.env.development`:
```env
VITE_API_URL=http://localhost:8080
```

Check backend is running:
```bash
curl http://localhost:8080/health
```

</details>

<details>
<summary><b>Database connection refused</b></summary>

Check service health:
```bash
docker-compose -f docker-compose.simple.yml ps
```

All services should show **healthy** status. If not:
```bash
docker-compose -f docker-compose.simple.yml logs postgresql
```

</details>

<details>
<summary><b>Celery tasks not processing</b></summary>

Check Celery worker logs:
```bash
docker-compose -f docker-compose.simple.yml logs -f celery-worker
```

Verify RabbitMQ connection:
```bash
docker-compose -f docker-compose.simple.yml logs rabbitmq
```

</details>

<details>
<summary><b>AI models downloading slowly</b></summary>

First run downloads ~1.7GB of AI models (CLIP ViT-L/14). This is cached for future use.

Monitor download progress:
```bash
docker-compose -f docker-compose.simple.yml logs -f celery-worker
```

</details>

<details>
<summary><b>Complete reset (nuclear option)</b></summary>

**WARNING: Deletes all data, images, and databases**

```bash
# Stop everything and remove all data
docker-compose -f docker-compose.simple.yml down -v

# Fresh start
docker-compose -f docker-compose.simple.yml up --build -d

# Reinitialize database
docker-compose -f docker-compose.simple.yml exec --user root app flask db init
docker-compose -f docker-compose.simple.yml exec --user root app flask db migrate -m "Fresh start"
docker-compose -f docker-compose.simple.yml exec --user root app flask db upgrade
```

</details>

---

## 📊 Monitoring & Health

| Endpoint | Purpose |
|----------|---------|
| `http://localhost:8080/health` | Backend health check |
| `http://localhost:15672` | RabbitMQ management UI |

**Container status:**
```bash
docker-compose -f docker-compose.simple.yml ps
```

**Resource monitoring:**
```bash
docker stats
```

**View all logs:**
```bash
docker-compose -f docker-compose.simple.yml logs -f
```

---

## ⚙️ Configuration

### Environment Variables

<details>
<summary><b>Backend Configuration</b> (<code>.env</code>)</summary>

```bash
# Database
DATABASE_URL=postgresql://app_user:password@localhost:5432/image_search_db
POSTGRES_USER=app_user
POSTGRES_PASSWORD=secure_app_password
POSTGRES_DB=image_search_db

# Redis & Celery
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=pyamqp://admin:secure_rabbit_password@localhost:5672//
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# RabbitMQ
RABBITMQ_USER=admin
RABBITMQ_PASSWORD=secure_rabbit_password

# Security
JWT_SECRET_KEY=your-super-secret-jwt-key-change-this
RATE_LIMIT_STORAGE_URL=redis://localhost:6379/2

# Application
FLASK_ENV=production
TIMEZONE=Africa/Harare
```

</details>

<details>
<summary><b>Frontend Configuration</b> (<code>.env.development</code>)</summary>

```bash
# API endpoint
VITE_API_URL=http://localhost:8080
```

</details>

### Production Deployment

For GPU-accelerated inference:
```bash
# Use the GPU-enabled Docker Compose configuration
cd backend
docker-compose up --build -d
```

---

## 💻 Manual Setup (Without Docker)

<details>
<summary><b>Expand for non-Docker installation</b></summary>

### Requirements
- Python 3.11+
- PostgreSQL 15 with pgvector
- Redis server
- RabbitMQ server
- Node.js 18+

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
python -m spacy download en_core_web_lg

# Configure environment
cp .env.example .env
# Edit .env with your database credentials

# Initialize database
flask db init
flask db migrate -m "Initial migration"
flask db upgrade

# Start services (separate terminals)
python main.py                                              # Terminal 1: Flask
celery -A main.celery worker --loglevel=info --pool=solo   # Terminal 2: Celery worker
celery -A main.celery beat --loglevel=info                 # Terminal 3: Celery beat
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

</details>

---

## 🤝 Contributing

Contributions welcome! Please follow these guidelines:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Test** your changes thoroughly
4. **Commit** with clear messages (`git commit -m 'Add amazing feature'`)
5. **Push** to your branch (`git push origin feature/amazing-feature`)
6. **Open** a Pull Request

### Development Guidelines

- Backend changes: Restart containers with `docker-compose restart app`
- Frontend changes: Auto-reload via Vite (no restart needed)
- Database changes: Create migrations with `flask db migrate`
- Run tests before submitting PRs

---

## 📄 License

This project is for **educational and development purposes**.

---

## 🙏 Acknowledgments

Built with amazing open-source technologies:

- **[OpenAI CLIP](https://github.com/openai/CLIP)** - Connecting text and images
- **[OpenCLIP](https://github.com/mlfoundations/open_clip)** - Open-source CLIP implementation
- **[Vue.js](https://vuejs.org/)** - Progressive JavaScript framework
- **[Flask](https://flask.palletsprojects.com/)** - Python web framework
- **[shadcn-vue](https://www.shadcn-vue.com/)** - Beautifully designed components
- **[Tailwind CSS](https://tailwindcss.com/)** - Utility-first CSS framework

---

<div align="center">

**Made with dedication and attention to detail**

⭐ Star this repo if you find it useful!

</div>