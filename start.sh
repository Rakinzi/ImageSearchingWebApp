#!/bin/bash

# Image Search Web Application - Quick Start Script
# This script starts all services and initializes the database

set -e  # Exit on error

echo "=========================================="
echo "Image Search App - Quick Start"
echo "=========================================="
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running"
    echo "Please start Docker Desktop and try again"
    exit 1
fi

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from .env.example..."
    cp .env.example .env
    echo "✅ .env file created"
    echo ""
    echo "⚠️  IMPORTANT: For production, edit .env and change:"
    echo "   - POSTGRES_PASSWORD"
    echo "   - RABBITMQ_PASSWORD"
    echo "   - JWT_SECRET_KEY"
    echo ""
    read -p "Press Enter to continue..."
fi

# Stop any existing containers
echo ""
echo "🛑 Stopping existing containers..."
docker-compose down 2>/dev/null || true

# Build and start services
echo ""
echo "🏗️  Building and starting services..."
docker-compose up -d --build

# Wait for services to be healthy
echo ""
echo "⏳ Waiting for services to be healthy..."
sleep 10

# Check if database needs initialization
if docker-compose exec -T app flask db current 2>/dev/null | grep -q "None"; then
    echo ""
    echo "🗄️  Initializing database (first time setup)..."
    docker-compose exec --user root app flask db init
    docker-compose exec --user root app flask db migrate -m "Initial migration"
    docker-compose exec --user root app flask db upgrade
    echo "✅ Database initialized"
else
    echo ""
    echo "✅ Database already initialized"
fi

# Check service status
echo ""
echo "📊 Service Status:"
docker-compose ps

echo ""
echo "=========================================="
echo "✅ Application is running!"
echo "=========================================="
echo ""
echo "Access points:"
echo "  🌐 Frontend:          http://localhost"
echo "  🔌 Backend API:       http://localhost/api/"
echo "  ❤️  Health Check:      http://localhost/health"
echo "  🐰 RabbitMQ Mgmt:     http://localhost:15672"
echo "     (Username: admin, Password: secure_rabbit_password)"
echo ""
echo "Useful commands:"
echo "  📜 View logs:         docker-compose logs -f"
echo "  🛑 Stop services:     docker-compose down"
echo "  🔄 Restart:           docker-compose restart"
echo ""
echo "For more info, see DEPLOYMENT.md"
echo "=========================================="
