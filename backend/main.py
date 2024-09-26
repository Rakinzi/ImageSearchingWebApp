from flask import Flask
from flask_cors import CORS
from routes.imagesRoute import images_blueprint
from routes.facesRoute import faces_blueprint
from configs.celery_config import make_celery
from services.model import make_clip_model
import os

app = Flask(__name__)
CORS(app)

app.config.update(
    broker_url='amqp://guest:guest@localhost:5672//',
    result_backend='rpc://',
    imports=('tasks.imageProcessingAsync',)

)

celery = make_celery(app)

app.register_blueprint(images_blueprint)
app.register_blueprint(faces_blueprint, url_prefix='/faces')


def create_upload_folder():
    upload_folder = "static/uploads/images"
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)


if __name__ == '__main__':
    make_clip_model()
    create_upload_folder()
    app.run(debug=True, host="0.0.0.0")
