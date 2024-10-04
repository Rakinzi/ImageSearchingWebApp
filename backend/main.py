from flask import Flask
from flask_cors import CORS
from routes.imagesRoute import images_blueprint
from routes.facesRoute import faces_blueprint
from configs.celery_config import make_celery
from services.model import make_clip_model
import os
from tasks.faceProcessingAsync import faces_scheduler
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from models.user import db
from routes.auth import auth_bp
from configs.auth_config import AuthConfig
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config.from_object(AuthConfig)

CORS(app, resources={r"/*": {"origins": "*"}})

JWTManager(app)

db.init_app(app)

Migrate(app, db)

app.config.update(
    broker_url='amqp://guest:guest@localhost:5672//',
    result_backend='rpc://',
    imports=('tasks.imageProcessingAsync',)

)

celery = make_celery(app)

app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(images_blueprint, url_prefix='/images')
app.register_blueprint(faces_blueprint, url_prefix='/faces')


@app.route('/health')
def health_check():
    return {'status': 'healthy'}, 200


def create_upload_folder():
    upload_folder = "static/uploads/images"
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)


if __name__ == '__main__':
    faces_scheduler()
    make_clip_model()
    create_upload_folder()
    app.run(debug=True, host="0.0.0.0")
