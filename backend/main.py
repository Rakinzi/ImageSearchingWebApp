from flask import Flask
from flask_cors import CORS
from routes.imagesRoute import images_blueprint

app = Flask(__name__)
CORS(app)

app.register_blueprint(images_blueprint)


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")
