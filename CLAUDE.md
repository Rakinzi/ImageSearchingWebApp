# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Frontend (Vue.js 3 + Vite + shadcn-vue)
```bash
cd frontend
npm install       # Install dependencies
npm run dev       # Start development server (http://localhost:5173)
npm run build     # Build for production
npm run preview   # Preview production build
npm run type-check # Type checking with Vue TSC
```

### Backend (Flask + Python)

#### Docker Setup (Recommended)
```bash
cd backend

# Start all services (PostgreSQL, Redis, RabbitMQ, Flask app, Celery worker)
docker-compose -f docker-compose.simple.yml up --build -d

# Initialize database (first time only)
docker-compose -f docker-compose.simple.yml exec --user root app flask db init
docker-compose -f docker-compose.simple.yml exec --user root app flask db migrate -m "Initial migration"
docker-compose -f docker-compose.simple.yml exec --user root app flask db upgrade

# View logs
docker-compose -f docker-compose.simple.yml logs -f app
docker-compose -f docker-compose.simple.yml logs -f celery-worker

# Restart services after code changes (no dependency changes)
docker-compose -f docker-compose.simple.yml restart app

# Rebuild after dependency changes
docker-compose -f docker-compose.simple.yml up --build app

# Database migrations
docker-compose -f docker-compose.simple.yml exec --user root app flask db migrate -m "Description"
docker-compose -f docker-compose.simple.yml exec --user root app flask db upgrade
docker-compose -f docker-compose.simple.yml exec --user root app flask db downgrade
docker-compose -f docker-compose.simple.yml exec --user root app flask db history

# Reset database (⚠️ deletes all data)
docker-compose -f docker-compose.simple.yml down && \
docker volume rm backend_postgresql_data && \
docker-compose -f docker-compose.simple.yml up --build -d && \
docker-compose -f docker-compose.simple.yml exec --user root app flask db init && \
docker-compose -f docker-compose.simple.yml exec --user root app flask db migrate -m "Fresh start" && \
docker-compose -f docker-compose.simple.yml exec --user root app flask db upgrade
```

#### Manual Setup (Alternative)
```bash
cd backend

# Environment setup (required first time)
python -m venv venv
source venv/bin/activate  # Linux/MacOS
# OR
venv\Scripts\activate     # Windows

pip install -r requirements.txt
python -m spacy download en_core_web_lg

# Database initialization (required first time)
flask db init
flask db migrate -m "Initial migration"
flask db upgrade

# Start services in separate terminals
python main.py              # Main Flask server (port 8080)
celery -A main.celery worker --loglevel=info --pool=solo  # Task worker
```

#### Testing ML Features
```bash
cd backend

# Test image embeddings with CLIP
python utils/test_embeddings.py

# Test face detection
python utils/test_face_detection.py

# Test OCR functionality
python utils/test_ocr.py

# Migrate embeddings between models
python utils/migrate_embeddings.py
```

### Prerequisites
- **Docker & Docker Compose** (recommended)
- **Python 3.11** (required for backend)
- **Node.js 16.x+** and npm (for frontend)
- **RabbitMQ** (for Celery, included in Docker setup)
- **PostgreSQL 15** (included in Docker setup)
- **Redis** (for caching, included in Docker setup)

## Architecture Overview

This is an **Image Search Web Application** with separate frontend and backend services:

### Backend Architecture
- **Framework**: Flask 3.0 with modular blueprint structure
- **API**: RESTful API with two versions
  - `/api/v1/` - Legacy endpoints (backward compatibility)
  - `/api/v2/` - Modern endpoints with enhanced features and type safety
- **Database**: PostgreSQL 15 with SQLAlchemy ORM and Flask-Migrate for schema management
- **Authentication**: JWT-based auth with Flask-JWT-Extended
- **Task Queue**: Celery with RabbitMQ for background image processing
- **Cache**: Redis for session management and caching
- **AI/ML Stack**:
  - OpenAI CLIP for image embeddings and semantic search
  - FaceNet (facenet-pytorch) and DeepFace for face recognition
  - spaCy (en_core_web_lg) and sentence-transformers for NLP processing
  - ChromaDB for vector database and similarity search
  - TensorFlow CPU for ML operations
  - OCR capabilities for text extraction from images
- **Key Directories**:
  - `api/` - REST API endpoints organized by version (v1, v2)
  - `models/` - SQLAlchemy database models (both legacy and modern)
  - `services/` - Business logic and AI processing services
  - `tasks/` - Celery background tasks for image/face processing
  - `middleware/` - Auth, rate limiting, audit logging, security headers
  - `config/` - Configuration management (settings.py, modern_settings.py)
  - `utils/` - Utilities, validators, testing scripts, and helpers

### Backend API Versions
- **v1 API**: Original endpoints for backward compatibility
- **v2 API**: Modern API with:
  - Pydantic validation for request/response models
  - Comprehensive error handling with structured responses
  - Type hints throughout
  - Enhanced search capabilities (semantic, text, metadata, hybrid)
  - Better status tracking for async operations

### Frontend Architecture
- **Framework**: Vue.js 3 with Composition API
- **UI Library**: **shadcn-vue** (NOT Naive UI) - Modern component library built on:
  - Reka UI (headless UI primitives)
  - Tailwind CSS 4.x for styling
  - Lucide icons (lucide-vue-next)
- **Build Tool**: Vite 5 for fast development and building
- **State Management**: Pinia stores
  - `authStore` - Authentication and user session
  - `imagesStore` - Image gallery and search
  - `FaceStore` - Face detection and clustering
- **Routing**: Vue Router for SPA navigation
- **TypeScript**: Full TypeScript support with vue-tsc type checking
- **Key Features**:
  - Component-based architecture using shadcn-vue components
  - Built-in dark/light theme support via Tailwind CSS variables
  - Responsive design with Tailwind grid system
  - Advanced form validation and file upload
  - All UI styling via Tailwind CSS utility classes

### Component Structure (shadcn-vue)
All UI components are in `frontend/src/components/ui/`:
- Button, Input, Card, Badge
- Dialog, Sheet, Dropdown Menu
- Alert, Checkbox, Label, Separator
- Configured via `components.json` with "new-york" style
- Add new components: `npx shadcn-vue@latest add <component-name>`

### Communication
- Frontend communicates with backend via REST API calls
- Backend processes images asynchronously using Celery workers
- Real-time updates handled through standard HTTP polling
- API base URL: `http://localhost:8080` (configurable via VITE_API_URL)

## Key Technical Details

### Backend
- **GPU Support**: Includes both GPU and CPU-only configurations for ML models
  - `docker-compose.simple.yml` - CPU-only (recommended for most setups)
  - `docker-compose.yml` - GPU-enabled (requires NVIDIA Docker runtime)
- **Security**: Rate limiting, CORS, security headers, audit logging, JWT validation
- **Monitoring**:
  - Health check: `GET /health` (component status)
  - Metrics: `GET /metrics` (Prometheus format)
- **Image Processing**: EXIF data extraction, geolocation, ML-based analysis, semantic search
- **Database Migrations**: Flask-Migrate for schema versioning and changes
- **Type Safety**: Pydantic models for v2 API with runtime validation
- **Configuration**: Environment-specific settings with validation
- **Package Manager**: UV (ultra-fast Python package installer) in Docker setup

### Frontend
- **Styling System**: Tailwind CSS 4.x with custom design tokens
- **CSS Variables**: Theme colors defined in `src/style.css` (`:root` and `.dark`)
- **Icon Library**: Lucide icons via `lucide-vue-next`
- **File Uploads**: Drag-and-drop with progress tracking
- **Authentication**: JWT token stored in authStore, included in API requests
- **Environment Variables**: Configure API URL via `.env.development`

### Development Workflow
1. **Start backend**: Run Docker Compose or manual Flask + Celery setup
2. **Start frontend**: Run `npm run dev` in frontend directory
3. **Hot reload**: Frontend auto-reloads on changes, backend requires restart
4. **Database changes**: Create migration → Apply migration → Restart app
5. **Testing ML features**: Use test scripts in `backend/utils/` directory

### Access Points
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8080
- **API Docs**: http://localhost:8080/api/v2/docs (OpenAPI/Swagger)
- **Health Check**: http://localhost:8080/health
- **RabbitMQ Management**: http://localhost:15672 (admin/secure_rabbit_password)

### Common Issues
- **Permission errors in Docker**: Use `--user root` for flask db commands
- **Frontend can't connect**: Check `VITE_API_URL` in frontend `.env.development`
- **Database connection**: Verify PostgreSQL is healthy with `docker-compose ps`
- **Image processing stuck**: Check Celery worker logs for errors
