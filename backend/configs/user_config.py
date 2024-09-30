import os

# Generate a random secret key
SECRET_KEY = os.urandom(24)

# SQLAlchemy database configuration
SQLALCHEMY_DATABASE_URI = 'sqlite:///../users.db'  # Adjust path relative to the config file
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Flask-Mail configuration
MAIL_SERVER = 'smtp.gmail.com'
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USERNAME = os.getenv('MAIL_USERNAME', 'your_email@gmail.com')  # Use environment variables for sensitive data
MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', 'your_email_password')  # Use environment variables for sensitive data
MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'your_email@gmail.com')
