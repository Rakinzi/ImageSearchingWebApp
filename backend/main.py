from flask import Flask
from flask_cors import CORS
from routes.imagesRoute import images_blueprint
from routes.facesRoute import faces_blueprint
from configs.celery_config import make_celery
from services.model import make_clip_model
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'thisisasecretkey'
db = SQLAlchemy(app)

CORS(app)

app.config.update(
    broker_url='amqp://guest:guest@localhost:5672//',
    result_backend='rpc://',
    imports=('tasks.imageProcessingAsync',)

)

celery = make_celery(app)

app.register_blueprint(images_blueprint, url_prefix='/images')
app.register_blueprint(faces_blueprint, url_prefix='/faces')


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    firstname = db.Column(db.String(50), nullable=False)
    lastname = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(50), nullable=False)


if os.path.exists('./database.db'):
    pass
else:
    with app.app_context():  # Ensures we are inside the app's context
        db.create_all()


def create_upload_folder():
    upload_folder = "static/uploads/images"
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)


if __name__ == '__main__':
    make_clip_model()
    create_upload_folder()
    app.run(debug=True, host="0.0.0.0")
