# Image Search Backend API

A production-ready Flask backend for AI-powered image search and face detection, built with modern security practices and horizontal scaling capabilities.

## 🚀 Features

- **AI-Powered Search**: CLIP-based semantic image search
- **Face Detection**: Automatic face detection and clustering using MTCNN and FaceNet
- **Vector Database**: ChromaDB for efficient similarity search with Pinecone option
- **Security First**: JWT authentication, rate limiting, audit logging, OWASP Top 10 compliance  
- **Scalable Architecture**: Docker containers with GPU/CPU fallback
- **Background Processing**: Celery task queue for async operations
- **Real-time Processing**: Automatic face detection and image processing
- **Admin Dashboard**: Comprehensive admin tools and monitoring
- **Email Integration**: Automated email notifications
- **OpenAPI Documentation**: Auto-generated API docs

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Nginx Proxy   │────│  Flask App      │────│   Celery        │
│   Rate Limiting │    │   JWT Auth      │    │   Background    │
│   SSL/Security  │    │   API v1        │    │   Processing    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐             │
         │              │     MySQL       │             │
         └──────────────│   User/Metadata │─────────────┘
                        │   Audit Logs    │
                        └─────────────────┘
                                 │
                    ┌─────────────────┐    ┌─────────────────┐
                    │    ChromaDB     │    │     Redis       │
                    │ Vector Storage  │    │  Cache/Session  │
                    │  Face/Image     │    │  Rate Limiting  │
                    └─────────────────┘    └─────────────────┘
```

## 📋 Prerequisites

- **Docker & Docker Compose** (recommended)
- **Python 3.9+** (for local development)
- **GPU Support** (optional, NVIDIA Docker for GPU acceleration)
- **16GB+ RAM** (recommended for processing)
- **MySQL 8.0+**
- **Redis 6.0+**

## 🐳 Quick Start with Docker (Recommended)

### 1. Clone and Setup
```bash
git clone <repository-url>
cd backend
cp .env.example .env
```

### 2. Configure Environment Variables
Edit `.env` file with your settings:
```bash
# Database
MYSQL_ROOT_PASSWORD=secure_root_password
MYSQL_DATABASE=image_search_db
MYSQL_USER=app_user
MYSQL_PASSWORD=secure_app_password

# JWT
JWT_SECRET_KEY=your-super-secret-jwt-key-change-this-in-production

# Email (Optional)
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password

# Vector Database
VECTOR_DB_TYPE=chromadb
# PINECONE_API_KEY=your-pinecone-key  # Optional
```

### 3. Start Services
```bash
# With GPU support (recommended)
docker-compose up --build

# CPU only
docker-compose -f docker-compose.cpu.yml up --build
```

### 4. Initialize Database
```bash
# Run migrations
docker-compose exec app flask db upgrade

# Create admin user (optional)
docker-compose exec app python scripts/create_admin.py
```

### 5. Access Services
- **API**: http://localhost:5000
- **API Documentation**: http://localhost:5000/api/v1/docs
- **RabbitMQ Management**: http://localhost:15672 (admin/secure_rabbit_password)
- **Health Check**: http://localhost:5000/health

## 🛠️ Local Development Setup

### 1. Python Environment
```bash
# Install Python 3.9+
python3.9 -m venv venv

# Windows
venv\Scripts\activate

# Linux/MacOS  
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# For CPU-only development
pip install -r requirements-cpu.txt
```

### 2. System Dependencies

#### Windows
- Install [CMake](https://cmake.org/download/)
- Install [Visual Studio Build Tools](https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022)

#### Linux (Ubuntu/Debian)
```bash
sudo apt-get update
sudo apt-get install -y build-essential cmake pkg-config libhdf5-dev \
    libopencv-dev libgtk-3-dev libboost-all-dev python3.9-dev \
    mysql-client libmysqlclient-dev
```

#### macOS
```bash
brew install cmake opencv boost hdf5 mysql-client
```

### 3. Database Setup
```bash
# Install and start MySQL
# Ubuntu/Debian
sudo apt-get install mysql-server
sudo systemctl start mysql

# macOS
brew install mysql
brew services start mysql

# Create database
mysql -u root -p
CREATE DATABASE image_search_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'app_user'@'localhost' IDENTIFIED BY 'secure_app_password';
GRANT ALL PRIVILEGES ON image_search_db.* TO 'app_user'@'localhost';
FLUSH PRIVILEGES;
```

### 4. Redis Setup
```bash
# Ubuntu/Debian
sudo apt-get install redis-server
sudo systemctl start redis

# macOS
brew install redis
brew services start redis

# Windows
# Download from https://github.com/microsoftarchive/redis/releases
```

### 5. RabbitMQ Setup
```bash
# Ubuntu/Debian
sudo apt-get install rabbitmq-server
sudo systemctl start rabbitmq-server
sudo rabbitmq-plugins enable rabbitmq_management

# macOS
brew install rabbitmq
brew services start rabbitmq

# Windows
# Download from https://www.rabbitmq.com/install-windows.html
```

### 6. Initialize Application
```bash
# Install Python package for NLTK
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('words')"

# Download spaCy model
python -m spacy download en_core_web_sm

# Initialize database
flask db init
flask db migrate -m "Initial migration"
flask db upgrade

# Start Flask development server
python app.py
```

### 7. Start Background Workers
```bash
# In separate terminal - Celery worker
celery -A app.celery worker --loglevel=info --concurrency=4

# In separate terminal - Celery beat scheduler  
celery -A app.celery beat --loglevel=info
```

## 📚 API Documentation

### Authentication Endpoints
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login  
- `POST /api/v1/auth/refresh` - Refresh JWT token
- `GET /api/v1/auth/me` - Get current user info
- `POST /api/v1/auth/logout` - User logout

### Image Management
- `POST /api/v1/images/upload` - Upload images (max 10 files)
- `POST /api/v1/images/batch-upload` - Batch upload (max 50 files)
- `GET /api/v1/images/` - List user images (paginated)
- `GET /api/v1/images/{id}` - Get image details
- `GET /api/v1/images/{id}/file` - Serve original image
- `GET /api/v1/images/{id}/thumbnail` - Serve thumbnail
- `POST /api/v1/images/search` - Semantic search
- `DELETE /api/v1/images/{id}` - Delete image

### Face Detection
- `POST /api/v1/faces/process` - Trigger face processing
- `GET /api/v1/faces/` - List detected faces (paginated)
- `GET /api/v1/faces/{id}` - Get face details
- `GET /api/v1/faces/{id}/image` - Serve face image
- `GET /api/v1/faces/clusters` - List face clusters
- `POST /api/v1/faces/assign-person` - Assign person to faces
- `POST /api/v1/faces/cluster` - Trigger face clustering

### Admin Endpoints
- `GET /api/v1/admin/audit-logs` - System audit logs
- `GET /api/v1/admin/users` - User management
- `GET /api/v1/admin/system/stats` - System statistics
- `GET /api/v1/admin/system/health` - Health check

### Rate Limits
- **Authentication**: 10 requests/minute
- **Image Upload**: 20 requests/hour
- **Search**: 100 requests/hour
- **General API**: 1000 requests/hour

Full interactive documentation available at `/api/v1/docs`

## 🔧 Configuration

### Environment Variables
| Variable | Description | Default |
|----------|-------------|---------|
| `FLASK_ENV` | Environment mode | `production` |
| `DATABASE_URL` | MySQL connection string | Required |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379/0` |
| `JWT_SECRET_KEY` | JWT signing key | Required |
| `VECTOR_DB_TYPE` | Vector database type | `chromadb` |
| `MAIL_SERVER` | SMTP server | `smtp.gmail.com` |
| `MAX_CONTENT_LENGTH` | Max upload size | `16777216` (16MB) |
| `RATE_LIMIT_DEFAULT` | Default rate limit | `1000 per hour` |

### Security Configuration
- **CORS**: Configurable origins
- **Rate Limiting**: Redis-backed with user-specific limits
- **Input Validation**: Comprehensive request validation
- **SQL Injection Protection**: Parameterized queries
- **File Upload Security**: Type validation, virus scanning
- **Audit Logging**: All API requests and security events

## 🚀 Production Deployment

### 1. SSL/TLS Setup
```bash
# Generate certificates (Let's Encrypt recommended)
certbot --nginx -d yourdomain.com

# Update nginx.conf with your domain
# Copy certificates to config/ssl/
```

### 2. Production Environment
```bash
# Update .env for production
FLASK_ENV=production
FLASK_DEBUG=False

# Use strong secrets
JWT_SECRET_KEY=$(openssl rand -hex 32)
MYSQL_ROOT_PASSWORD=$(openssl rand -hex 16)
```

### 3. Monitoring Setup
```bash
# Enable monitoring
ENABLE_METRICS=True

# Access metrics
curl http://localhost:5000/metrics
```

### 4. Backup Strategy
```bash
# Database backups
docker-compose exec mysql mysqldump -u root -p image_search_db > backup.sql

# Vector database backup
docker-compose exec app python scripts/backup_vectors.py
```

## 🧪 Testing

### Run Tests
```bash
# Install test dependencies
pip install pytest pytest-flask pytest-cov

# Run tests
pytest

# With coverage
pytest --cov=. --cov-report=html
```

### API Testing
```bash
# Test health endpoint
curl http://localhost:5000/health

# Test authentication
curl -X POST http://localhost:5000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"TestPass123!","name":"Test User"}'
```

## 🔍 Monitoring & Logging

### Log Locations
- **Application Logs**: `logs/app.log`
- **Audit Logs**: `logs/audit.log`
- **Access Logs**: Available via `/api/v1/admin/audit-logs`

### Health Checks
- **Application**: `GET /health`
- **Database**: Automatic connection testing
- **Services**: `GET /api/v1/admin/system/health`

### Performance Monitoring
- **Metrics**: Prometheus format at `/metrics`
- **Queue Status**: Celery flower at `http://localhost:5555`
- **Database**: Built-in query monitoring

## 🐛 Troubleshooting

### Common Issues

#### GPU Not Detected
```bash
# Check GPU support
docker run --rm --gpus all nvidia/cuda:11.8-base nvidia-smi

# Use CPU fallback
export CUDA_VISIBLE_DEVICES=""
```

#### Out of Memory
```bash
# Reduce batch size
export BATCH_SIZE=8

# Increase Docker memory limit
# Edit docker-compose.yml memory limits
```

#### Permission Issues
```bash
# Fix file permissions
sudo chown -R 1000:1000 static/ logs/ chroma_db/
chmod -R 755 static/ logs/ chroma_db/
```

#### Database Connection Issues
```bash
# Check MySQL status
docker-compose exec mysql mysql -u root -p -e "SELECT 1;"

# Reset database
docker-compose down -v
docker-compose up mysql -d
# Wait for initialization, then start other services
```

### Debug Mode
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
export FLASK_DEBUG=True

# Restart services
docker-compose restart app
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- **Documentation**: [docs.imagesearch.com](https://docs.imagesearch.com)
- **Issues**: [GitHub Issues](https://github.com/yourusername/image-search/issues)
- **Email**: support@imagesearch.com
- **Discord**: [Community Server](https://discord.gg/imagesearch)

---

**Built with ❤️ using Flask, Docker, and AI**