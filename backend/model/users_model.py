from flask_sqlalchemy import SQLAlchemy

# Instantiate SQLAlchemy without db import
db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    is_verified = db.Column(db.Boolean, default=False)

    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.password = password
