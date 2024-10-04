# configs/auth_config.py

import os
from datetime import timedelta


class AuthConfig:
    # JWT Settings
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///auth.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'mykey')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

    # Email Settings
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.getenv('MAIL_USERNAME', 'leightonsilver@gmail.com')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', 'qxfjyciwtityhvrz')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'leightonsilver@gmail.com')

    # Frontend URL for email verification
    FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:5173')

    # Token Settings
    VERIFICATION_TOKEN_EXPIRES = timedelta(hours=24)
    PASSWORD_RESET_TOKEN_EXPIRES = timedelta(hours=1)