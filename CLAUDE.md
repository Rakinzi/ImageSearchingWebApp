# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Frontend (Vue.js + Vite + Naive UI)
```bash
cd frontend
npm install       # Install dependencies (Naive UI, icons, etc.)
npm run dev       # Start development server
npm run build     # Build for production
npm run preview   # Preview production build
npm run type-check # Type checking with Vue TSC
```

### Backend (Flask + Python)
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

# Start services
python main.py              # Main Flask server (port 8080)
celery -A main.celery worker --loglevel=info --pool=solo  # Task worker
```

### Docker Deployment
```bash
cd backend

# CPU-only version (recommended for most setups)
docker-compose -f docker-compose.simple.yml up -d

# GPU version (requires NVIDIA Docker runtime)
docker-compose up -d

# View logs
docker-compose logs -f app
docker-compose logs -f celery-worker
```

**Prerequisites:**
- Python 3.11 (required for backend)
- Node.js 16.x+ and npm (for frontend)
- RabbitMQ server (for Celery task queue)
- CMake (Windows only)

## Frontend Upgrade (v2)

The frontend has been completely modernized with Naive UI:

### Modern Frontend Features
- **Component Library**: Naive UI - stable, well-maintained Vue 3 component library
- **Zero Custom Components**: All UI elements use Naive UI components exclusively
- **TypeScript Support**: Full TypeScript integration with Vue TSC
- **Modern Dependencies**: Removed legacy packages (Tailwind, Dropzone, Vuex, etc.)
- **Clean Architecture**: Simplified structure using only proven, stable libraries

### Key Changes
- **Replaced**: TailwindCSS → Naive UI styling system
- **Replaced**: Custom components → Naive UI components only
- **Replaced**: Moment.js → Day.js (lighter alternative)
- **Replaced**: Vuex → Pinia (already in use)
- **Removed**: All custom styling and CSS files
- **Added**: TypeScript support and type checking
- **Added**: Modern icon system (@vicons)

### Component Structure
- **App.vue**: Main layout using Naive UI layout components
- **UploadComponent.vue**: File upload using n-upload with drag-and-drop
- **Views**: All views use only Naive UI components
- **No Custom Components**: Everything uses stable, documented Naive UI components

## Architecture Overview

This is an **Image Search Web Application** with separate frontend and backend services:

### Backend Architecture
- **Framework**: Flask with modular blueprint structure
- **API**: RESTful API under `/api/v1` prefix
- **Database**: SQLAlchemy ORM with Flask-Migrate for schema management
- **Authentication**: JWT-based auth with Flask-JWT-Extended
- **Task Queue**: Celery with RabbitMQ for background image processing
- **AI/ML Stack**:
  - OpenAI CLIP for image embeddings
  - Face recognition (facenet-pytorch, deepface)
  - NLP processing (spacy, sentence-transformers)
  - Vector database (ChromaDB)
- **Key Directories**:
  - `api/` - REST API endpoints organized by version
  - `models/` - SQLAlchemy database models
  - `services/` - Business logic and AI processing services
  - `tasks/` - Celery background tasks for image/face processing
  - `middleware/` - Auth, rate limiting, audit logging
  - `config/` - Configuration management

### Frontend Architecture
- **Framework**: Vue.js 3 with Composition API and TypeScript support
- **UI Library**: Naive UI (stable component library similar to shadcn for React)
- **Build Tool**: Vite for fast development and building
- **State Management**: Pinia stores (authStore, FaceStore, etc.)
- **Routing**: Vue Router for SPA navigation
- **Icons**: @vicons/ionicons5 and @vicons/tabler
- **Key Features**:
  - Modern component-only architecture using Naive UI
  - Built-in dark/light theme support
  - Responsive design with grid system
  - Advanced form validation and file upload
  - No custom CSS needed - all styling handled by Naive UI

### Communication
- Frontend communicates with backend via REST API calls
- Backend processes images asynchronously using Celery workers
- Real-time updates handled through standard HTTP polling

## Backend Upgrade (v2)

The backend has been modernized with enhanced patterns and functionality:

### Modern Architecture Features
- **Type Safety**: Full type hints and Pydantic validation
- **Modern API Patterns**: Structured responses, comprehensive error handling
- **Enhanced Models**: Modern SQLAlchemy patterns with hybrid properties and validation
- **Advanced Search**: Semantic, text, metadata, and hybrid search capabilities
- **Async Processing**: Background task processing with comprehensive status tracking

### API Versions
- **v1 API**: Original endpoints at `/api/v1/` (legacy compatibility)
- **v2 API**: Modern endpoints at `/api/v2/` with enhanced features

### Configuration
- **Legacy Config**: `config/settings.py` (original configuration)
- **Modern Config**: `config/modern_settings.py` (Pydantic-based with validation)

### Models
- **Legacy Models**: Original models in `models/` directory
- **Modern Models**: Enhanced models like `models/modern_image.py` with type safety

### Services
- **Enhanced Services**: `services/modern_image_service.py` with advanced functionality
- **Response Utilities**: `utils/responses.py` for consistent API responses

## Key Technical Details

- **GPU Support**: Backend includes both GPU and CPU-only configurations for ML models
- **Security**: Rate limiting, CORS, security headers, audit logging, enhanced error handling
- **Monitoring**: Health check endpoint (`/health`) with component status and Prometheus metrics (`/metrics`)
- **Image Processing**: Supports EXIF data extraction, geolocation, ML-based analysis, and semantic search
- **Development vs Production**: Environment-specific configurations with validation
- **Type Safety**: Comprehensive type hints and runtime validation
- **API Documentation**: Auto-generated OpenAPI/Swagger documentation for both API versions