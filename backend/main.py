from flask import Flask
from flask_cors import CORS
from routes.imagesRoute import images_blueprint
import os

app = Flask(__name__)
CORS(app)

app.register_blueprint(images_blueprint)


def create_upload_folder():
    upload_folder = "static/uploads/images"
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)


if __name__ == '__main__':
    create_upload_folder()
    app.run(debug=True, host="0.0.0.0")
