#!/bin/bash

# Image Search Backend Setup Script
# This script sets up the Image Search backend for development or production

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        print_error "This script should not be run as root for security reasons"
        exit 1
    fi
}

# Check system requirements
check_requirements() {
    print_status "Checking system requirements..."
    
    # Check Python version
    if command -v python3.9 &> /dev/null; then
        print_success "Python 3.9+ found"
    elif command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
        if (( $(echo "$PYTHON_VERSION >= 3.9" | bc -l) )); then
            print_success "Python $PYTHON_VERSION found"
        else
            print_error "Python 3.9+ required, found $PYTHON_VERSION"
            exit 1
        fi
    else
        print_error "Python 3.9+ not found"
        exit 1
    fi
    
    # Check Docker
    if command -v docker &> /dev/null; then
        print_success "Docker found"
    else
        print_warning "Docker not found - required for production deployment"
    fi
    
    # Check Docker Compose
    if command -v docker-compose &> /dev/null; then
        print_success "Docker Compose found"
    else
        print_warning "Docker Compose not found - required for production deployment"
    fi
    
    # Check GPU support
    if command -v nvidia-smi &> /dev/null; then
        print_success "NVIDIA GPU support detected"
    else
        print_warning "No GPU detected - will use CPU processing"
    fi
}

# Setup environment
setup_environment() {
    print_status "Setting up environment..."
    
    # Create .env file if it doesn't exist
    if [ ! -f .env ]; then
        if [ -f .env.example ]; then
            cp .env.example .env
            print_success "Created .env file from example"
        else
            print_error ".env.example file not found"
            exit 1
        fi
    else
        print_warning ".env file already exists, skipping creation"
    fi
    
    # Generate secure secrets
    print_status "Generating secure secrets..."
    
    # Generate JWT secret if not set
    if ! grep -q "^JWT_SECRET_KEY=" .env || grep -q "^JWT_SECRET_KEY=your-super-secret-jwt-key" .env; then
        JWT_SECRET=$(openssl rand -hex 32)
        sed -i "s/^JWT_SECRET_KEY=.*/JWT_SECRET_KEY=$JWT_SECRET/" .env
        print_success "Generated JWT secret key"
    fi
    
    # Generate MySQL passwords if not set
    if ! grep -q "^MYSQL_ROOT_PASSWORD=" .env || grep -q "^MYSQL_ROOT_PASSWORD=secure_root_password" .env; then
        MYSQL_ROOT_PASS=$(openssl rand -hex 16)
        sed -i "s/^MYSQL_ROOT_PASSWORD=.*/MYSQL_ROOT_PASSWORD=$MYSQL_ROOT_PASS/" .env
        print_success "Generated MySQL root password"
    fi
    
    if ! grep -q "^MYSQL_PASSWORD=" .env || grep -q "^MYSQL_PASSWORD=secure_app_password" .env; then
        MYSQL_APP_PASS=$(openssl rand -hex 16)
        sed -i "s/^MYSQL_PASSWORD=.*/MYSQL_PASSWORD=$MYSQL_APP_PASS/" .env
        print_success "Generated MySQL app password"
    fi
}

# Setup Python virtual environment
setup_python_env() {
    print_status "Setting up Python virtual environment..."
    
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        print_success "Created Python virtual environment"
    else
        print_warning "Virtual environment already exists"
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip setuptools wheel
    
    # Install requirements
    if [ -f "requirements.txt" ]; then
        print_status "Installing Python dependencies..."
        pip install -r requirements.txt
        print_success "Python dependencies installed"
    else
        print_error "requirements.txt not found"
        exit 1
    fi
    
    # Download spaCy model
    print_status "Downloading spaCy language model..."
    python -m spacy download en_core_web_sm
    print_success "spaCy model downloaded"
    
    # Download NLTK data
    print_status "Downloading NLTK data..."
    python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('words'); nltk.download('punkt_tab')"
    print_success "NLTK data downloaded"
}

# Setup Docker environment
setup_docker() {
    print_status "Setting up Docker environment..."
    
    # Check if Docker is running
    if ! docker info &> /dev/null; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
    
    # Build Docker images
    print_status "Building Docker images..."
    docker-compose build
    print_success "Docker images built"
    
    # Start services
    print_status "Starting Docker services..."
    docker-compose up -d mysql redis rabbitmq
    
    # Wait for services to be ready
    print_status "Waiting for services to be ready..."
    sleep 30
    
    # Check service health
    if docker-compose exec mysql mysqladmin ping -h localhost --silent; then
        print_success "MySQL is ready"
    else
        print_error "MySQL failed to start"
        exit 1
    fi
    
    if docker-compose exec redis redis-cli ping | grep -q PONG; then
        print_success "Redis is ready"
    else
        print_error "Redis failed to start"
        exit 1
    fi
}

# Initialize database
init_database() {
    print_status "Initializing database..."
    
    if [ "$1" = "docker" ]; then
        # Docker setup
        docker-compose exec app flask db upgrade
        print_success "Database initialized with Docker"
    else
        # Local setup
        source venv/bin/activate
        export FLASK_APP=app.py
        flask db init || true  # Ignore error if already initialized
        flask db migrate -m "Initial migration" || true
        flask db upgrade
        print_success "Database initialized locally"
    fi
}

# Create directories
create_directories() {
    print_status "Creating necessary directories..."
    
    mkdir -p static/uploads/{images,thumbnails,faces}
    mkdir -p logs
    mkdir -p chroma_db
    mkdir -p backups
    
    # Set proper permissions
    chmod -R 755 static logs chroma_db backups
    
    print_success "Directories created"
}

# Display final instructions
show_instructions() {
    print_success "Setup completed successfully!"
    echo
    echo -e "${BLUE}==================== NEXT STEPS ====================${NC}"
    echo
    
    if [ "$1" = "docker" ]; then
        echo -e "${GREEN}Docker Setup Complete:${NC}"
        echo "1. Start all services:"
        echo "   docker-compose up"
        echo
        echo "2. Access the application:"
        echo "   • API: http://localhost:5000"
        echo "   • API Docs: http://localhost:5000/api/v1/docs"
        echo "   • Health Check: http://localhost:5000/health"
        echo
        echo "3. Management interfaces:"
        echo "   • RabbitMQ: http://localhost:15672 (admin / check .env for password)"
        echo
    else
        echo -e "${GREEN}Local Development Setup Complete:${NC}"
        echo "1. Activate virtual environment:"
        echo "   source venv/bin/activate"
        echo
        echo "2. Start the Flask application:"
        echo "   python app.py"
        echo
        echo "3. In separate terminals, start background workers:"
        echo "   celery -A app.celery worker --loglevel=info"
        echo "   celery -A app.celery beat --loglevel=info"
        echo
        echo "4. Access the application:"
        echo "   • API: http://localhost:5000"
        echo "   • API Docs: http://localhost:5000/api/v1/docs"
        echo
    fi
    
    echo -e "${YELLOW}Important Security Notes:${NC}"
    echo "• Update .env file with your actual email credentials"
    echo "• Change default passwords in production"
    echo "• Configure firewall rules for production deployment"
    echo "• Set up SSL/TLS certificates for HTTPS"
    echo
    echo -e "${BLUE}For production deployment, see README.md${NC}"
    echo "=================================================="
}

# Main setup function
main() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║            Image Search Backend Setup Script             ║"
    echo "║                                                          ║"
    echo "║  This script will help you set up the Image Search      ║"
    echo "║  backend for development or production use.              ║"
    echo "╚══════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo
    
    # Parse command line arguments
    SETUP_TYPE="local"
    SKIP_DEPS=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --docker)
                SETUP_TYPE="docker"
                shift
                ;;
            --skip-deps)
                SKIP_DEPS=true
                shift
                ;;
            --help)
                echo "Usage: $0 [OPTIONS]"
                echo
                echo "Options:"
                echo "  --docker      Set up using Docker (recommended for production)"
                echo "  --skip-deps   Skip dependency installation"
                echo "  --help        Show this help message"
                echo
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                echo "Use --help for usage information"
                exit 1
                ;;
        esac
    done
    
    print_status "Starting setup with mode: $SETUP_TYPE"
    echo
    
    # Run setup steps
    check_root
    check_requirements
    create_directories
    setup_environment
    
    if [ "$SETUP_TYPE" = "docker" ]; then
        if [ "$SKIP_DEPS" = false ]; then
            setup_docker
        fi
        init_database docker
    else
        if [ "$SKIP_DEPS" = false ]; then
            setup_python_env
        fi
        init_database local
    fi
    
    show_instructions "$SETUP_TYPE"
}

# Run main function with all arguments
main "$@"