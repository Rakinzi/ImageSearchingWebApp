#!/bin/bash
set -e

echo "Starting Image Search Application (CPU-only)..."

# Set Flask app for CLI commands
export FLASK_APP=app.py

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
flask db init || echo "DB already initialized"
flask db migrate -m "Initial migration" || echo "Migration already exists"
flask db upgrade || echo "Migration completed"

# Create upload directories
echo "Creating upload directories..."
mkdir -p static/uploads/{images,thumbnails,faces}
mkdir -p logs
mkdir -p chroma_db

# Download NLTK data if not exists
echo "Setting up NLTK data..."
python3.11 -c "
import nltk
import ssl
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

try:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
    nltk.download('words', quiet=True)
    print('NLTK data downloaded successfully')
except Exception as e:
    print(f'NLTK download warning: {e}')
"

# Try to download spaCy model
echo "Setting up spaCy model..."
python3.11 -c "
try:
    import spacy
    spacy.cli.download('en_core_web_sm')
    print('spaCy model downloaded successfully')
except Exception as e:
    print(f'spaCy download warning: {e}')
"

echo "Starting application..."

# Start the Flask application
if [ "$FLASK_ENV" = "development" ]; then
    exec flask run --host=0.0.0.0 --port=8080
else
    exec gunicorn --bind 0.0.0.0:8080 --workers 2 --worker-class eventlet --worker-connections 1000 --timeout 300 app:app
fi