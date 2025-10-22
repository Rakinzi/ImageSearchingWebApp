#!/bin/bash
set -e

echo "Starting Image Search Application (CPU-only)..."

# Wait for database to be ready
echo "Waiting for database..."
while ! nc -z postgresql 5432; do
    sleep 1
done
echo "Database is ready!"

# Wait for Redis to be ready
echo "Waiting for Redis..."
while ! nc -z redis 6379; do
    sleep 1
done
echo "Redis is ready!"

# Wait for RabbitMQ to be ready
echo "Waiting for RabbitMQ..."
while ! nc -z rabbitmq 5672; do
    sleep 1
done
echo "RabbitMQ is ready!"

# Run database migrations
echo "Running database migrations..."
flask db upgrade

# Create upload directories
echo "Creating upload directories..."
mkdir -p static/uploads/{images,thumbnails,faces}
mkdir -p logs
mkdir -p chroma_db

# Set proper permissions
chown -R app:app static logs chroma_db

# Download required NLTK data if not exists
echo "Setting up NLTK data..."
python -c "
import nltk
import ssl
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)
nltk.download('words', quiet=True)
nltk.download('punkt_tab', quiet=True)
"

# Initialize CLIP model
echo "Initializing CLIP model..."
python -c "
from services.vector_service import VectorService
try:
    vector_service = VectorService()
    print('CLIP model loaded successfully')
except Exception as e:
    print(f'Warning: Could not load CLIP model: {e}')
"

echo "Starting application..."

# Start the Flask application
if [ "$FLASK_ENV" = "development" ]; then
    exec flask run --host=0.0.0.0 --port=8080
else
    exec gunicorn --bind 0.0.0.0:8080 --workers 4 --worker-class eventlet --worker-connections 1000 --timeout 300 app:app
fi