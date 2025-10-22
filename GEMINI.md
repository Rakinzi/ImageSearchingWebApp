# Project Overview

This is a full-stack web application for image searching and management. It allows users to upload images, have them automatically processed to extract information like faces, text, and location, and then search through them using natural language.

The project is composed of two main parts:

*   **Frontend:** A Vue.js single-page application (SPA) built with Vite. It uses Pinia for state management, Vue Router for navigation, and the Naive UI component library.
*   **Backend:** A Python Flask application that provides a RESTful API for the frontend. It uses a PostgreSQL database with SQLAlchemy for data storage, Celery with Redis for asynchronous task processing, and a variety of machine learning and computer vision libraries for image analysis. It also features a two-version API, with v2 being the more modern and feature-rich.

## Key Technologies

**Frontend:**

*   Vue.js 3
*   Vite
*   Pinia
*   Vue Router
*   Naive UI
*   Axios
*   Firebase (for authentication)

**Backend:**

*   Flask
*   PostgreSQL (with SQLAlchemy)
*   Celery
*   Redis
*   PyTorch
*   TensorFlow
*   OpenCV
*   face_recognition
*   CLIP
*   ChromaDB (for vector search)
*   Spacy & NLTK (for NLP)

# Building and Running

## Frontend

1.  **Navigate to the frontend directory:**
    ```bash
    cd frontend
    ```
2.  **Install dependencies:**
    ```bash
    yarn install
    ```
3.  **Run the development server:**
    ```bash
    yarn dev
    ```

## Backend

1.  **Navigate to the backend directory:**
    ```bash
    cd backend
    ```
2.  **Create and activate a Python virtual environment (Python 3.11 recommended):**
    ```bash
    python3.11 -m venv venv
    source venv/bin/activate
    ```
3.  **Install Python dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Download the Spacy language model:**
    ```bash
    python -m spacy download en_core_web_lg
    ```
5.  **Set up and run RabbitMQ (or another Celery broker).**
6.  **Initialize the database:**
    ```bash
    flask db init
    flask db migrate -m "Initial migration"
    flask db upgrade
    ```
7.  **Run the Flask development server:**
    ```bash
    python main.py
    ```
8.  **Run the Celery worker:**
    ```bash
    celery -A main.celery worker --loglevel=info --pool=solo
    ```

# Development Conventions

*   The backend follows a service-oriented architecture, with a clear separation of concerns between API endpoints, services, and models.
*   The backend API is versioned, with v1 and v2 available under `/api/v1` and `/api/v2` respectively. The v2 API is more modern and should be preferred for new development.
*   The v2 API uses `marshmallow` schemas for request and response validation, and `structlog` for structured logging.
*   Asynchronous tasks are handled by Celery. Image processing is done in the background to avoid blocking API requests.
*   The frontend uses a component-based architecture with Vue.js. State is managed with Pinia, and routing is handled by Vue Router.
*   The project uses a vector database (ChromaDB) to enable semantic search on images.
*   The backend uses `pytest` for testing.
