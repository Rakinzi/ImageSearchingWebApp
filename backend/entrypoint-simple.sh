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

# Download CLIP model if not exists (cached in /home/app/.cache which is a mounted volume)
echo "Checking CLIP model cache..."
python3.11 -c "
import os
import sys

# Check if model is already cached
cache_dir = os.path.expanduser('~/.cache/huggingface/hub')
model_cached = False

if os.path.exists(cache_dir):
    # Check for ViT-L-14 model files
    for root, dirs, files in os.walk(cache_dir):
        if any('vit' in d.lower() and 'l' in d.lower() for d in dirs):
            model_cached = True
            print('✅ CLIP model already cached, skipping download')
            break

if not model_cached:
    print('📦 Downloading CLIP model (ViT-L-14, ~1.7GB)...')
    print('This is a one-time download, model will be cached for future use.')
    try:
        import torch
        import open_clip

        # Download model to cache
        model, _, preprocess = open_clip.create_model_and_transforms(
            'ViT-L-14',
            pretrained='laion2b_s32b_b82k',
            device='cpu'
        )
        print('✅ CLIP model downloaded and cached successfully!')

        # Clean up to save memory
        del model
        del preprocess

    except Exception as e:
        print(f'⚠️  CLIP model download warning: {e}')
        print('Image embeddings will be generated on first use (may take longer)')
        sys.exit(0)  # Don't fail startup if model download fails
" || echo "Continuing without pre-cached model..."

echo "Starting application..."

# Start the Flask application
if [ "$FLASK_ENV" = "development" ]; then
    exec flask run --host=0.0.0.0 --port=8080
else
    exec gunicorn --bind 0.0.0.0:8080 --workers 2 --worker-class eventlet --worker-connections 1000 --timeout 300 app:app
fi