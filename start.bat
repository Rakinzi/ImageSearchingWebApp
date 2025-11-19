@echo off
REM Image Search Web Application - Quick Start Script (Windows)
REM This script starts all services and initializes the database

echo ==========================================
echo Image Search App - Quick Start
echo ==========================================
echo.

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo Error: Docker is not running
    echo Please start Docker Desktop and try again
    pause
    exit /b 1
)

REM Check if .env exists
if not exist .env (
    echo Creating .env file from .env.example...
    copy .env.example .env
    echo .env file created
    echo.
    echo IMPORTANT: For production, edit .env and change:
    echo    - POSTGRES_PASSWORD
    echo    - RABBITMQ_PASSWORD
    echo    - JWT_SECRET_KEY
    echo.
    pause
)

REM Stop any existing containers
echo.
echo Stopping existing containers...
docker-compose down 2>nul

REM Build and start services
echo.
echo Building and starting services...
docker-compose up -d --build

REM Wait for services to be healthy
echo.
echo Waiting for services to be healthy...
timeout /t 10 /nobreak >nul

REM Initialize database
echo.
echo Initializing database (if needed)...
docker-compose exec --user root app flask db init
docker-compose exec --user root app flask db migrate -m "Initial migration"
docker-compose exec --user root app flask db upgrade

REM Check service status
echo.
echo Service Status:
docker-compose ps

echo.
echo ==========================================
echo Application is running!
echo ==========================================
echo.
echo Access points:
echo   Frontend:          http://localhost
echo   Backend API:       http://localhost/api/
echo   Health Check:      http://localhost/health
echo   RabbitMQ Mgmt:     http://localhost:15672
echo      (Username: admin, Password: secure_rabbit_password)
echo.
echo Useful commands:
echo   View logs:         docker-compose logs -f
echo   Stop services:     docker-compose down
echo   Restart:           docker-compose restart
echo.
echo For more info, see DEPLOYMENT.md
echo ==========================================
echo.
pause
