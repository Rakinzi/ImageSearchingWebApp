@echo off
echo Testing Image Search API...

REM Test health endpoint
echo.
echo 1. Testing Health Check...
curl -s http://localhost:5000/health
if %errorlevel%==0 (
    echo Health check passed!
) else (
    echo Health check failed - make sure the app is running
)

echo.
echo 2. Testing API Documentation...
curl -s -I http://localhost:5000/api/v1/docs | find "200"
if %errorlevel%==0 (
    echo API docs are accessible!
) else (
    echo API docs check failed
)

echo.
echo 3. Check Docker containers...
docker ps --filter "name=image_search"

echo.
echo Test complete!
echo.
echo If everything is working:
echo - Health API: http://localhost:5000/health
echo - API Docs: http://localhost:5000/api/v1/docs  
echo - RabbitMQ UI: http://localhost:15672 (admin/secure_rabbit_password)

pause