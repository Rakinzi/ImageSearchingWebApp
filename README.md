# Image Searcher

**Image Searcher** is a powerful and user-friendly web application designed for efficient image searching and management. This system allows users to search for images based on various criteria, including image content and metadata. 

## Overview

Image Searcher is designed to help users find and manage images easily. The system consists of two main components:

- **Backend**: The backend handles image processing, search functionality, and data management.
- **Frontend**: The frontend provides an intuitive interface for users to interact with the application.

## Features

- **Image Search**: Search images based on keywords or visual content.
- **Image Management**: Organize and manage your image collection effectively.
- **User-friendly Interface**: Easy-to-navigate interface for seamless image searching.

## Project Structure


- **`backend/`**: Contains all the server-side code and configuration, including API endpoints, database interactions, and image processing logic.
- **`frontend/`**: Includes all the client-side code and assets, such as HTML, CSS, JavaScript, and user interface components.

# Frontend Vite App

This is a Vite-powered frontend project located in the `frontend` directory. The project is configured to use Yarn as the package manager and includes Vue Router for handling navigation.

## Prerequisites

Before starting, ensure that you have the following installed:

- **Node.js**: Version `16.x.x` or above is required.
- **Yarn**: The recommended package manager for this project.

> You can also use `npm` if you prefer, but Yarn is recommended.

### Check Node.js version

To ensure you have the correct version of Node.js installed, run:

```bash
node -v
```

```bash

frontend/
├── public/                     # Static files
├── src/
│   ├── assets/                 # Assets like images, fonts, etc.
│   ├── components/             # Reusable Vue components
│   │   └── Navbar.vue          # Example component
│   ├── views/                  # Pages or views
│   │   └── Home.vue            # Example home page view
│   ├── router/                 # Vue Router configurations
│   │   └── index.js            # Router setup and routes
│   ├── App.vue                 # Root Vue component
│   ├── main.js                 # Main entry file
│   └── store/                  # Vuex store (if applicable)
│       └── index.js            # Vuex state management setup
├── .gitignore                  # Ignored files for Git
├── index.html                  # Main HTML template
├── package.json                # Project dependencies and scripts
├── vite.config.js              # Vite configuration
└── yarn.lock                   # Lockfile for Yarn dependencies

```


## Installation for the Backend

To get started, follow these steps:

If you are using Windows, you need to download CMake to ensure proper functionality. You can find it here:
- [Cmake](https://cmake.org/download/)


1. **Clone the repository:**

   ```bash
   git clone https://github.com/Rakinzi/ImageSearchingWebApp.git
   ```

2. **Navigate to the backend:**

   ```bash
   cd backend
   ```

Before creating a virtual env make sure you are using python version 3.11

You can download it on - [Python](https://www.python.org/downloads/release/python-3116/)

3. **Create a virtual environment with the following command**

  ```bash
   python -m venv venv
   ```

4. **Activate the virtual environment on Windows**

  ```bash
   venv\Scripts\activate
   ```

4. **Activate the virtual environment on Linux/MacOS**

 ```bash
   source venv/bin/activate
   ```

5. **Install python packages**

```bash
   pip install -r requirements.txt
   ```

6. **If installation problems persists you can install it the manual way if you have a GPU**

```bash
 pip install chromadb==0.5.5 face-recognition==1.3.0 Flask==3.0.3 Flask-Cors==5.0.0 firebase-admin==6.5.0 celery==5.4.0 facenet-pytorch==2.6.0 sentence-transformers==2.3.1 pyenchant==3.2.2 nvidia-cublas-cu12==12.6.1.4 nvidia-cuda-cupti-cu12==12.6.68 nvidia-cuda-nvrtc-cu12==12.6.68 nvidia-cuda-runtime-cu12==12.6.68 nvidia-cudnn-cu12==9.4.0.58 nvidia-cufft-cu12==11.2.6.59 nvidia-curand-cu12==10.3.7.68 nvidia-cusolver-cu12==11.6.4.69 nvidia-cusparse-cu12==12.5.3.3 nvidia-nvjitlink-cu12==12.6.68 nvidia-nvtx-cu12==12.6.68 nltk==3.9.1 tensorflow==2.16.1 torch==2.2.2 keras==3.5.0 Flask-Mail==0.10.0 Flask-SQLAlchemy==3.1.1 email_validator==2.2.0 itsdangerous==2.2.0 Werkzeug==3.0.4 Flask-Bcrypt==1.0.1 Flask-JWT-Extended==4.6.0 Flask-Login==0.6.3 Flask-Migrate==4.0.7 Flask-WTF==1.2.1 deepface==0.0.93 git+https://github.com/openai/CLIP.git opencv-python==4.10.0.84 opencv-python-headless==4.10.0.84 numpy==1.26.4 pillow==10.2.0 joblib==1.4.2 geopy==2.4.1 ExifRead==3.0.0 spacy==3.7.4 python-dateutil==2.8.2 contractions==0.1.73 APScheduler==3.10.4  tf-keras
   ```

6. **If installation problems persists you can install it the manual way if you don't have a GPU**

```bash
 pip install chromadb==0.5.5 face-recognition==1.3.0 Flask==3.0.3 Flask-Cors==5.0.0 firebase-admin==6.5.0 celery==5.4.0 facenet-pytorch==2.6.0 sentence-transformers==2.3.1 pyenchant==3.2.2 nltk==3.9.1 tensorflow==2.16.1 torch==2.2.2 keras==3.5.0 Flask-Mail==0.10.0 Flask-SQLAlchemy==3.1.1 email_validator==2.2.0 itsdangerous==2.2.0 Werkzeug==3.0.4 Flask-Bcrypt==1.0.1 Flask-JWT-Extended==4.6.0 Flask-Login==0.6.3 Flask-Migrate==4.0.7 Flask-WTF==1.2.1 deepface==0.0.93 git+https://github.com/openai/CLIP.git opencv-python==4.10.0.84 opencv-python-headless==4.10.0.84 numpy==1.26.4 pillow==10.2.0 joblib==1.4.2 geopy==2.4.1 ExifRead==3.0.0 spacy==3.7.4 python-dateutil==2.8.2 contractions==0.1.73 APScheduler==3.10.4
   ```

7. **Download the spacy language pack for natural language processing**

```bash
python -m spacy download en_core_web_lg
   ```

8. **After installation download the RabbitMQ server**

For more instructions on how to download the server visit

### Windows
[RabbitMQ](https://www.rabbitmq.com/docs/install-windows/)

### Linux Ubuntu
[RabbitMQ](https://www.rabbitmq.com/docs/install-debian)

9. **Start the RabbitMQ server on your machine**

10. **Before starting the main server we need to initialize our database first with the 3 commands below**
```bash
  flask db init
  flask db migrate -m "Initial migration"
  flask db upgrade
   ```

11. **To start the server**
```bash
   python main.py
   ```

12. **To start the Celery tasks handler**
```bash
   celery -A main.celery worker --loglevel=info --pool=solo
   ```

## You are good to go for the backend