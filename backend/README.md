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
   pip install chromadb==0.5.5 face-recognition==1.3.0 Flask==3.0.3 Flask-Cors==4.0.0 firebase-admin==6.5.0 celery==5.4.0 facenet-pytorch==2.6.0 sentence-transformers==2.3.1 pyenchant==3.2.2 nvidia-cublas-cu12==12.6.1.4 nvidia-cuda-cupti-cu12==12.6.68 nvidia-cuda-nvrtc-cu12==12.6.68 nvidia-cuda-runtime-cu12==12.6.68 nvidia-cudnn-cu12==9.4.0.58 nvidia-cufft-cu12==11.2.6.59 nvidia-curand-cu12==10.3.7.68 nvidia-cusolver-cu12==11.6.4.69 nvidia-cusparse-cu12==12.5.3.3 nvidia-nvjitlink-cu12==12.6.68 nvidia-nvtx-cu12==12.6.68 nltk==3.9.1 tensorflow==2.16.1 torch==2.2.2 celery==5.4.0 keras==3.5.0 Flask-Mail==0.10.0 Flask-SQLAlchemy==3.1.1 email_validator==2.2.0 itsdangerous==2.2.0 Werkzeug==3.0.4
   ```

6. **If installation problems persists you can install it the manual way if you don't have a GPU**

```bash
   pip install chromadb==0.5.5 face-recognition==1.3.0 Flask==3.0.3 Flask-Cors==4.0.0 firebase-admin==6.5.0 celery==5.4.0 facenet-pytorch==2.6.0 sentence-transformers==2.3.1 pyenchant==3.2.2 celery==5.4.0 nltk==3.9.1 tensorflow==2.16.1 torch==2.2.2 keras==3.5.0 Flask-Mail==0.10.0 Flask-SQLAlchemy==3.1.1 email_validator==2.2.0 itsdangerous==2.2.0 Werkzeug==3.0.4
   ```

7. **After installation download the RabbitMQ server**

For more instructions on how to download the server visit

### Windows
[RabbitMQ](https://www.rabbitmq.com/docs/install-windows/)

### Linux Ubuntu
[RabbitMQ](https://www.rabbitmq.com/docs/install-debian)

8. **Start the RabbitMQ server on your machine**

9. **To start the server**
```bash
   python main.py
   ```

10 **To start the Celery tasks handler**
```bash
   celery -A main.celery worker --loglevel=info --pool=solo
   ```

## You are good to go for the backend